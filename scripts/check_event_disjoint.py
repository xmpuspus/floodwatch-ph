"""CI gate: event-disjoint holdout integrity (locked decision 1).

Three checks:
  1. train_ids ∩ holdout_ids == ∅  (no event in both splits)
  2. Canonical sha256 recomputed from the id lists matches the stored `sha256`
     field (proves the split file has not drifted since bootstrap_labels.py ran)
  3. If model/embeddings/floodwatch_embeddings_v1.npz is present: the cache
     is built from THREE mutually-exclusive server-side masks
     (pos_train = train_sum>=1 AND hold_sum==0; pos_hold = hold_sum>=1 AND
     train_sum==0; negatives = never flooded). Event-disjointness is therefore
     structural — a positive point cannot belong to both a train and a holdout
     event. This check asserts the npz schema and that `group` holds only
     {train,holdout} with positives present in BOTH groups (so the holdout is
     non-degenerate).

If the npz is absent, checks 1+2 still run and the script exits 0 with a note.

Exit code 0 = all checks pass, 1 = any violation.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPLIT_FILE = REPO / "model" / "holdout_events.json"
NPZ_PATH = REPO / "model" / "embeddings" / "floodwatch_embeddings_v1.npz"


def _canonical_sha256(train_ids: list[int], holdout_ids: list[int]) -> str:
    """Recompute the sha256 exactly as bootstrap_labels.py does."""
    payload = json.dumps(
        {"train_ids": train_ids, "holdout_ids": holdout_ids},
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def main() -> int:
    if not SPLIT_FILE.exists():
        print(f"[check_event_disjoint] FAIL: {SPLIT_FILE} not found", file=sys.stderr)
        return 1

    try:
        split = json.loads(SPLIT_FILE.read_text())
    except Exception as exc:
        print(f"[check_event_disjoint] FAIL: cannot parse {SPLIT_FILE}: {exc}", file=sys.stderr)
        return 1

    train_ids: list[int] = split.get("train_ids", [])
    holdout_ids: list[int] = split.get("holdout_ids", [])
    stored_sha256: str = split.get("sha256", "")

    fails = 0

    # Check 1: disjoint
    overlap = set(train_ids) & set(holdout_ids)
    if overlap:
        print(
            f"[check_event_disjoint] FAIL: {len(overlap)} event(s) appear in both "
            f"train and holdout: {sorted(overlap)[:10]}",
            file=sys.stderr,
        )
        fails += 1
    else:
        print(
            f"[check_event_disjoint] OK: train/holdout disjoint "
            f"({len(train_ids)} train + {len(holdout_ids)} holdout events)"
        )

    # Check 2: canonical sha256
    computed = _canonical_sha256(sorted(train_ids), sorted(holdout_ids))
    if computed != stored_sha256:
        print(
            f"[check_event_disjoint] FAIL: sha256 mismatch",
            file=sys.stderr,
        )
        print(f"  stored:   {stored_sha256}", file=sys.stderr)
        print(f"  computed: {computed}", file=sys.stderr)
        print(
            "  The split file has been edited manually or regenerated with a "
            "different seed. Run `make labels` to regenerate.",
            file=sys.stderr,
        )
        fails += 1
    else:
        print(f"[check_event_disjoint] OK: split sha256 matches ({computed[:16]}...)")

    # Check 3: npz row-group consistency
    if not NPZ_PATH.exists():
        print(
            "[check_event_disjoint] npz not present, split-file checks only"
        )
        return 0 if fails == 0 else 1

    try:
        import numpy as np
        data = np.load(NPZ_PATH, allow_pickle=True)
    except Exception as exc:
        print(
            f"[check_event_disjoint] FAIL: cannot load {NPZ_PATH}: {exc}",
            file=sys.stderr,
        )
        return 1

    if "group" not in data or "y" not in data:
        print(
            "[check_event_disjoint] FAIL: npz missing 'group' or 'y' arrays",
            file=sys.stderr,
        )
        return 1

    group_arr = data["group"].astype(str)
    y_arr = data["y"].astype(int)
    if len(group_arr) != len(y_arr):
        print(
            "[check_event_disjoint] FAIL: group and y arrays differ in length",
            file=sys.stderr,
        )
        return 1

    bad = set(group_arr) - {"train", "holdout"}
    if bad:
        print(
            f"[check_event_disjoint] FAIL: unexpected group values {sorted(bad)}",
            file=sys.stderr,
        )
        fails += 1
    else:
        import numpy as np

        tr_pos = int(((group_arr == "train") & (y_arr == 1)).sum())
        ho_pos = int(((group_arr == "holdout") & (y_arr == 1)).sum())
        ho_neg = int(((group_arr == "holdout") & (y_arr == 0)).sum())
        if tr_pos == 0 or ho_pos == 0 or ho_neg == 0:
            print(
                "[check_event_disjoint] FAIL: degenerate split "
                f"(train_pos={tr_pos}, holdout_pos={ho_pos}, holdout_neg={ho_neg})",
                file=sys.stderr,
            )
            fails += 1
        else:
            print(
                "[check_event_disjoint] OK: structural event-disjoint cache "
                f"({len(y_arr)} rows; holdout has {ho_pos} pos / {ho_neg} neg)"
            )

    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
