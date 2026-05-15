"""Province-level exposure aggregation (v1.0 honest scope).

FAO GAUL level-2 = Philippine provinces. Per unit over the event AOI:
  population        WorldPop 2020 (sum, rounded to nearest 10)
  built_up_km2      GHSL built surface 2020 (honest area, not a fabricated count)
  observed_events   number of GFD historical flood events intersecting the unit
  peak_flood_pct    max over the event's Sentinel-1 dates of (flooded area in
                    unit / unit area), from the Track A flood polygons
Barangay-resolution and the official-hazard-map cross-reference are documented
v1.1 refinements (PH barangay polygons / PH gov hazard layers are not a clean
public asset — the documented PH civic-data failure mode).

Output: site/public/data/barangay_exposure.json  (keyed by admin id; the key
name is retained for site compatibility — values are province units)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from floodwatch_ph.eeauth import init_ee  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "site" / "public" / "data"


def run(event_key: str) -> int:
    ee = init_ee()
    events = json.loads((HERE.parent / "event" / "events.json").read_text())
    ev = events[event_key]
    aoi = ee.Geometry.Rectangle(ev["bbox"])

    adm = (
        ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level2")
        .filter(ee.Filter.eq("ADM0_NAME", "Philippines"))
        .filterBounds(aoi)
        .map(lambda f: f.intersection(aoi, 100))
    )
    pop = ee.ImageCollection("WorldPop/GP/100m/pop").filter(
        ee.Filter.eq("year", 2020)
    ).filter(ee.Filter.eq("country", "PHL")).mosaic()
    built = (
        ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2020")
        .select("built_surface")
    )
    gfd = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1").filterBounds(aoi)

    # observed historical event count per unit (server-side)
    ev_count = gfd.select("flooded").map(
        lambda im: im.gt(0).rename("f")
    ).sum().unmask(0)

    flood_fc = json.loads((DATA / f"flood_{event_key}.geojson").read_text())
    dates = sorted({ft["properties"]["date"] for ft in flood_fc["features"]})

    def per_unit(f):
        geom = f.geometry()
        area = geom.area(100)
        p = pop.reduceRegion(ee.Reducer.sum(), geom, 100, maxPixels=1e9,
                             bestEffort=True).get("population")
        b = built.reduceRegion(ee.Reducer.sum(), geom, 100, maxPixels=1e9,
                               bestEffort=True).get("built_surface")
        ec = ev_count.reduceRegion(ee.Reducer.max(), geom, 250, maxPixels=1e9,
                                   bestEffort=True).values().get(0)
        return f.set({"_pop": p, "_built": b, "_area": area, "_ev": ec})

    units = adm.map(per_unit).getInfo()

    # peak flood % per unit across dates, from Track A polygons (EE intersection)
    flood_by_date = {}
    for d in dates:
        fc = ee.FeatureCollection([
            ee.Feature(ee.Geometry(ft["geometry"]))
            for ft in flood_fc["features"] if ft["properties"]["date"] == d
        ])
        flood_by_date[d] = fc.geometry().simplify(100)

    out = {}
    for ft in units["features"]:
        pr = ft["properties"]
        uid = str(pr.get("ADM2_CODE"))
        name = pr.get("ADM2_NAME")
        prov = pr.get("ADM1_NAME")
        area_m2 = pr.get("_area") or 0
        geom = ee.Geometry(ft["geometry"])
        peak = 0.0
        for d in dates:
            inter = geom.intersection(flood_by_date[d], 100).area(100).getInfo()
            if area_m2:
                peak = max(peak, inter / area_m2)
        out[uid] = {
            "name": name,
            "city": name,
            "province": prov,
            "population": int(round((pr.get("_pop") or 0) / 10.0) * 10),
            "built_up_km2": round((pr.get("_built") or 0) / 1e6, 3),
            "observed_events": int(pr.get("_ev") or 0),
            "peak_flood_pct": round(peak * 100, 2),
            "on_official_hazard_map": None,
        }

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "barangay_exposure.json").write_text(json.dumps({
        "_meta": {
            "event": event_key,
            "admin_level": "province (FAO GAUL level-2, ~82 PH provinces); "
            "city/barangay resolution is a v1.1 refinement",
            "official_hazard_overlay": "v1.1 (PH gov hazard layers are "
            "token-gated/SPA-only — documented PH civic-data failure mode)",
            "disclaimer": "Observed flood exposure derived from public satellite "
            "data. Patterns may have legitimate explanations; figures warrant "
            "independent verification.",
        },
        "units": out,
    }, indent=2))
    print(f"[exposure] wrote barangay_exposure.json: {len(out)} province "
          f"units for {event_key}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default="carina_2024")
    raise SystemExit(run(ap.parse_args().event))
