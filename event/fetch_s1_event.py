"""Thin CLI to inspect Sentinel-1 acquisition dates available for an event
window (used when registering a new event). The flood pipeline itself lives
in flood_extent.py; this is the acquisition-coverage probe."""
from __future__ import annotations
import argparse, datetime, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from floodwatch_ph.eeauth import init_ee  # noqa: E402

def dates_for(bbox, d0, d1):
    ee = init_ee()
    aoi = ee.Geometry.Rectangle(bbox)
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(aoi)
          .filterDate(d0, d1).filter(ee.Filter.eq("instrumentMode", "IW"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))
    ts = s1.aggregate_array("system:time_start").getInfo()
    return sorted({datetime.datetime.fromtimestamp(t/1000, datetime.timezone.utc)
                   .date().isoformat() for t in ts})

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default="carina_2024")
    a = ap.parse_args()
    ev = json.loads((Path(__file__).resolve().parent / "events.json").read_text())[a.event]
    b = ev["baseline_window"][0]
    e = (datetime.date.fromisoformat(ev["event_dates"][-1]) + datetime.timedelta(days=5)).isoformat()
    print(a.event, "S1 dates:", dates_for(ev["bbox"], b, e))
