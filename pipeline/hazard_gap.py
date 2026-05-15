"""The civic layer (v1.0 honest scope): the gap between MODELED flood-proneness
(Track B recurrence_clf_v1) and the HISTORICAL OBSERVED flood record (GFD).

Per city/municipality (FAO GAUL level-2) in the v1.0 Luzon reference region
(union of the Carina + Koppu AOIs):
  recurrence_score  mean Track B calibrated score of recurrence-prone sample
                    points falling in the unit
  observed_events   GFD historical flood-event count intersecting the unit
  gap:
    "under_observed_prone"  recurrence_score >= 0.60 and observed_events <= 1
                            (the model flags it prone; the historical record
                            barely captured it — the headline civic finding)
    "charted"               observed_events >= 3 (well-recorded flood zone)
    "monitored"             recurrence_score >= 0.60 and observed_events == 2
    "low"                   otherwise

The official UP NOAH / PAGASA / MGB hazard-map cross-reference is the v1.1
extension (those layers are token-gated/SPA-only — the documented PH failure
mode). Conservative civic language; public-records disclaimer on the layer.

Output: site/public/data/hazard_gap.geojson
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from floodwatch_ph.eeauth import init_ee  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "site" / "public" / "data"
PRONE_T = 0.60


def main() -> int:
    ee = init_ee()
    from floodwatch_ph.eeauth import PH_BBOX

    region = ee.Geometry.Rectangle(PH_BBOX)  # national: all PH provinces
    adm = ee.FeatureCollection(
        "FAO/GAUL_SIMPLIFIED_500m/2015/level2"
    ).filter(ee.Filter.eq("ADM0_NAME", "Philippines"))
    prone = json.loads((DATA / "recurrence_prone.geojson").read_text())
    pts = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Point(ft["geometry"]["coordinates"]),
                   {"score": ft["properties"]["score"]})
        for ft in prone["features"]
    ])
    gfd = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1").filterBounds(region)
    ev_count = gfd.select("flooded").map(lambda im: im.gt(0)).sum().unmask(0)

    def annotate(f):
        g = f.geometry()
        in_pts = pts.filterBounds(g)
        score = ee.Algorithms.If(in_pts.size().gt(0),
                                 in_pts.aggregate_mean("score"), 0)
        ec = ev_count.reduceRegion(ee.Reducer.max(), g, 250, maxPixels=1e9,
                                   bestEffort=True).values().get(0)
        return f.set({"_score": score, "_ev": ec})

    fc = adm.map(annotate).getInfo()
    feats, counts = [], {}
    for ft in fc["features"]:
        pr = ft["properties"]
        s = round(float(pr.get("_score") or 0), 3)
        ec = int(pr.get("_ev") or 0)
        if s >= PRONE_T and ec <= 1:
            gap = "under_observed_prone"
        elif ec >= 3:
            gap = "charted"
        elif s >= PRONE_T and ec == 2:
            gap = "monitored"
        else:
            gap = "low"
        counts[gap] = counts.get(gap, 0) + 1
        feats.append({
            "type": "Feature",
            "geometry": ft["geometry"],
            "properties": {
                "city": pr.get("ADM2_NAME"),
                "province": pr.get("ADM1_NAME"),
                "recurrence_score": s,
                "observed_events": ec,
                "gap": gap,
            },
        })

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "hazard_gap.geojson").write_text(json.dumps({
        "type": "FeatureCollection",
        "_meta": {
            "scope": "v1.0 Luzon reference region (Carina + Koppu AOI union)",
            "model": "recurrence_clf_v1",
            "prone_threshold": PRONE_T,
            "official_hazard_overlay": "v1.1 (PH gov hazard layers token-gated/"
            "SPA-only — documented PH civic-data failure mode)",
            "gap_counts": counts,
            "disclaimer": "Modeled flood-proneness vs the historical observed "
            "record, from public satellite data. Patterns may have legitimate "
            "explanations; figures warrant independent verification.",
        },
        "features": feats,
    }))
    print(f"[hazard_gap] wrote hazard_gap.geojson: {len(feats)} units, "
          f"gap counts {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
