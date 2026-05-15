"""Bootstrap recurrence labels from the Global Flood Database and build the
EVENT-DISJOINT holdout split (locked decision 1).

Each GFD event (`GLOBAL_FLOOD_DB/MODIS_EVENTS/V1` image) is one atomic unit.
A fixed-seed split assigns whole events to train or holdout. No pixel/point
is ever shared across the boundary, so adjacent-pixel leakage is impossible
by construction. The split file is hashed; CI asserts the hash and asserts
holdout event ids never appear in any training fold.

Outputs:
  model/labels.jsonl        one line per GFD PH event: id, dates, group
  model/holdout_events.json {seed, train_ids, holdout_ids, sha256}
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from floodwatch_ph.eeauth import PH_BBOX, init_ee  # noqa: E402

HERE = Path(__file__).resolve().parent
HOLDOUT_FRACTION = 0.30
SEED = 42


def main() -> int:
    ee = init_ee()
    aoi = ee.Geometry.Rectangle(PH_BBOX)
    gfd = (
        ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1")
        .filterBounds(aoi)
        .sort("system:time_start")
    )
    n = gfd.size().getInfo()
    print(f"[bootstrap] GFD events intersecting PH: {n}")

    feats = gfd.toList(n)
    events = []
    for i in range(n):
        img = ee.Image(feats.get(i))
        p = img.toDictionary(
            [
                "id",
                "dfo_centroid_x",
                "dfo_centroid_y",
                "dfo_main_cause",
                "dfo_dead",
                "dfo_displaced",
                "dfo_severity",
                "gfd_country_name",
            ]
        ).getInfo()
        ts = img.get("system:time_start").getInfo()
        began = (
            __import__("datetime")
            .datetime.fromtimestamp(ts / 1000, __import__("datetime").timezone.utc)
            .date()
            .isoformat()
            if ts
            else None
        )
        ev_id = int(p.get("id"))
        events.append(
            {
                "id": ev_id,
                "began": began,
                "main_cause": p.get("dfo_main_cause"),
                "dead": p.get("dfo_dead"),
                "displaced": p.get("dfo_displaced"),
                "severity": p.get("dfo_severity"),
                "centroid": [p.get("dfo_centroid_x"), p.get("dfo_centroid_y")],
            }
        )
    events.sort(key=lambda e: e["id"])

    # Deterministic event-disjoint split: seeded shuffle, hold out a whole
    # contiguous-after-shuffle slice of EVENTS (never points).
    import random

    rng = random.Random(SEED)
    order = list(range(len(events)))
    rng.shuffle(order)
    n_hold = max(1, round(len(events) * HOLDOUT_FRACTION))
    hold_pos = set(order[:n_hold])
    for idx, ev in enumerate(events):
        ev["group"] = "holdout" if idx in hold_pos else "train"

    train_ids = sorted(e["id"] for e in events if e["group"] == "train")
    holdout_ids = sorted(e["id"] for e in events if e["group"] == "holdout")
    assert not (set(train_ids) & set(holdout_ids)), "event leak in split"

    (HERE / "labels.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in events)
    )

    split = {
        "seed": SEED,
        "holdout_fraction": HOLDOUT_FRACTION,
        "n_events": len(events),
        "train_ids": train_ids,
        "holdout_ids": holdout_ids,
    }
    canonical = json.dumps(
        {"train_ids": train_ids, "holdout_ids": holdout_ids},
        separators=(",", ":"),
        sort_keys=True,
    )
    split["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    (HERE / "holdout_events.json").write_text(json.dumps(split, indent=2))

    print(
        f"[bootstrap] {len(train_ids)} train + {len(holdout_ids)} holdout events; "
        f"split sha256 {split['sha256'][:16]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
