"""Build site/public/data/current_risk.geojson — the near-real-time RAINFALL
CONTEXT layer for FloodWatch.PH.

WHAT THIS IS / IS NOT
---------------------
This is NOT a flood forecast, NOT a flood probability, NOT a risk score. It is
GPM IMERG rainfall *accumulation* (already-fallen rain) sampled over the
EXISTING modeled flood-prone areas (Track B, recurrence_prone.geojson), as of
the latest available IMERG timestamp. It exists to bridge the Sentinel-1 SAR
revisit gap (6-12 day cadence): heavy rain over known-prone areas since the
last possible SAR pass is *context*, not a prediction. For warnings, PAGASA.

OUTPUT SCHEMA — site/public/data/current_risk.geojson  (read by Agent D / G)
---------------------------------------------------------------------------
FeatureCollection with a top-level ``_meta`` block.

_meta:
  as_of                : str  ISO8601 UTC — latest IMERG image time used
  generated_at         : str  ISO8601 UTC — when this file was built
  windows              : {h24:int, h72:int} accumulation window lengths (hours)
  aoi                  : {name:str, bbox:[W,S,E,N]}
  source               : "NASA GPM IMERG V07"
  band_definition_source : str — citation for the rainfall-advisory band labels
  scan_status          : "ok" | "no_data" | "low_confidence"
  feature_count        : int
  disclaimer           : str (one line, mandatory)
  prone_source         : provenance of the prone mask used
  context_bands        : the label band table actually applied

features[]: Point Feature, geometry = the prone-grid sample point.
  properties:
    rain_mm_24h        : float  accumulated mm over the last 24 h
    rain_mm_72h        : float  accumulated mm over the last 72 h
    context_flag       : "none" | "yellow" | "orange" | "red"
                         (RAINFALL-INTENSITY label over a prone area;
                          explicitly NOT flood likelihood)
    prone_score        : float  Track B calibrated recurrence score (passthrough)

CONTEXT BAND LABELS (labels only — describe rainfall, not flooding)
-------------------------------------------------------------------
PAGASA color-coded rainfall advisory thresholds are defined on 1-hour
rainfall: Yellow 7.5-15 mm/h, Orange 15-30 mm/h, Red >30 mm/h. We do not
observe a flood; we report multi-hour GPM accumulation. We map the same color
*labels* onto 24-hour accumulation using the PAGASA 1-hour band edges scaled to
a conservative sustained-rain proxy (band edge x 4 h of sustained rain):
Yellow >=30 mm/24h, Orange >=60 mm/24h, Red >=120 mm/24h. This is a labeling
convention for context only; it is not a PAGASA product and not a flood
forecast. Source: Official Gazette PH, "How to make sense of PAGASA's
color-coded warning signals"
(https://www.officialgazette.gov.ph/how-to-make-sense-of-pagasas-color-coded-warning-signals/);
PAGASA legend (https://www.pagasa.dost.gov.ph/learnings/legend).
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

from realtime.ee_retry import get_info, init_ee_retry  # noqa: E402
from realtime.fetch_gpm import (  # noqa: E402
    AOI_BBOX,
    accumulation_image,
    aoi_geometry,
    latest_imerg_time,
)

PRONE_GEOJSON = _REPO / "site" / "public" / "data" / "recurrence_prone.geojson"
OUT_GEOJSON = _REPO / "site" / "public" / "data" / "current_risk.geojson"

AOI_NAME = "Greater Metro Manila + Central Luzon (SLEX/NLEX corridor)"
WINDOW_H24 = 24
WINDOW_H72 = 72

# Label edges on 24-hour accumulation (mm). See module docstring for the
# PAGASA 1-hour band -> sustained-rain proxy derivation.
BAND_YELLOW_MM24 = 30.0
BAND_ORANGE_MM24 = 60.0
BAND_RED_MM24 = 120.0

BAND_DEFINITION_SOURCE = (
    "PAGASA color-coded rainfall advisory (Yellow 7.5-15, Orange 15-30, "
    "Red >30 mm/h, 1-hour rainfall), mapped as LABELS onto 24h GPM "
    "accumulation (>=30 / >=60 / >=120 mm/24h). Not a PAGASA product; "
    "context only. Source: Official Gazette PH "
    "(officialgazette.gov.ph/how-to-make-sense-of-pagasas-color-coded-"
    "warning-signals/); PAGASA legend (pagasa.dost.gov.ph/learnings/legend)."
)

DISCLAIMER = (
    "Rainfall accumulation over modeled flood-prone areas as of {as_of}. "
    "Context only - not a flood forecast. For warnings use PAGASA."
)

CONTEXT_BANDS = {
    "yellow": f">= {BAND_YELLOW_MM24:.0f} mm / 24h",
    "orange": f">= {BAND_ORANGE_MM24:.0f} mm / 24h",
    "red": f">= {BAND_RED_MM24:.0f} mm / 24h",
}


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _band(mm24: float) -> str:
    if mm24 >= BAND_RED_MM24:
        return "red"
    if mm24 >= BAND_ORANGE_MM24:
        return "orange"
    if mm24 >= BAND_YELLOW_MM24:
        return "yellow"
    return "none"


def _load_prone_points_in_aoi(ee):
    """Load Track B prone points clipped to the AOI bbox as an ee.FeatureCollection.

    Returns (ee.FeatureCollection, n:int). Uses the existing modeled-prone mask
    (recurrence_prone.geojson) — does NOT recompute Track B.
    """
    gj = json.loads(PRONE_GEOJSON.read_text())
    w, s, e, n = AOI_BBOX
    feats = []
    for f in gj["features"]:
        if not f["properties"].get("prone"):
            continue
        x, y = f["geometry"]["coordinates"]
        if w <= x <= e and s <= y <= n:
            feats.append(
                ee.Feature(
                    ee.Geometry.Point([x, y]),
                    {"prone_score": float(f["properties"].get("score", 0.0))},
                )
            )
    return ee.FeatureCollection(feats), len(feats)


def _write(meta: dict, features: list[dict]) -> None:
    OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_GEOJSON.write_text(
        json.dumps(
            {"type": "FeatureCollection", "_meta": meta, "features": features},
            separators=(",", ":"),
        )
    )


def build() -> dict:
    """Run the full pipeline against live IMERG. Returns the _meta block."""
    generated_at = _now_utc_iso()
    base_meta = {
        "generated_at": generated_at,
        "windows": {"h24": WINDOW_H24, "h72": WINDOW_H72},
        "aoi": {"name": AOI_NAME, "bbox": AOI_BBOX},
        "source": "NASA GPM IMERG V07",
        "band_definition_source": BAND_DEFINITION_SOURCE,
        "context_bands": CONTEXT_BANDS,
        "prone_source": (
            "recurrence_prone.geojson (Track B recurrence_clf_v1, "
            "prone flag passthrough; not recomputed)"
        ),
    }

    ee = init_ee_retry()
    aoi = aoi_geometry(ee)

    # Latest IMERG timestamp (the 'as of'). If empty -> no_data, no fabrication.
    try:
        as_of_dt, _ = get_info(lambda: latest_imerg_time(ee, aoi))
    except (LookupError, RuntimeError) as exc:
        print(f"[current_risk] no IMERG data: {exc!r}", file=sys.stderr)
        meta = {
            **base_meta,
            "as_of": None,
            "scan_status": "no_data",
            "feature_count": 0,
            "disclaimer": DISCLAIMER.format(as_of="n/a"),
        }
        _write(meta, [])
        return meta

    as_of = as_of_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    acc24, n24 = accumulation_image(ee, aoi, as_of_dt, WINDOW_H24)
    acc72, n72 = accumulation_image(ee, aoi, as_of_dt, WINDOW_H72)

    if not n24 and not n72:
        meta = {
            **base_meta,
            "as_of": as_of,
            "scan_status": "no_data",
            "feature_count": 0,
            "disclaimer": DISCLAIMER.format(as_of=as_of),
        }
        _write(meta, [])
        return meta

    prone_fc, n_prone = _load_prone_points_in_aoi(ee)
    if n_prone == 0:
        meta = {
            **base_meta,
            "as_of": as_of,
            "scan_status": "no_data",
            "feature_count": 0,
            "disclaimer": DISCLAIMER.format(as_of=as_of),
        }
        _write(meta, [])
        return meta
    if n_prone > 4500:  # locked EE getInfo 5000 abort cap — stay well under
        raise RuntimeError(
            f"{n_prone} prone points exceeds the 4500 getInfo cap; "
            "coarsen the AOI"
        )

    # Server-side sample both accumulation rasters at the prone points.
    # IMERG native grid ~0.1 deg (~11132 m); sample at native scale.
    stacked = acc24.rename("rain_mm_24h").addBands(acc72.rename("rain_mm_72h"))
    sampled = stacked.reduceRegions(
        collection=prone_fc,
        reducer=ee.Reducer.first(),
        scale=11132,
    )
    fc = get_info(lambda: sampled.getInfo())

    features: list[dict] = []
    for f in fc["features"]:
        p = f["properties"]
        mm24 = p.get("rain_mm_24h")
        mm72 = p.get("rain_mm_72h")
        mm24 = round(float(mm24), 2) if mm24 is not None else 0.0
        mm72 = round(float(mm72), 2) if mm72 is not None else 0.0
        features.append(
            {
                "type": "Feature",
                "geometry": f["geometry"],
                "properties": {
                    "rain_mm_24h": mm24,
                    "rain_mm_72h": mm72,
                    "context_flag": _band(mm24),
                    "prone_score": round(float(p.get("prone_score", 0.0)), 3),
                },
            }
        )

    # low_confidence if a window is sparsely populated (expected full counts:
    # ~48 slices/24h, ~144/72h at 30-min cadence).
    sparse = n24 < 24 or n72 < 72
    scan_status = "low_confidence" if sparse else "ok"

    meta = {
        **base_meta,
        "as_of": as_of,
        "scan_status": scan_status,
        "feature_count": len(features),
        "imerg_slices": {"h24": n24, "h72": n72},
        "disclaimer": DISCLAIMER.format(as_of=as_of),
    }
    _write(meta, features)
    return meta


if __name__ == "__main__":
    m = build()
    print(json.dumps(m, indent=2))
    print("feature_count:", m["feature_count"])
