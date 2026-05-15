"""Verify the event-disjoint holdout split file (model/holdout_events.json).

Three assertions:
  1. train_ids ∩ holdout_ids == ∅
  2. Canonical sha256 recomputed from the id lists matches the stored value
  3. holdout_fraction is in (0, 1) — a sanity check that the split is real

These run offline from committed files with no network access.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPLIT_FILE = ROOT / "model" / "holdout_events.json"


@pytest.fixture(scope="module")
def split():
    if not SPLIT_FILE.exists():
        pytest.skip(f"{SPLIT_FILE} not present")
    return json.loads(SPLIT_FILE.read_text())


def _canonical_sha256(train_ids: list[int], holdout_ids: list[int]) -> str:
    payload = json.dumps(
        {"train_ids": train_ids, "holdout_ids": holdout_ids},
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def test_train_holdout_disjoint(split):
    """No event id appears in both train and holdout."""
    train = set(split["train_ids"])
    holdout = set(split["holdout_ids"])
    overlap = train & holdout
    assert not overlap, (
        f"{len(overlap)} event(s) appear in both train and holdout: {sorted(overlap)}"
    )


def test_canonical_sha256_matches(split):
    """Recomputed sha256 matches the stored value — proves the split has not drifted."""
    train_ids = sorted(split["train_ids"])
    holdout_ids = sorted(split["holdout_ids"])
    computed = _canonical_sha256(train_ids, holdout_ids)
    stored = split["sha256"]
    assert computed == stored, (
        f"sha256 mismatch:\n  stored:   {stored}\n  computed: {computed}\n"
        "Run `make labels` to regenerate from scratch."
    )


def test_holdout_fraction_in_range(split):
    """holdout_fraction is a real value in (0, 1) — catches accidental overwrites."""
    frac = split["holdout_fraction"]
    assert 0 < frac < 1, f"holdout_fraction={frac!r} is out of range (0, 1)"
