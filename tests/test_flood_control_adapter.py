"""Truth-table tests for FloodControlAdapter.

Mirrors the ghostwatch test_classifier.py truth-table pattern: enumerate the
flood-control membership decision tree, the status normalization variants, and
the geolocation_confidence fallback. No network, no mocking the unit under
test; the adapter's own static methods and parse() are exercised on tiny
in-memory frames.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from floodwatch_ph.adapters.flood_control import FloodControlAdapter


# ---------------------------------------------------------------------------
# _is_flood_control: the category/keyword membership decision tree
# ---------------------------------------------------------------------------


def test_exact_category_is_flood_control():
    # Rule 1: the canonical DPWH category is always in, case/space-insensitive.
    assert FloodControlAdapter._is_flood_control("Flood Control and Drainage", "") is True
    assert FloodControlAdapter._is_flood_control("  flood control and drainage ", "x") is True


def test_explicit_roads_category_never_reclassified_even_with_drainage_text():
    # Rule 3: an explicit non-flood category is never rescued by its
    # description, even when the description mentions drainage.
    assert (
        FloodControlAdapter._is_flood_control(
            "Roads", "construction of road with drainage and slope protection"
        )
        is False
    )


def test_explicit_bridge_category_dropped():
    assert (
        FloodControlAdapter._is_flood_control(
            "Bridges", "bridge with river control components"
        )
        is False
    )


def test_uninformative_category_rescued_by_flood_keyword():
    # Rule 2: a funding-shell category + a flood-control description is in.
    assert (
        FloodControlAdapter._is_flood_control(
            "GAA 2023", "construction of flood control structure along river"
        )
        is True
    )
    assert FloodControlAdapter._is_flood_control("", "drainage canal improvement") is True


def test_uninformative_category_without_flood_keyword_excluded():
    assert FloodControlAdapter._is_flood_control("Unprogrammed", "office renovation") is False
    assert FloodControlAdapter._is_flood_control("", "asphalt overlay works") is False


@pytest.mark.parametrize(
    "category,title,expected",
    [
        ("Flood Control and Drainage", "anything", True),
        ("FLOOD CONTROL AND DRAINAGE", "", True),
        ("Roads", "drainage and slope protection along the road", False),
        ("Buildings", "rainwater system in the building", False),
        ("Water Supply", "flood control dike", False),
        ("CSSP", "construction of dike and revetment", True),
        ("GAA 2024", "river control project", True),
        ("", "seawall and bank protection", True),
        ("Bridges", "river control bridge approach", False),
        ("Unprogrammed", "multi-storey car park", False),
    ],
)
def test_membership_truth_table(category, title, expected):
    assert FloodControlAdapter._is_flood_control(category, title) is expected


# ---------------------------------------------------------------------------
# status normalization (BaseAdapter.normalize_status via the adapter map)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Completed", "completed"),
        ("100% complete", "completed"),
        ("finished", "completed"),
        ("On-Going", "ongoing"),
        ("On-going", "ongoing"),
        ("in progress", "ongoing"),
        ("Under Construction", "ongoing"),
        ("Not Yet Started", "not_started"),
        ("not started", "not_started"),
        ("For Procurement", "not_started"),
        ("procurement", "not_started"),
        ("for implementation", "not_started"),
        ("pending", "not_started"),
        ("Terminated", "terminated"),
        ("some unknown value", "unknown"),
        (None, "unknown"),
    ],
)
def test_status_normalization(raw, expected):
    a = FloodControlAdapter()
    assert a.normalize_status(raw) == expected


def test_not_yet_started_does_not_leak_into_ongoing():
    """The raw DPWH value "Not Yet Started" lowercases to "not yet started",
    which contains the substring "started" (an ongoing variant). The status
    map orders not_started before ongoing so the negated form wins. Real
    "On-Going" must still map to ongoing (no not_started variant is a
    substring of "on-going") and "Completed" stays completed (checked
    first). This encodes the requirement, not the prior buggy behavior."""
    a = FloodControlAdapter()
    assert a.normalize_status("Not Yet Started") == "not_started"
    assert a.normalize_status("not started") == "not_started"
    assert a.normalize_status("For Procurement") == "not_started"
    # Real ongoing and completed values are unaffected by the reorder.
    assert a.normalize_status("On-Going") == "ongoing"
    assert a.normalize_status("Completed") == "completed"
    assert a.normalize_status("Terminated") == "terminated"


# ---------------------------------------------------------------------------
# geolocation_confidence: 1.0 with usable source coords, 0.6 fallback
# ---------------------------------------------------------------------------


def _parse_frame(rows: list[dict]) -> pd.DataFrame:
    """Run the real adapter.parse() against a tiny in-memory parquet."""
    import tempfile

    df = pd.DataFrame(rows)
    with tempfile.TemporaryDirectory() as d:
        fp = Path(d) / "tiny.parquet"
        df.to_parquet(fp, index=False)
        return FloodControlAdapter().parse(fp)


def test_geolocation_confidence_one_with_valid_ph_coords():
    out = _parse_frame(
        [
            {
                "contractId": "FC-1",
                "description": "construction of flood control dike",
                "category": "Flood Control and Drainage",
                "contractCost": 5_000_000,
                "status": "Completed",
                "latitude": 14.6,
                "longitude": 120.98,
                "region": "NCR",
                "province": "Metro Manila",
            }
        ]
    )
    assert len(out) == 1
    assert out.iloc[0]["geolocation_confidence"] == 1.0
    assert out.iloc[0]["status"] == "completed"


def test_geolocation_confidence_fallback_without_coords():
    out = _parse_frame(
        [
            {
                "contractId": "FC-2",
                "description": "drainage canal improvement",
                "category": "Flood Control and Drainage",
                "contractCost": 3_000_000,
                "status": "Ongoing",
                "latitude": None,
                "longitude": None,
                "region": "Region III",
                "province": "Bulacan",
            }
        ]
    )
    assert len(out) == 1
    assert out.iloc[0]["geolocation_confidence"] == 0.6


def test_out_of_ph_coords_drop_to_fallback_confidence():
    out = _parse_frame(
        [
            {
                "contractId": "FC-3",
                "description": "river control structure",
                "category": "Flood Control and Drainage",
                "contractCost": 9_000_000,
                "status": "Completed",
                "latitude": 51.5,  # London — outside the PH bbox
                "longitude": -0.12,
                "region": "X",
                "province": "Y",
            }
        ]
    )
    assert len(out) == 1
    assert out.iloc[0]["geolocation_confidence"] == 0.6


def test_explicit_road_row_excluded_from_parsed_subset():
    out = _parse_frame(
        [
            {
                "contractId": "RD-1",
                "description": "road widening with drainage",
                "category": "Roads",
                "contractCost": 8_000_000,
                "status": "Completed",
                "latitude": 14.6,
                "longitude": 121.0,
                "region": "NCR",
                "province": "Metro Manila",
            },
            {
                "contractId": "FC-9",
                "description": "flood control revetment",
                "category": "Flood Control and Drainage",
                "contractCost": 4_000_000,
                "status": "Completed",
                "latitude": 14.7,
                "longitude": 121.1,
                "region": "NCR",
                "province": "Metro Manila",
            },
        ]
    )
    ids = set(out["project_id"])
    assert "FC-9" in ids
    assert "RD-1" not in ids
