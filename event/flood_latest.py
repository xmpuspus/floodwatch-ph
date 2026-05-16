"""Near-real-time Track A — latest Sentinel-1 pass flood extent.

OBSERVED, NOT A FORECAST, NOT LIVE. This runs the EXACT same detection method
as event/flood_extent.py (Otsu-on-VH + got-darker-vs-dry-baseline change gate
+ permanent-water + slope + HAND flood-plausible-terrain) on the most recent
usable Sentinel-1 acquisition over the Greater Metro Manila + Central Luzon
corridor. S1 revisit is ~6–12 days, so "latest" means the newest *satellite
pass*, lagged by days, never instantaneous.

The detection functions are imported from event/flood_extent.py — not
reimplemented — so the locked permanent-water CI gate and the published method
stay byte-for-byte identical to the validated event path.

Hard reliability guards (audit-mandated — the prior pipeline could silently
ship empty data as if it were "no flood"):
  - every EE init + getInfo wrapped in bounded retry/backoff (event/_ee_retry)
  - getInfo feature payloads capped well under the locked 5000-abort cap
  - if there is no usable pass / a degenerate Otsu valley / an implausible
    feature count, we write an EMPTY FeatureCollection and an honest
    _meta.scan_status instead of a fake flood polygon or a blank-map lie.

Output: site/public/data/flood_latest.geojson
Schema: docs/research/SCHEMA-latest.md (the contract Agents B and D build to).
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from event._ee_retry import ee_init_retry, get_info_retry  # noqa: E402
from event.fetch_s1_latest import (  # noqa: E402
    AOI_BBOX,
    AOI_NAME,
    BASELINE_DAYS,
    DEFAULT_LOOKBACK_DAYS,
    aoi_geometry,
    detect_latest_pass,
)

# Reuse the VALIDATED detection method verbatim (do not reimplement).
from event.flood_extent import (  # noqa: E402
    _flood_image,
    _s1_vh_vv,
    _vectorize,
)
from event.permanent_water import (  # noqa: E402
    flood_plausible_terrain,
    land_slope_ok,
    permanent_water_mask,
)
from floodwatch_ph.eeauth import init_ee  # noqa: E402

DATA = HERE.parent / "site" / "public" / "data"
METHOD = (
    "S1 VH: Otsu-on-VH + got-darker-vs-dry-baseline change gate + "
    "permanent-water + slope + HAND-style flood-plausible-terrain mask "
    "(identical to event/flood_extent.py), run on the latest usable S1 pass"
)

# Implausibility band for a single ~1.3 deg corridor pass. Above the upper
# bound the Otsu valley almost certainly latched onto SAR speckle / agriculture
# rather than flood; treat as low-confidence rather than publish a fake sheet.
MAX_PLAUSIBLE_FLOOD_KM2 = 4000.0
# Otsu valley is clamped to [-24, -14] dB in _flood_image; a value pinned to
# either rail means the histogram had no real water/land separation.
OTSU_RAIL_LO, OTSU_RAIL_HI = -24.0, -14.0


def _now_iso() -> str:
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _write(meta: dict, features: list) -> Path:
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "flood_latest.geojson"
    out.write_text(
        json.dumps(
            {"type": "FeatureCollection", "_meta": meta, "features": features}
        )
    )
    (DATA / "flood_latest_meta.json").write_text(json.dumps(meta, indent=2))
    return out


def _base_meta(scan_status: str, **extra) -> dict:
    """Schema-stable _meta. Carries every key tests/test_schema.py and
    scripts/check_permanent_water.py require (event, label, role, gauged,
    permanent_water_masked, aoi_name, bbox, dates) PLUS the realtime fields
    documented in docs/research/SCHEMA-latest.md."""
    meta = {
        # --- keys required by the existing flood_*.geojson schema/CI ---
        "event": "latest",
        "label": "Latest Sentinel-1 pass — Greater Metro Manila + Central Luzon",
        "role": "realtime",
        "gauged": False,
        "permanent_water_masked": True,  # CI-gated (locked decision 2)
        "aoi_name": AOI_NAME,
        "bbox": AOI_BBOX,
        "dates": [],  # populated only on a successful 'ok' scan
        # --- near-real-time specific fields (SCHEMA-latest.md contract) ---
        "scan_status": scan_status,
        "observed_not_forecast": True,
        "generated_at": _now_iso(),
        "as_of": None,
        "lookback_days": DEFAULT_LOOKBACK_DAYS,
        "baseline_days": BASELINE_DAYS,
        "s1_scene_ids": [],
        "feature_count": 0,
        "method": METHOD,
        "disclaimer": (
            "Observed flood extent derived from public Sentinel-1 SAR. This is "
            "the most recent satellite pass (S1 revisit ~6–12 days), not a "
            "forecast and not live. Patterns may have legitimate explanations; "
            "figures warrant independent verification."
        ),
    }
    meta.update(extra)
    return meta


def run(lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> int:
    ee = ee_init_retry(init_ee)

    def gi(obj, label):
        return get_info_retry(obj, init_fn=init_ee, label=label)

    aoi = aoi_geometry(ee)

    pass_info = detect_latest_pass(ee, aoi, gi, lookback_days=lookback_days)

    if pass_info["status"] != "ok":
        meta = _base_meta(
            "no_usable_pass",
            note=(
                f"No Sentinel-1 acquisition with >= {int(0.55 * 100)}% AOI "
                f"coverage in the last {lookback_days} days."
            ),
        )
        out = _write(meta, [])
        print(
            f"[flood_latest] scan_status=no_usable_pass "
            f"(lookback {lookback_days} d) -> wrote empty {out.name}"
        )
        return 0

    as_of = pass_info["as_of"]
    scene_ids = pass_info["scene_ids"]
    orbit_pass = pass_info["orbit_pass"]
    rel_orbit = pass_info["rel_orbit"]

    # Dry baseline: median VH over BASELINE_DAYS ending the day before the
    # event pass, SAME orbit pass + relative orbit so the change detection is
    # like-for-like (this is what the validated event path does with its fixed
    # dry window; here the window is derived from the detected pass date).
    ev_d0 = as_of
    ev_d1 = (_dt.date.fromisoformat(as_of) + _dt.timedelta(days=1)).isoformat()
    b1 = as_of
    b0 = (
        _dt.date.fromisoformat(as_of) - _dt.timedelta(days=BASELINE_DAYS)
    ).isoformat()

    def _orbit_filtered(coll):
        return coll.filter(
            ee.Filter.eq("orbitProperties_pass", orbit_pass)
        ).filter(ee.Filter.eq("relativeOrbitNumber_start", rel_orbit))

    perm = permanent_water_mask(ee).clip(aoi)
    slope_ok = land_slope_ok(ee).clip(aoi)
    plausible = flood_plausible_terrain(ee).clip(aoi)

    base_vh = (
        _orbit_filtered(_s1_vh_vv(ee, aoi, b0, b1))
        .select("VH")
        .median()
        .focal_median(50, "circle", "meters")
    )
    ev_img = _orbit_filtered(_s1_vh_vv(ee, aoi, ev_d0, ev_d1)).median()

    flood, thr = _flood_image(
        ee, aoi, base_vh, ev_img, perm, slope_ok, plausible
    )
    thr_v = float(gi(thr, "otsu_threshold"))

    area_km2 = gi(
        ee.Number(
            flood.multiply(ee.Image.pixelArea())
            .reduceRegion(
                ee.Reducer.sum(), aoi, 30, maxPixels=1e9, bestEffort=True
            )
            .get("flood")
        ).divide(1e6),
        "flood_area_km2",
    )
    area_km2 = round(float(area_km2 or 0.0), 2)

    # _vectorize already enforces VEC_MIN_KM2 + VEC_MAX_FEATS (2600 << 5000
    # getInfo abort cap), so this payload is always bounded.
    fc = gi(_vectorize(ee, flood, aoi), "vectorize_flood")
    raw_feats = fc.get("features", [])
    features = [
        {
            "type": "Feature",
            "geometry": ft["geometry"],
            "properties": {"date": as_of, "event": "latest"},
        }
        for ft in raw_feats
        if ft.get("geometry")
    ]
    n = len(features)

    # ---- degenerate / low-confidence guards ----
    scan_status = "ok"
    note = None
    if thr_v <= OTSU_RAIL_LO + 1e-6 or thr_v >= OTSU_RAIL_HI - 1e-6:
        scan_status = "degenerate_threshold"
        note = (
            f"Otsu valley pinned to clamp rail ({thr_v:.2f} dB) — no real "
            "water/land separation in the histogram; extent not published."
        )
    elif area_km2 > MAX_PLAUSIBLE_FLOOD_KM2:
        scan_status = "low_confidence"
        note = (
            f"Detected area {area_km2:.0f} km2 exceeds the plausibility cap "
            f"({MAX_PLAUSIBLE_FLOOD_KM2:.0f} km2) for one corridor pass — "
            "likely speckle/agriculture, not flood; extent not published."
        )

    if scan_status != "ok":
        # Honest empty FC — never ship a fabricated polygon.
        meta = _base_meta(
            scan_status,
            as_of=as_of,
            s1_scene_ids=scene_ids,
            lookback_days=lookback_days,
            feature_count=0,
            otsu_threshold_db=round(thr_v, 3),
            rejected_flood_area_km2=area_km2,
            orbit_pass=orbit_pass,
            relative_orbit=rel_orbit,
            aoi_coverage=pass_info.get("coverage"),
            note=note,
        )
        out = _write(meta, [])
        print(
            f"[flood_latest] as_of={as_of} scan_status={scan_status} "
            f"(area={area_km2} km2, Otsu={thr_v:.2f} dB) -> empty {out.name}"
        )
        return 0

    meta = _base_meta(
        "ok",
        as_of=as_of,
        s1_scene_ids=scene_ids,
        lookback_days=lookback_days,
        feature_count=n,
        otsu_threshold_db=round(thr_v, 3),
        orbit_pass=orbit_pass,
        relative_orbit=rel_orbit,
        aoi_coverage=pass_info.get("coverage"),
        dates=[
            {
                "date": as_of,
                "flood_area_km2": area_km2,
                "otsu_threshold_db": round(thr_v, 3),
                "n_polygons": n,
            }
        ],
    )
    out = _write(meta, features)
    print(
        f"[flood_latest] as_of={as_of} scan_status=ok area={area_km2} km2 "
        f"Otsu={thr_v:.2f} dB feature_count={n} -> wrote {out.name}"
    )
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS
    )
    raise SystemExit(run(ap.parse_args().lookback_days))
