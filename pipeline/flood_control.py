"""Flood-control accountability cross-reference and emit.

Joins the BetterGovPH flood-control subset against FloodWatch's own signal:
- `hazard_gap.geojson` 82 province polygons (recurrence_score, observed_events,
  gap class), used both for the point-in-polygon province resolution and as
  the source of the province-centroid fallback.
- `flood_carina_2024.geojson` dated Sentinel-1 observed-extent polygons; for
  each project with coordinates, record which dated passes its location fell
  within observed water.

Writes two governed files into site/public/data/:
- `flood_control_accountability.json` aggregate-only (by_province / by_type /
  by_tranche + _meta). No named-project list anywhere.
- `flood_control_by_id.json` every project keyed by id, lookup-only.

Conservative posture: "warrants independent investigation", never an
accusation. No efficacy or causation language. The disclaimer and
public-record block are baked into every record; assert_governed runs before
either file is written.

Run:
  python3 pipeline/flood_control.py

Offline / deterministic CI: when pipeline/_dpwh_flood_control_cache.parquet is
present the adapter reads it and no network is touched.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from floodwatch_ph.accountability import governance  # noqa: E402
from floodwatch_ph.adapters.flood_control import FloodControlAdapter  # noqa: E402

DATA = HERE.parent / "site" / "public" / "data"
CACHE = HERE / "_dpwh_flood_control_cache.parquet"
PRONE_T = 0.60  # matches pipeline/hazard_gap.py PRONE_T

ACCOUNTABILITY_OUT = DATA / "flood_control_accountability.json"
BY_ID_OUT = DATA / "flood_control_by_id.json"


def _polygonal(geom):
    """Reduce a geometry to its polygonal part, dropping lines and points.

    hazard_gap features are a mix of Polygon, MultiPolygon, and
    GeometryCollection (the last carrying stray LineStrings). Containment
    tests need polygons only.
    """
    g = shape(geom)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g.buffer(0)
    if g.geom_type == "GeometryCollection":
        polys = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        if not polys:
            return None
        from shapely.ops import unary_union

        return unary_union(polys).buffer(0)
    return None


def _load_province_index() -> tuple[STRtree, list, list[dict]]:
    """Build an STRtree over the 82 hazard_gap province polygons.

    Returns (tree, geoms, props) where geoms[i] aligns with props[i].
    """
    fc = json.loads((DATA / "hazard_gap.geojson").read_text())
    geoms: list = []
    props: list[dict] = []
    for f in fc["features"]:
        g = _polygonal(f["geometry"])
        if g is None or g.is_empty:
            continue
        geoms.append(g)
        props.append(f["properties"])
    return STRtree(geoms), geoms, props


def _load_observed_passes() -> list[tuple[str, object]]:
    """Return (date, polygon) for every dated Sentinel-1 observed-extent shape."""
    fc = json.loads((DATA / "flood_carina_2024.geojson").read_text())
    out: list[tuple[str, object]] = []
    for f in fc["features"]:
        g = shape(f["geometry"]).buffer(0)
        if g.is_empty:
            continue
        out.append((str(f["properties"].get("date", "")), g))
    return out


def _province_centroid_lookup(props: list[dict], geoms: list) -> dict[str, int]:
    """Map a province-text token to a hazard_gap polygon index.

    The bettergovph location.province is a DEO name ("Bulacan 1st DEO");
    hazard_gap city is the bare province ("Bulacan"). Match on the leading
    province token, case-insensitive.
    """
    idx: dict[str, int] = {}
    for i, p in enumerate(props):
        idx[str(p.get("city", "")).lower().strip()] = i
    return idx


def _resolve_province_text(province_raw: str, name_index: dict[str, int]) -> int | None:
    """Resolve a DEO-style province string to a hazard_gap polygon index."""
    s = province_raw.lower().strip()
    if not s:
        return None
    if s in name_index:
        return name_index[s]
    # Strip trailing DEO descriptors: "bulacan 1st deo" -> "bulacan".
    for token in (" deo", " 1st", " 2nd", " 3rd", " 4th", " 5th", " 6th"):
        s = s.split(token)[0].strip()
    for key, i in name_index.items():
        if s == key or s.startswith(key) or key.startswith(s):
            return i
    return None


def main() -> int:
    adapter = FloodControlAdapter()
    snapshot = adapter.fetch(HERE)
    if snapshot is None:
        print(
            "[flood_control] fetch failed and no cache present; cannot proceed",
            file=sys.stderr,
        )
        return 1

    snapshot_sha = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    df = adapter.parse(snapshot)
    n_projects = len(df)
    if n_projects == 0:
        print("[flood_control] parsed zero flood-control projects", file=sys.stderr)
        return 1

    tree, geoms, props = _load_province_index()
    name_index = _province_centroid_lookup(props, geoms)
    observed = _load_observed_passes()

    # Per-province accumulators.
    prov_n: dict[int, int] = defaultdict(int)
    prov_alloc: dict[int, float] = defaultdict(float)
    prov_flagged: dict[int, int] = defaultdict(int)
    prov_passes: dict[int, set] = defaultdict(set)

    type_n: dict[str, int] = defaultdict(int)
    type_alloc: dict[str, float] = defaultdict(float)
    type_flagged: dict[str, int] = defaultdict(int)

    tranche_n: dict[str, int] = defaultdict(int)
    tranche_alloc: dict[str, float] = defaultdict(float)
    tranche_flagged: dict[str, int] = defaultdict(int)

    total_alloc = 0.0
    projects_map: dict[str, dict] = {}

    for rec in df.to_dict("records"):
        pid = rec["project_id"]
        amount = rec["contract_amount"]
        amount_val = (
            float(amount)
            if amount is not None and amount == amount and amount > 0
            else None
        )
        alloc_int = int(round(amount_val)) if amount_val is not None else None
        if amount_val is not None:
            total_alloc += amount_val

        lat, lon = rec["latitude"], rec["longitude"]
        lat = lat if lat is not None and lat == lat else None
        lon = lon if lon is not None and lon == lon else None
        prov_idx: int | None = None
        confidence = float(rec["geolocation_confidence"])

        if lat is not None and lon is not None:
            pt = Point(lon, lat)
            for i in tree.query(pt):
                if geoms[i].contains(pt):
                    prov_idx = int(i)
                    break
        if prov_idx is None:
            prov_idx = _resolve_province_text(str(rec["province"]), name_index)
            confidence = 0.6  # province-centroid fallback

        # Dated observed passes the project location falls within.
        passes: list[str] = []
        if lat is not None and lon is not None:
            pt = Point(lon, lat)
            for date, poly in observed:
                if poly.contains(pt):
                    if date not in passes:
                        passes.append(date)
        observed_passes = len(passes)

        recurrence = None
        province_name = None
        region_name = None
        if prov_idx is not None:
            pp = props[prov_idx]
            recurrence = float(pp.get("recurrence_score") or 0.0)
            province_name = pp.get("city")
            region_name = pp.get("province")

        is_prone = recurrence is not None and recurrence >= PRONE_T
        flagged = is_prone and observed_passes > 0

        if prov_idx is not None:
            prov_n[prov_idx] += 1
            if amount_val is not None:
                prov_alloc[prov_idx] += amount_val
            if flagged:
                prov_flagged[prov_idx] += 1
            for d in passes:
                prov_passes[prov_idx].add(d)

        ptype = rec["project_type"]
        type_n[ptype] += 1
        if amount_val is not None:
            type_alloc[ptype] += amount_val
        if flagged:
            type_flagged[ptype] += 1

        tranche = governance.tranche_for(amount_val)
        if tranche is not None:
            tranche_n[tranche] += 1
            tranche_alloc[tranche] += amount_val or 0.0
            if flagged:
                tranche_flagged[tranche] += 1

        projects_map[pid] = {
            "title": rec["title"],
            "allocation_php": alloc_int,
            "status": rec["status"],
            "geolocation_confidence": round(confidence, 2),
            "province": province_name,
            "region": region_name,
            "recurrence_score": round(recurrence, 3) if recurrence is not None else None,
            "observed_flood_passes": observed_passes,
            "disclaimer": governance.DISCLAIMER,
        }

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    by_province = []
    for i in sorted(prov_n, key=lambda k: str(props[k].get("city") or "")):
        pp = props[i]
        n = prov_n[i]
        by_province.append(
            {
                "province": pp.get("city"),
                "region": pp.get("province"),
                "n_projects": n,
                "allocation_php": int(round(prov_alloc[i])),
                "recurrence_score": round(float(pp.get("recurrence_score") or 0.0), 3),
                "observed_events": int(pp.get("observed_events") or 0),
                "gap": pp.get("gap"),
                "observed_flood_passes": len(prov_passes[i]),
                "flagged_rate": round(prov_flagged[i] / n, 4) if n else 0.0,
                "warrants_investigation": bool(
                    prov_alloc[i] > 0
                    and (
                        float(pp.get("recurrence_score") or 0.0) >= PRONE_T
                        or len(prov_passes[i]) > 0
                    )
                ),
                "disclaimer": governance.DISCLAIMER,
            }
        )

    by_type = []
    for t in sorted(type_n, key=lambda k: -type_alloc[k]):
        n = type_n[t]
        by_type.append(
            {
                "project_type": t,
                "n_projects": n,
                "allocation_php": int(round(type_alloc[t])),
                "flagged_rate": round(type_flagged[t] / n, 4) if n else 0.0,
                "disclaimer": governance.DISCLAIMER,
            }
        )

    by_tranche = []
    for label, _lo, _hi in governance.BUDGET_TRANCHES:
        n = tranche_n.get(label, 0)
        by_tranche.append(
            {
                "tranche": label,
                "n_projects": n,
                "allocation_php": int(round(tranche_alloc.get(label, 0.0))),
                "flagged_rate": round(tranche_flagged.get(label, 0) / n, 4) if n else 0.0,
                "disclaimer": governance.DISCLAIMER,
            }
        )

    total_alloc_int = int(round(total_alloc))

    accountability = {
        "_meta": {
            "source": "BetterGovPH bettergovph/dpwh-transparency-data (CC0)",
            "snapshot_sha256": snapshot_sha,
            "n_projects": n_projects,
            "total_allocation_php": total_alloc_int,
            "generated_utc": generated,
            "scope": "BetterGovPH DPWH transparency, flood-control subset",
            "population": (
                "DPWH category 'Flood Control and Drainage' plus "
                "unclassified-category projects whose description is "
                "flood-control; explicitly road/bridge/building-categorized "
                "projects excluded even when they include drainage components"
            ),
            "geolocation_caveat": "MYPS planning coords; ~10-15% uncertain (COA)",
            "warrants_investigation_rule": (
                "allocation_php > 0 AND (recurrence_score >= 0.60 OR "
                "observed_flood_passes > 0)"
            ),
            "prone_threshold": PRONE_T,
            "disclaimer": governance.DISCLAIMER,
            "public_record_block": governance.PUBLIC_RECORD_BLOCK,
        },
        "by_province": by_province,
        "by_type": by_type,
        "by_tranche": by_tranche,
    }

    by_id = {
        "_meta": {
            "source": "BetterGovPH bettergovph/dpwh-transparency-data (CC0)",
            "snapshot_sha256": snapshot_sha,
            "n_projects": n_projects,
            "generated_utc": generated,
            "population": (
                "DPWH category 'Flood Control and Drainage' plus "
                "unclassified-category projects whose description is "
                "flood-control; explicitly road/bridge/building-categorized "
                "projects excluded even when they include drainage components"
            ),
            "geolocation_caveat": "MYPS planning coords; ~10-15% uncertain (COA)",
            "disclaimer": governance.DISCLAIMER,
            "public_record_block": governance.PUBLIC_RECORD_BLOCK,
        },
        "projects": projects_map,
    }

    governance.assert_governed(accountability)
    governance.assert_governed(by_id)

    DATA.mkdir(parents=True, exist_ok=True)
    ACCOUNTABILITY_OUT.write_text(json.dumps(accountability, ensure_ascii=False))
    BY_ID_OUT.write_text(json.dumps(by_id, ensure_ascii=False))

    resolved = sum(prov_n.values())
    print(
        f"[flood_control] {n_projects} flood-control projects, "
        f"total_allocation_php={total_alloc_int}, "
        f"{resolved} resolved to a province, "
        f"snapshot_sha256={snapshot_sha}"
    )
    print(f"[flood_control] wrote {ACCOUNTABILITY_OUT.name} ({len(by_province)} provinces, "
          f"{len(by_type)} types, {len(by_tranche)} tranches)")
    print(f"[flood_control] wrote {BY_ID_OUT.name} ({len(projects_map)} projects)")
    for row in by_province:
        print(
            f"  {row['province']}: n={row['n_projects']} "
            f"alloc={row['allocation_php']} rec={row['recurrence_score']} "
            f"passes={row['observed_flood_passes']} "
            f"warrants={row['warrants_investigation']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
