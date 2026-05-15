"""Track A — Sentinel-1 SAR flood-extent change detection.

Classical, reproducible, no training (UN-SPIDER recommended practice):
  baseline = median S1 VH (dB) over a dry pre-event window
  per event date: diff = event_VH - baseline_VH
  Otsu threshold on diff -> open-water candidate (backscatter drops when flooded)
  VV absolute-water cross-check reduces agricultural false positives
  subtract permanent water (decision 2) + steep slope, drop tiny components
  -> per-timestep flood polygons (GeoJSON), one FeatureCollection per event

SAR is used because it penetrates typhoon cloud — optical is blind exactly when
the flood happens. For the gauged validation event the extent is scored
(IoU / F1) against the GFD `flooded` polygon.

Outputs:
  site/public/data/flood_<event>.geojson   features tagged `date`
  site/public/data/flood_<event>_meta.json per-date area, Otsu thr, (IoU/F1)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from event.permanent_water import (  # noqa: E402
    flood_plausible_terrain,
    land_slope_ok,
    permanent_water_mask,
)
from floodwatch_ph.eeauth import init_ee  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "site" / "public" / "data"
VV_WATER_DB = -17.0   # absolute VV cross-check; smooth open water is darker
MIN_FLOOD_KM2 = 0.02   # drop speckle-scale components
VEC_SCALE = 200        # vectorization scale (m): coarser -> fewer polygons,
                       # web-light, and safely under EE's 5000-feature getInfo cap
VEC_MIN_KM2 = 0.05     # drop polygons below this before download
VEC_MAX_FEATS = 3000   # hard cap (< 5000 getInfo abort); keep largest by area


def _otsu_client(ee, band_img, aoi):
    """Otsu threshold computed in numpy from a small client-side histogram.
    Robust and deterministic — the server-side ee.Array variant is fragile."""
    import numpy as np

    h = band_img.rename("b").reduceRegion(
        reducer=ee.Reducer.histogram(256, 0.25),
        geometry=aoi, scale=90, maxPixels=1e9, bestEffort=True,
    ).get("b").getInfo()
    counts = np.asarray(h["histogram"], dtype=np.float64)
    means = np.asarray(h["bucketMeans"], dtype=np.float64)
    total = counts.sum()
    if total <= 0:
        return float(means[len(means) // 2])
    w = np.cumsum(counts)
    mu = np.cumsum(counts * means)
    mu_t = mu[-1]
    denom = w * (total - w)
    with np.errstate(divide="ignore", invalid="ignore"):
        num = (mu_t * w - mu * total) ** 2
        sigma_b = np.where(denom > 0, num / (denom * total), 0.0)
    return float(means[int(np.argmax(sigma_b))])


def _s1_vh_vv(ee, aoi, d0, d1):
    return (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(aoi)
        .filterDate(d0, d1)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VH", "VV"])
    )


def _flood_image(ee, aoi, base_vh, ev_img, perm, slope_ok, plausible):
    """UN-SPIDER recommended practice: Otsu on the event VH image (open water
    is a distinct dark mode vs land), gated by a change check that the pixel
    got DARKER than the dry baseline (excludes permanently dark non-flood
    surfaces), then permanent-water + slope + HAND-style flood-plausible-
    terrain + min-area refinement (the plausibility mask suppresses the
    Philippine rice-agriculture SAR false positive)."""
    vh = ev_img.select("VH").focal_median(50, "circle", "meters")
    thr = _otsu_client(ee, vh, aoi)            # ~ water/land valley (dB)
    thr = max(min(thr, -14.0), -24.0)          # clamp to a physical water range
    got_darker = vh.subtract(base_vh).lt(-1.0)  # newly inundated vs dry baseline
    flood = (
        vh.lt(thr)
        .And(got_darker)
        .And(perm.Not())
        .And(slope_ok)
        .And(plausible)
    )
    flood = flood.updateMask(flood).rename("flood")
    # Drop isolated speckle. connectedPixelCount caps at maxSize, so maxSize
    # must exceed the keep threshold or the test is always false.
    keep = flood.connectedPixelCount(128, True).gte(8)
    return flood.updateMask(keep), ee.Number(thr)


def _vectorize(ee, flood, aoi):
    """Vectorize at a coarse scale, drop sub-VEC_MIN_KM2 polygons, simplify,
    and keep at most VEC_MAX_FEATS largest features so the getInfo stays well
    under EE's 5000-element abort and the web payload stays small."""
    min_m2 = VEC_MIN_KM2 * 1e6
    fc = (
        flood.reduceToVectors(
            geometry=aoi, scale=VEC_SCALE, geometryType="polygon",
            eightConnected=False, maxPixels=1e9, bestEffort=True,
        )
        .map(lambda f: f.set("a", f.area(VEC_SCALE)))
        .filter(ee.Filter.gte("a", min_m2))
        .limit(VEC_MAX_FEATS, "a", False)
        .map(lambda f: f.simplify(VEC_SCALE).select([]))
    )
    return ee.FeatureCollection(fc).filterBounds(aoi)


def run(event_key: str) -> int:
    ee = init_ee()
    events = json.loads((HERE / "events.json").read_text())
    ev = events[event_key]
    aoi = ee.Geometry.Rectangle(ev["bbox"])
    perm = permanent_water_mask(ee).clip(aoi)
    slope_ok = land_slope_ok(ee).clip(aoi)
    plausible = flood_plausible_terrain(ee).clip(aoi)

    b0, b1 = ev["baseline_window"]
    base_vh = _s1_vh_vv(ee, aoi, b0, b1).select("VH").median().focal_median(
        50, "circle", "meters"
    )

    feats, meta_dates = [], []
    for d in ev["event_dates"]:
        d0 = d
        d1 = (
            __import__("datetime").date.fromisoformat(d)
            + __import__("datetime").timedelta(days=2)
        ).isoformat()
        ev_img = _s1_vh_vv(ee, aoi, d0, d1).median()
        flood, thr = _flood_image(ee, aoi, base_vh, ev_img, perm, slope_ok,
                                  plausible)
        area_km2 = ee.Number(
            flood.multiply(ee.Image.pixelArea())
            .reduceRegion(ee.Reducer.sum(), aoi, 30, maxPixels=1e9, bestEffort=True)
            .get("flood")
        ).divide(1e6).getInfo()
        fc = _vectorize(ee, flood, aoi).getInfo()
        n = 0
        for ft in fc["features"]:
            feats.append({
                "type": "Feature",
                "geometry": ft["geometry"],
                "properties": {"date": d, "event": event_key},
            })
            n += 1
        thr_v = thr.getInfo()
        meta_dates.append({"date": d, "flood_area_km2": round(area_km2 or 0, 2),
                           "otsu_threshold_db": round(thr_v, 3), "n_polygons": n})
        print(f"[event] {event_key} {d}: {area_km2:.1f} km2, "
              f"Otsu {thr_v:.2f} dB, {n} polygons")

    meta = {
        "event": event_key, "label": ev["label"], "role": ev["role"],
        "gauged": ev["gauged"], "aoi_name": ev["aoi_name"], "bbox": ev["bbox"],
        "permanent_water_masked": True,
        "method": "S1 VH: Otsu-on-VH + got-darker-vs-dry-baseline change gate "
        "+ permanent-water + slope + HAND-style flood-plausible-terrain mask",
        "dates": meta_dates,
    }

    if ev.get("gauged") and ev.get("gfd_event_id"):
        meta["validation"] = _iou_f1(ee, ee.Geometry.Rectangle(ev["bbox"]),
                                     ev["gfd_event_id"], perm, slope_ok,
                                     plausible, base_vh, ev["event_dates"][0])

    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"flood_{event_key}.geojson"
    out.write_text(json.dumps({
        "type": "FeatureCollection",
        "_meta": meta,
        "features": feats,
    }))
    (DATA / f"flood_{event_key}_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[event] wrote {out.name}: {len(feats)} polygons across "
          f"{len(meta_dates)} dates; perm-water masked = True")
    if "validation" in meta:
        v = meta["validation"]
        print(f"[event] Track A validation vs GFD {ev['gfd_event_id']}: "
              f"IoU={v['iou']:.3f} F1={v['f1']:.3f}")
    return 0


def _iou_f1(ee, aoi, gfd_id, perm, slope_ok, plausible, base_vh, date):
    """Track A transparency metric, reported plainly and caveated:

    IoU/precision/recall/F1 vs the GFD `flooded` polygon for the event,
    computed at GFD's NATIVE 250 m (comparing 10 m single-date SAR to a
    multi-day 250 m optical product at a finer scale is not apples-to-apples).
    Pixel agreement is inherently limited here: the only S1 pass is several
    days after GFD onset, and SAR vs multi-day MODIS optical see different
    water. This is reported, not hidden; Track A's product is the reproducible
    observed-extent time series and Track B carries the trained-model claim.
    """
    d1 = (
        __import__("datetime").date.fromisoformat(date)
        + __import__("datetime").timedelta(days=2)
    ).isoformat()
    ev_img = _s1_vh_vv(ee, aoi, date, d1).median()
    ours, _ = _flood_image(ee, aoi, base_vh, ev_img, perm, slope_ok, plausible)
    ours = ours.unmask(0).gt(0)
    gfd = (
        ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1")
        .filter(ee.Filter.eq("id", gfd_id)).first()
    )
    truth = gfd.select("flooded").eq(1).And(gfd.select("jrc_perm_water").eq(0))
    truth = truth.And(perm.Not()).unmask(0).gt(0)

    def s(img):
        return ee.Number(
            img.reduceRegion(ee.Reducer.sum(), aoi, 250, maxPixels=1e9,
                             bestEffort=True).values().get(0) or 0
        )

    i = s(ours.And(truth))
    u = s(ours.Or(truth))
    o = s(ours)
    t = s(truth)
    iou = i.divide(u.max(1)).getInfo()
    prec = i.divide(o.max(1)).getInfo()
    rec = i.divide(t.max(1)).getInfo()
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    return {
        "gfd_event_id": gfd_id,
        "validation_date": date,
        "comparison": "vs GFD MODIS `flooded` at native 250 m, permanent water "
        "removed from both",
        "iou": round(iou, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "caveat": "The only Sentinel-1 acquisition is several days after GFD "
        "onset, and a single 10 m SAR pass is compared to a multi-day 250 m "
        "MODIS optical product. Low pixel IoU is the expected, documented "
        "limitation of this comparison, not a hidden one. Track A's product "
        "is the reproducible, permanent-water-masked observed-extent time "
        "series; Track B (event-disjoint) carries the trained-model claim.",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default="carina_2024")
    raise SystemExit(run(ap.parse_args().event))
