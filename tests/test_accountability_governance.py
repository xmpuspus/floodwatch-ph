"""Governance + cross-reference truth-table tests.

Mirrors the ghostwatch test_api.py disclaimer-presence gate, adapted to the
static data layer: every emitted aggregate record must carry the exact
DISCLAIMER, assert_governed must raise on a tampered disclaimer, the by-id map
must be a dict not a list, and the conservative warrants_investigation rule
must hold on the published artifact. No network; runs from committed files and
pure functions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from floodwatch_ph.accountability import governance

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "site" / "public" / "data"
ACCT = DATA_DIR / "flood_control_accountability.json"
BYID = DATA_DIR / "flood_control_by_id.json"

PRESENT = ACCT.exists() and BYID.exists()
skip_absent = pytest.mark.skipif(
    not PRESENT, reason="accountability JSON not present (Phase-1-only build)"
)


# ---------------------------------------------------------------------------
# assert_governed: raises on missing / altered disclaimer
# ---------------------------------------------------------------------------


def _good_obj() -> dict:
    return {
        "_meta": {
            "disclaimer": governance.DISCLAIMER,
            "public_record_block": governance.PUBLIC_RECORD_BLOCK,
        },
        "by_province": [{"province": "X", "disclaimer": governance.DISCLAIMER}],
        "projects": {"P1": {"title": "t", "disclaimer": governance.DISCLAIMER}},
    }


def test_assert_governed_passes_on_good_object():
    governance.assert_governed(_good_obj())  # must not raise


def test_assert_governed_raises_on_tampered_meta_disclaimer():
    obj = _good_obj()
    obj["_meta"]["disclaimer"] = governance.DISCLAIMER + " (edited)"
    with pytest.raises(ValueError, match="disclaimer missing or altered"):
        governance.assert_governed(obj)


def test_assert_governed_raises_on_missing_public_record_block():
    obj = _good_obj()
    del obj["_meta"]["public_record_block"]
    with pytest.raises(ValueError, match="public_record_block"):
        governance.assert_governed(obj)


def test_assert_governed_raises_on_record_missing_disclaimer():
    obj = _good_obj()
    obj["by_province"][0].pop("disclaimer")
    with pytest.raises(ValueError, match=r"by_province\[0\]"):
        governance.assert_governed(obj)


def test_assert_governed_raises_when_projects_is_a_list():
    obj = _good_obj()
    obj["projects"] = [{"title": "t", "disclaimer": governance.DISCLAIMER}]
    with pytest.raises(ValueError, match="projects must be a dict"):
        governance.assert_governed(obj)


# ---------------------------------------------------------------------------
# tranche_for: budget banding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "amount,label",
    [
        (None, None),
        (0, None),
        (-5, None),
        (5_000_000, "<₱10M"),
        (10_000_000, "₱10-50M"),
        (49_999_999, "₱10-50M"),
        (50_000_000, "₱50-100M"),
        (100_000_000, "₱100-500M"),
        (499_999_999, "₱100-500M"),
        (500_000_000, ">₱500M"),
        (9_000_000_000, ">₱500M"),
    ],
)
def test_tranche_for(amount, label):
    assert governance.tranche_for(amount) == label


# ---------------------------------------------------------------------------
# cross-reference rule: warrants_investigation
# ---------------------------------------------------------------------------

PRONE_T = __import__("pipeline.flood_control", fromlist=["PRONE_T"]).PRONE_T


def _warrants(allocation: float, recurrence: float, passes: int) -> bool:
    """The conservative rule, verbatim from pipeline/flood_control.py:
    allocation > 0 AND (recurrence_score >= PRONE_T OR observed passes > 0)."""
    return bool(allocation > 0 and (recurrence >= PRONE_T or passes > 0))


def test_prone_threshold_is_060():
    assert PRONE_T == 0.60


@pytest.mark.parametrize(
    "alloc,rec,passes,expected",
    [
        # Prone + observed -> True.
        (5_000_000, 0.80, 2, True),
        # Allocated + modeled-prone, no observed pass -> True.
        (1_000_000, 0.60, 0, True),
        # Allocated + observed pass, low recurrence -> True.
        (1_000_000, 0.10, 1, True),
        # Zero allocation -> False even if very prone + observed.
        (0, 0.95, 5, False),
        # Allocated but not prone and no observed pass -> False.
        (8_000_000, 0.30, 0, False),
        # Just under the threshold, no observed pass -> False.
        (8_000_000, 0.59, 0, False),
    ],
)
def test_warrants_investigation_truth_table(alloc, rec, passes, expected):
    assert _warrants(alloc, rec, passes) is expected


# ---------------------------------------------------------------------------
# the published artifact obeys the governance + cross-reference contract
# ---------------------------------------------------------------------------


@skip_absent
def test_published_aggregate_every_record_carries_exact_disclaimer():
    obj = json.loads(ACCT.read_text())
    assert obj["_meta"]["disclaimer"] == governance.DISCLAIMER
    assert obj["_meta"]["public_record_block"] == governance.PUBLIC_RECORD_BLOCK
    for key in ("by_province", "by_type", "by_tranche"):
        for i, row in enumerate(obj.get(key, [])):
            assert row.get("disclaimer") == governance.DISCLAIMER, f"{key}[{i}]"
    # assert_governed itself passes on the real file.
    governance.assert_governed(obj)


@skip_absent
def test_published_by_id_is_dict_not_list():
    obj = json.loads(BYID.read_text())
    assert isinstance(obj["projects"], dict)
    assert not isinstance(obj["projects"], list)
    assert len(obj["projects"]) > 0
    a_pid = next(iter(obj["projects"]))
    assert obj["projects"][a_pid]["disclaimer"] == governance.DISCLAIMER


@skip_absent
def test_published_warrants_flag_matches_the_conservative_rule():
    obj = json.loads(ACCT.read_text())
    for row in obj["by_province"]:
        alloc = row.get("allocation_php") or 0
        rec = float(row.get("recurrence_score") or 0.0)
        passes = int(row.get("observed_flood_passes") or 0)
        assert row["warrants_investigation"] == _warrants(alloc, rec, passes), (
            row.get("province")
        )


@skip_absent
def test_aggregate_file_has_no_named_project_keys():
    obj = json.loads(ACCT.read_text())
    forbidden = {"title", "name", "contractor", "project_name", "project_id"}
    for key in ("by_province", "by_type", "by_tranche"):
        for row in obj.get(key, []):
            assert not (forbidden & set(row.keys())), key
    assert not isinstance(obj.get("projects"), list)
