"""Expressway / major-road flood-exposure join (near-real-time Track A).

Intersects the most recent Sentinel-1 *observed* flood extent
(`site/public/data/flood_latest.geojson`, produced by `event/flood_latest.py`,
schema in `docs/research/SCHEMA-latest.md`) with the Philippine expressway +
major-road network pulled live from OpenStreetMap via the Overpass API.

The point of this file is the headline civic use-case: "which expressway
segments (SLEX / NLEX / Skyway / ...) intersected water in the latest satellite
pass". It is OBSERVED, lagged by the S1 revisit (~6-12 days), and is NOT a
forecast or a routing instruction.

Roads source
------------
OpenStreetMap (100% public, no paid deps), Overpass API. We query
`highway in (motorway, motorway_link, trunk, trunk_link, primary, primary_link)`
inside the flood AOI bbox. Residential/service roads are dropped to keep the
output mobile-friendly. Named expressways (SLEX, NLEX, SCTEX, Skyway incl.
Stage 3, CAVITEX, TPLEX, NAIAX, C5, EDSA, Commonwealth) are labelled from the
OSM `ref` / `name` tags. The raw Overpass response is cached to
`pipeline/_osm_roads_cache.geojson` so reruns are deterministic-ish and don't
hammer Overpass; delete that file (or pass --refresh-osm) to re-fetch.

scan_status handling (honest, no fake intersections)
----------------------------------------------------
`flood_latest.geojson` carries `_meta.scan_status` in
`{ok, no_usable_pass, degenerate_threshold, low_confidence}`. Only when it is
`"ok"` (and there are polygons) do we compute real intersections. For every
other status we still emit every monitored segment but with
`exposure="unknown"` and `_meta.note` explaining the satellite pass was not
usable. The site must show "no usable pass", never a misleading "0 roads
flooded".

Geometry / metric math
----------------------
Flood polygons and roads are reprojected to PH UTM zone 51N (EPSG:32651) for
all length / buffer math. Flood polygons are buffered by `BUFFER_M` (30 m) to
account for SAR pixel size + vector simplification edge, so a road running
immediately alongside detected water is flagged. Per segment we compute:
intersected length (m), flooded fraction, and a categorical `exposure`:

  flooded  meaningful overlap (>= FLOODED_FRACTION_MIN of the segment, or
           >= FLOODED_LENGTH_MIN metres of it, inside the *unbuffered* water)
  near     touches only the 30 m buffer / a minor clip of real water
  clear    no overlap with water or its buffer
  unknown  scan_status != "ok" (pass not usable)

Output schema -- site/public/data/road_flood_exposure.geojson
-------------------------------------------------------------
FeatureCollection. Each feature:
  geometry  LineString | MultiLineString (WGS84, simplified ~10 m)
  properties {
    road_name        str   human name (ref/name, normalised)
    ref              str   OSM ref tag (e.g. "E2", "N1") or ""
    osm_id           int   OSM way id
    highway_class    str   motorway | trunk | primary (+ _link)
    exposure         str   flooded | near | clear | unknown
    flooded_length_m float metres of this segment under detected water
    flooded_fraction float 0..1 of the segment length under detected water
    is_expressway    bool  named limited-access expressway
  }
_meta {
  generated_at        ISO-8601 UTC
  as_of               carried from flood_latest (the S1 pass date) or null
  scan_status         carried from flood_latest
  source              "OpenStreetMap (Overpass) ∩ Sentinel-1 observed extent"
  buffer_m            30
  road_scope          str   which OSM classes are monitored (motorway+trunk,
                       named expressways, ref-bearing primary; link ramps and
                       ref-less local primary excluded for mobile size)
  aoi_name, bbox      carried from flood_latest
  observed_not_forecast  true
  feature_count       int
  note                present when scan_status != "ok" (why exposure=unknown)
  expressway_summary  per named expressway: {flooded, near, clear, unknown,
                       flooded_km}
  disclaimer          public-data / not-a-forecast / not-routing string
}
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import requests
from pyproj import Transformer
from shapely.geometry import (
    LineString,
    MultiLineString,
    mapping,
    shape,
)
from shapely.ops import transform as shp_transform
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "site" / "public" / "data"
OSM_CACHE = HERE / "_osm_roads_cache.geojson"
FLOOD_PATH = DATA / "flood_latest.geojson"
OUT_PATH = DATA / "road_flood_exposure.geojson"

# --- tuning -----------------------------------------------------------------
BUFFER_M = 30.0  # SAR pixel + vector-simplification edge tolerance
FLOODED_FRACTION_MIN = 0.05  # >=5% of the segment under real water -> flooded
FLOODED_LENGTH_MIN = 80.0  # ...or >=80 m of it -> flooded (short ramps)
SIMPLIFY_M = 12.0  # tolerance for flooded/near segments (precision matters)
SIMPLIFY_CLEAR_M = 110.0  # clear segments far from water: coarse is fine, the
# map only needs their rough shape so the corridor is visible
COORD_DECIMALS = 5  # ~1 m precision; plenty for road display, halves file size
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Named limited-access / arterial corridors we explicitly surface. Matching is
# case-insensitive substring against the OSM ref+name. Order matters: first hit
# wins so "Skyway Stage 3" is checked before "Skyway".
EXPRESSWAY_PATTERNS: list[tuple[str, list[str], bool]] = [
    ("Skyway Stage 3", ["skyway stage 3", "skyway stage iii", "metro manila skyway stage 3"], True),
    ("Skyway", ["skyway", "metro manila skyway", "smc skyway"], True),
    ("SLEX", ["slex", "south luzon expressway"], True),
    ("NLEX", ["nlex", "north luzon expressway"], True),
    ("SCTEX", ["sctex", "subic–clark–tarlac", "subic-clark-tarlac"], True),
    ("TPLEX", ["tplex", "tarlac–pangasinan–la union", "tarlac-pangasinan-la union"], True),
    ("CAVITEX", ["cavitex", "manila–cavite expressway", "manila-cavite expressway", "coastal road"], True),
    ("NAIAX", ["naiax", "naia expressway"], True),
    ("CALAX", ["calax", "cavite–laguna expressway", "cavite-laguna expressway"], True),
    ("C5", ["c-5", "c5 road", "circumferential road 5", "carlos p. garcia"], False),
    ("EDSA", ["edsa", "epifanio de los santos"], False),
    ("Commonwealth Ave", ["commonwealth avenue", "commonwealth ave"], False),
]


def _overpass_query(bbox: list[float]) -> str:
    w, s, e, n = bbox
    # Overpass bbox order is (south, west, north, east)
    bb = f"{s},{w},{n},{e}"
    return f"""
[out:json][timeout:120];
(
  way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link)$"]({bb});
);
out body geom;
""".strip()


def _fetch_overpass(bbox: list[float]) -> dict:
    """Fetch road ways from Overpass with backoff+jitter across mirrors."""
    query = _overpass_query(bbox)
    last_err: Exception | None = None
    attempts = 4
    for i in range(attempts):
        endpoint = OVERPASS_ENDPOINTS[i % len(OVERPASS_ENDPOINTS)]
        try:
            r = requests.post(
                endpoint, data={"data": query},
                headers={"User-Agent": "FloodWatch.PH/1.0 road-exposure"},
                timeout=180,
            )
            if r.status_code == 200:
                js = r.json()
                if js.get("elements"):
                    return js
                raise RuntimeError("Overpass returned 0 road elements")
            raise RuntimeError(f"Overpass HTTP {r.status_code} from {endpoint}")
        except Exception as exc:  # noqa: BLE001 -- retried and re-raised loudly
            last_err = exc
            wait = (2 ** i) + random.uniform(0, 1.5)
            print(f"[road] Overpass attempt {i + 1}/{attempts} via {endpoint} "
                  f"failed: {exc} -- retrying in {wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(
        f"Overpass unreachable after {attempts} attempts (last: {last_err}). "
        "Refusing to emit a fake/empty road file. Re-run when Overpass is up "
        "or supply a populated pipeline/_osm_roads_cache.geojson."
    )


def _overpass_to_features(js: dict) -> list[dict]:
    """Flatten Overpass `out geom` ways into GeoJSON LineString features."""
    feats = []
    for el in js.get("elements", []):
        if el.get("type") != "way":
            continue
        geom = el.get("geometry") or []
        if len(geom) < 2:
            continue
        coords = [[p["lon"], p["lat"]] for p in geom]
        tags = el.get("tags", {})
        feats.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "osm_id": el["id"],
                "highway": tags.get("highway", ""),
                "ref": tags.get("ref", "") or "",
                "name": tags.get("name", "") or "",
            },
        })
    return feats


def _load_roads(bbox: list[float], refresh: bool) -> list[dict]:
    if OSM_CACHE.exists() and not refresh:
        cached = json.loads(OSM_CACHE.read_text())
        feats = cached.get("features", [])
        if feats:
            print(f"[road] using cached OSM roads: {len(feats)} ways "
                  f"({OSM_CACHE.name})")
            return feats
    print("[road] querying Overpass for the AOI road network ...")
    js = _fetch_overpass(bbox)
    feats = _overpass_to_features(js)
    if not feats:
        raise RuntimeError("Overpass response had no usable road ways.")
    OSM_CACHE.write_text(json.dumps(
        {"type": "FeatureCollection", "features": feats}))
    print(f"[road] fetched {len(feats)} road ways from Overpass, cached to "
          f"{OSM_CACHE.name}")
    return feats


def _round_geom(geom: dict, nd: int) -> dict:
    """Round LineString/MultiLineString coords in-place for wire size."""
    t = geom["type"]
    if t == "LineString":
        geom["coordinates"] = [[round(x, nd), round(y, nd)]
                               for x, y in geom["coordinates"]]
    elif t == "MultiLineString":
        geom["coordinates"] = [
            [[round(x, nd), round(y, nd)] for x, y in part]
            for part in geom["coordinates"]
        ]
    return geom


def _classify(ref: str, name: str) -> tuple[str, str, bool]:
    """-> (display road_name, canonical expressway key or '', is_expressway)."""
    hay = f"{ref} {name}".lower()
    for key, pats, is_xpwy in EXPRESSWAY_PATTERNS:
        if any(p in hay for p in pats):
            disp = name.strip() or ref.strip() or key
            return disp, key, is_xpwy
    disp = (name.strip() or ref.strip() or "Unnamed road")
    return disp, "", False


def run(refresh_osm: bool = False) -> int:
    flood = json.loads(FLOOD_PATH.read_text())
    fmeta = flood.get("_meta", {})
    scan_status = fmeta.get("scan_status", "no_usable_pass")
    as_of = fmeta.get("as_of")
    bbox = fmeta.get("bbox", [120.40, 14.00, 121.55, 15.40])
    aoi_name = fmeta.get("aoi_name", "Greater Metro Manila + Central Luzon")

    road_feats = _load_roads(bbox, refresh_osm)

    # Metric projection: WGS84 <-> PH UTM zone 51N
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
    to_ll = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)

    def fwd(x, y, z=None):
        return to_m.transform(x, y)

    def inv(x, y, z=None):
        return to_ll.transform(x, y)

    usable = scan_status == "ok" and bool(flood.get("features"))
    water_m = None
    water_buf_m = None
    if usable:
        polys = [shape(ft["geometry"]) for ft in flood["features"]]
        water_ll = unary_union(polys)
        water_m = shp_transform(fwd, water_ll)
        if not water_m.is_valid:
            water_m = water_m.buffer(0)
        water_buf_m = water_m.buffer(BUFFER_M)

    out_features: list[dict] = []
    summary: dict[str, dict] = {}

    for rf in road_feats:
        p = rf["properties"]
        hw = p.get("highway", "")
        ref = p.get("ref", "") or ""
        name = p.get("name", "") or ""
        osm_id = p.get("osm_id")
        disp_name, xpwy_key, is_xpwy = _classify(ref, name)
        highway_class = hw

        # Scope to the flood-routing network (the "route around flooded
        # SLEX/NLEX" use-case): all motorway + trunk, every named expressway,
        # and ref-bearing primary (PH national highways N1/N2/... = the real
        # alternate routes). Dropped: non-expressway link/ramp stubs and
        # ref-less local "primary" city streets — clutter that does not help
        # routing and would blow the mobile size budget. Documented in
        # _meta.road_scope so the site/QA know exactly what is monitored.
        if hw.endswith("_link") and not is_xpwy:
            continue
        if hw.startswith("primary") and not is_xpwy and not ref:
            continue

        try:
            line_ll = shape(rf["geometry"])
        except Exception:  # noqa: BLE001 -- skip malformed OSM geometry
            continue
        if line_ll.is_empty or line_ll.length == 0:
            continue
        line_m = shp_transform(fwd, line_ll)
        seg_len = line_m.length
        if seg_len <= 0:
            continue

        flooded_len = 0.0
        if usable:
            inter_real = line_m.intersection(water_m)
            flooded_len = inter_real.length if not inter_real.is_empty else 0.0
            inter_buf = line_m.intersection(water_buf_m)
            near_len = inter_buf.length if not inter_buf.is_empty else 0.0
            frac = flooded_len / seg_len if seg_len else 0.0
            if (frac >= FLOODED_FRACTION_MIN
                    or flooded_len >= FLOODED_LENGTH_MIN):
                exposure = "flooded"
            elif flooded_len > 0 or near_len > 0:
                exposure = "near"
            else:
                exposure = "clear"
        else:
            exposure = "unknown"
            frac = 0.0

        # simplify for the wire, back to WGS84. Clear segments (the bulk of
        # the AOI, far from any water) get a coarse tolerance; flooded/near
        # segments keep fine detail so the affected stretch is accurate.
        tol = SIMPLIFY_M if exposure in ("flooded", "near") else SIMPLIFY_CLEAR_M
        line_m_s = line_m.simplify(tol, preserve_topology=False)
        if line_m_s.is_empty:
            line_m_s = line_m
        geom_ll = shp_transform(inv, line_m_s)
        if isinstance(geom_ll, (LineString, MultiLineString)):
            geom_out = _round_geom(mapping(geom_ll), COORD_DECIMALS)
        else:
            geom_out = _round_geom(mapping(line_ll), COORD_DECIMALS)

        out_features.append({
            "type": "Feature",
            "geometry": geom_out,
            "properties": {
                "road_name": disp_name,
                "ref": ref,
                "osm_id": osm_id,
                "highway_class": highway_class,
                "exposure": exposure,
                "flooded_length_m": round(flooded_len, 1),
                "flooded_fraction": round(frac, 4),
                "is_expressway": bool(is_xpwy),
            },
        })

        if xpwy_key:
            s = summary.setdefault(xpwy_key, {
                "flooded": 0, "near": 0, "clear": 0, "unknown": 0,
                "flooded_km": 0.0,
            })
            s[exposure] += 1
            s["flooded_km"] += flooded_len / 1000.0

    for s in summary.values():
        s["flooded_km"] = round(s["flooded_km"], 3)

    note = None
    if not usable:
        reason = {
            "no_usable_pass": "no S1 acquisition with sufficient AOI coverage "
            "in the lookback window",
            "degenerate_threshold": "the last S1 pass had no reliable "
            "water/land separation",
            "low_confidence": "the last S1 pass detected an implausible extent "
            "(withheld)",
        }.get(scan_status, "the latest Sentinel-1 pass was not usable")
        note = (f"Exposure is 'unknown' for every segment because {reason}. "
                "No intersection was computed; this is not '0 roads flooded'.")

    fc = {
        "type": "FeatureCollection",
        "_meta": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
            "as_of": as_of,
            "scan_status": scan_status,
            "source": "OpenStreetMap (Overpass) ∩ Sentinel-1 observed "
            "extent",
            "buffer_m": BUFFER_M,
            "road_scope": "all motorway + trunk, every named expressway "
            "(SLEX/NLEX/SCTEX/Skyway/CAVITEX/TPLEX/NAIAX/CALAX/C5/EDSA/"
            "Commonwealth), and ref-bearing primary (PH national highways = "
            "alternate routes). Non-expressway link ramps and ref-less local "
            "primary streets are excluded to keep the layer mobile-sized.",
            "aoi_name": aoi_name,
            "bbox": bbox,
            "observed_not_forecast": True,
            "feature_count": len(out_features),
            "expressway_summary": summary,
            "disclaimer": (
                f"Expressway segments intersecting the most recent Sentinel-1 "
                f"observed flood extent as of {as_of}. Observed, not a forecast "
                f"or routing instruction. For live road conditions use MMDA "
                f"Flood Control, PAGASA, LGU DRRMO."
            ),
        },
        "features": out_features,
    }
    if note:
        fc["_meta"]["note"] = note

    DATA.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(fc, separators=(",", ":")))
    size_kb = OUT_PATH.stat().st_size / 1024.0

    n_xpwy = sum(1 for f in out_features
                 if f["properties"]["is_expressway"])
    by_exp: dict[str, int] = {}
    for f in out_features:
        e = f["properties"]["exposure"]
        by_exp[e] = by_exp.get(e, 0) + 1
    print(f"[road] scan_status={scan_status} as_of={as_of}")
    print(f"[road] wrote {OUT_PATH.relative_to(HERE.parent)}: "
          f"{len(out_features)} segments ({n_xpwy} expressway), "
          f"{size_kb:.1f} KB")
    print(f"[road] exposure breakdown: {by_exp}")
    print(f"[road] expressway_summary: "
          f"{json.dumps(summary, indent=2)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-osm", action="store_true",
                    help="ignore pipeline/_osm_roads_cache.geojson and re-query "
                    "Overpass")
    raise SystemExit(run(refresh_osm=ap.parse_args().refresh_osm))
