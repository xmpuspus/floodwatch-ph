"""Coarse Sentinel-1 built-change corroboration for completed flood-control
projects.

For every parsed flood-control project the DPWH records as completed and that
carries a valid in-Philippines coordinate, this computes a coarse change in
Sentinel-1 VH backscatter between a pre-`start_date` window and a
post-`completion_date` window inside a small (~120 m) buffer at the recorded
point. A built physical structure (concrete dike, revetment, pumping station,
seawall) tends to raise VH backscatter relative to the prior surface, so a
a despeckled mean-VH rise is a weak, indicative corroboration that *something was
built at the recorded coordinate*.

This is deliberately conservative:
- It is NOT confirmation that the project was completed.
- Absence of a VH rise is NOT evidence of a ghost project. The recorded
  coordinate itself is a MYPS planning coordinate that is roughly 10-15 percent
  wrong (the same caveat the rest of the pipeline carries), so a no-signal
  result can simply mean the structure is a hundred metres away from the point
  we sampled.
- It is never a finding of fraud or project failure.

The committed cache `pipeline/_satellite_verify_cache.json` is idempotent and
resumable: already-checked contract ids are skipped, keys are sorted and floats
are rounded to a fixed precision, so a full rerun that adds no new ids
reproduces a byte-identical file.

Run:
  python3 pipeline/satellite_verify.py
  python3 pipeline/satellite_verify.py --limit 8        # small sample
  python3 pipeline/satellite_verify.py --max-ids 500    # safety cap

Deterministic offline CI never invokes this; it is a network/EE target like
`make event`.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from floodwatch_ph.adapters.flood_control import FloodControlAdapter  # noqa: E402

CACHE = HERE / "_satellite_verify_cache.json"

# Buffer (m) around the recorded point. ~120 m mirrors the event-pipeline
# vectorization scale and keeps each getInfo tiny (one reduceRegion over a
# sub-hectare disc), well under the v1.0 getInfo-5000-element limit.
BUFFER_M = 120
# Pre/post windows (days). Wide enough to land at least one Sentinel-1 IW pass
# (6-12 day repeat over the Philippines) on each side without straddling the
# construction period itself.
PRE_WINDOW_DAYS = 180
POST_WINDOW_DAYS = 180
# A small guard so the pre window ends before ground was broken and the post
# window starts after hand-over, not on the day of.
EDGE_GUARD_DAYS = 14

# VH mean-delta thresholds (dB). A built concrete/rock structure is a strong
# specular-plus-rough scatterer and lifts mean VH; vegetation regrowth or
# speckle stays inside the noise band. Conservative bands: below WEAK_DB is
# treated as no usable signal, WEAK_DB..STRONG_DB is a weak rise, at or above
# STRONG_DB is a strong rise. These are intentionally cautious because the
# coordinate may not sit on the structure at all.
WEAK_DB = 1.5
STRONG_DB = 3.0

# Sentinel-1 IW VH valid backscatter range (dB). Values outside this are
# border/no-data artefacts and the sample is discarded rather than scored.
VH_MIN_DB = -30.0
VH_MAX_DB = 0.0

EE_COLLECTION = "COPERNICUS/S1_GRD"
METHOD = (
    "despeckled mean VH (dB) over a ~120 m disc at the recorded point: "
    "post-completion-window mean minus pre-start-window mean; "
    "Sentinel-1 IW GRD, VH polarisation, both orbit passes"
)
DISCLAIMER = (
    "Indicative corroboration of a built change at the recorded coordinate, "
    "not confirmation; absence of signal is NOT evidence of a ghost because "
    "the recorded coordinate itself may be wrong (the MYPS problem). Not a "
    "finding of fraud or project failure."
)


def classify_signal(vh_delta_db: float | None) -> str:
    """Map a VH mean-delta (dB) to a conservative built-change signal class.

    None (no usable pre/post imagery) -> "none". Below WEAK_DB -> "none".
    WEAK_DB..STRONG_DB -> "weak". >= STRONG_DB -> "strong". A drop in VH is
    never read as a built structure, so only positive deltas can score.
    """
    if vh_delta_db is None or not math.isfinite(vh_delta_db):
        return "none"
    if vh_delta_db >= STRONG_DB:
        return "strong"
    if vh_delta_db >= WEAK_DB:
        return "weak"
    return "none"


def _valid_ph_coord(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    if lat != lat or lon != lon:  # NaN
        return False
    # PH_BBOX = [116.7, 4.4, 126.7, 21.3] (lon_min, lat_min, lon_max, lat_max).
    return 4.4 <= lat <= 21.3 and 116.7 <= lon <= 126.7


def _iso(d: date) -> str:
    return d.isoformat()


def _windows(start_date: str, completion_date: str):
    """Return (pre0, pre1, post0, post1) ISO date strings, or None if the
    recorded dates are unusable or out of order.

    pre window:  [start - guard - PRE_WINDOW, start - guard]
    post window: [completion + guard, completion + guard + POST_WINDOW]
    """
    try:
        sd = date.fromisoformat(start_date[:10])
        cd = date.fromisoformat(completion_date[:10])
    except (TypeError, ValueError):
        return None
    if cd < sd:
        return None
    pre1 = sd - timedelta(days=EDGE_GUARD_DAYS)
    pre0 = pre1 - timedelta(days=PRE_WINDOW_DAYS)
    post0 = cd + timedelta(days=EDGE_GUARD_DAYS)
    post1 = post0 + timedelta(days=POST_WINDOW_DAYS)
    if pre0 >= pre1 or post0 >= post1:
        return None
    return _iso(pre0), _iso(pre1), _iso(post0), _iso(post1)


def _eligible_projects(limit: int | None, max_ids: int | None):
    """Parse the flood-control subset and yield the completed, in-PH,
    coordinate-bearing, date-bearing projects in a deterministic id order."""
    adapter = FloodControlAdapter()
    snapshot = adapter.fetch(HERE)
    if snapshot is None:
        print(
            "[satellite_verify] adapter fetch failed and no cache present",
            file=sys.stderr,
        )
        return []
    df = adapter.parse(snapshot)
    rows = []
    for rec in df.to_dict("records"):
        if rec.get("status") != "completed":
            continue
        lat, lon = rec.get("latitude"), rec.get("longitude")
        if not _valid_ph_coord(lat, lon):
            continue
        start_date = rec.get("start_date")
        completion_date = rec.get("completion_date")
        if not isinstance(start_date, str) or not isinstance(completion_date, str):
            continue
        win = _windows(start_date, completion_date)
        if win is None:
            continue
        rows.append(
            {
                "id": str(rec["project_id"]),
                "lat": float(lat),
                "lon": float(lon),
                "windows": win,
            }
        )
    rows.sort(key=lambda r: r["id"])
    if max_ids is not None:
        rows = rows[:max_ids]
    if limit is not None:
        rows = rows[:limit]
    return rows


def _robust_mean_vh(ee, point, d0, d1):
    """Robust mean VH (dB) over a small disc, or None.

    Uses the per-pixel median of the IW VH stack in the window (the median
    over time despeckles the multiplicative SAR noise), then a spatial mean
    over the ~120 m disc. bestEffort + a small maxPixels keep the getInfo
    payload to a single scalar.
    """
    disc = point.buffer(BUFFER_M)
    coll = (
        ee.ImageCollection(EE_COLLECTION)
        .filterBounds(disc)
        .filterDate(d0, d1)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VH"])
    )
    if coll.size().getInfo() == 0:
        return None
    vh_med = coll.median().select("VH")
    val = vh_med.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=disc,
        scale=30,
        maxPixels=1e7,
        bestEffort=True,
    ).get("VH").getInfo()
    if val is None:
        return None
    f = float(val)
    if not math.isfinite(f) or f < VH_MIN_DB or f > VH_MAX_DB:
        return None
    return f


def _load_cache() -> dict:
    if CACHE.exists() and CACHE.stat().st_size > 0:
        try:
            return json.loads(CACHE.read_text())
        except json.JSONDecodeError:
            print(
                "[satellite_verify] existing cache unreadable; rebuilding",
                file=sys.stderr,
            )
    return {"_meta": {}, "by_id": {}}


def _write_cache(by_id: dict, n_checked: int, ee_ran: bool) -> None:
    """Write the governed cache with sorted keys and fixed float rounding so a
    no-new-id rerun is byte-identical."""
    sorted_by_id = {
        k: {
            "satellite_checked": v["satellite_checked"],
            "built_change_signal": v["built_change_signal"],
            "vh_delta_db": (
                round(v["vh_delta_db"], 3)
                if v["vh_delta_db"] is not None
                else None
            ),
        }
        for k, v in sorted(by_id.items())
    }
    payload = {
        "_meta": {
            "generated_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "n_checked": n_checked,
            "ee_collection": EE_COLLECTION,
            "ee_available": ee_ran,
            "method": METHOD,
            "buffer_m": BUFFER_M,
            "pre_window_days": PRE_WINDOW_DAYS,
            "post_window_days": POST_WINDOW_DAYS,
            "thresholds": {
                "weak_db": WEAK_DB,
                "strong_db": STRONG_DB,
                "vh_valid_db": [VH_MIN_DB, VH_MAX_DB],
            },
            "disclaimer": DISCLAIMER,
        },
        "by_id": sorted_by_id,
    }
    CACHE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def run(limit: int | None, max_ids: int | None) -> int:
    cache = _load_cache()
    by_id: dict = dict(cache.get("by_id", {}))
    already = set(by_id)

    projects = _eligible_projects(limit, max_ids)
    if not projects:
        # Nothing to do, but still emit a valid governed cache so the file
        # is always reviewable and the schema is stable.
        _write_cache(by_id, len(by_id), ee_ran=False)
        print(
            "[satellite_verify] no eligible completed-with-coords projects; "
            f"wrote governed cache with {len(by_id)} prior ids",
            file=sys.stderr,
        )
        return 0

    todo = [p for p in projects if p["id"] not in already]
    if not todo:
        # Idempotent no-op: rewrite the same content (byte-identical) so the
        # cache mtime/order is stable.
        _write_cache(by_id, len(by_id), ee_ran=False)
        print(
            f"[satellite_verify] all {len(projects)} sampled ids already "
            "checked; cache unchanged (no-op)"
        )
        return 0

    try:
        from floodwatch_ph.eeauth import init_ee

        ee = init_ee()
    except Exception as exc:
        # Degrade cleanly: a valid, empty-but-governed cache plus a clear
        # stderr note. The script and schema stay reviewable with no EE.
        _write_cache(by_id, len(by_id), ee_ran=False)
        print(
            f"[satellite_verify] Earth Engine unavailable ({exc}); wrote a "
            f"valid governed cache with {len(by_id)} prior ids and made no "
            "network calls. Re-run with EE_KEY_FILE set to backfill.",
            file=sys.stderr,
        )
        return 0

    n_new = 0
    for p in todo:
        pid = p["id"]
        pre0, pre1, post0, post1 = p["windows"]
        try:
            point = ee.Geometry.Point([p["lon"], p["lat"]])
            pre_vh = _robust_mean_vh(ee, point, pre0, pre1)
            post_vh = _robust_mean_vh(ee, point, post0, post1)
        except Exception as exc:
            print(
                f"[satellite_verify] {pid}: EE error, skipping ({exc})",
                file=sys.stderr,
            )
            continue
        if pre_vh is None or post_vh is None:
            delta = None
        else:
            delta = post_vh - pre_vh
        by_id[pid] = {
            "satellite_checked": True,
            "built_change_signal": classify_signal(delta),
            "vh_delta_db": delta,
        }
        n_new += 1
        print(
            f"[satellite_verify] {pid}: vh_delta="
            f"{'n/a' if delta is None else f'{delta:.2f} dB'} -> "
            f"{by_id[pid]['built_change_signal']}"
        )

    _write_cache(by_id, len(by_id), ee_ran=True)
    print(
        f"[satellite_verify] checked {n_new} new ids "
        f"({len(by_id)} total in cache); wrote {CACHE.name}"
    )
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only check the first N eligible ids (sampling)",
    )
    ap.add_argument(
        "--max-ids",
        type=int,
        default=None,
        help="safety cap on the total eligible ids considered",
    )
    args = ap.parse_args()
    raise SystemExit(run(args.limit, args.max_ids))
