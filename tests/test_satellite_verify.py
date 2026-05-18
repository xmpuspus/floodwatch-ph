"""Truth-table tests for the satellite built-change corroboration.

Mirrors test_flood_control_adapter.py: enumerate the VH-delta -> signal
classification bands, the pre/post window derivation, the in-PH + completed
eligibility filter, and the cache idempotency/merge contract. Pure and
network-free; the EE path is never exercised here. shapely/ee are import-
skipped so a CI runner without them still runs the deterministic logic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.satellite_verify import (
    STRONG_DB,
    WEAK_DB,
    _eligible_projects,
    _valid_ph_coord,
    _windows,
    classify_signal,
)


# ---------------------------------------------------------------------------
# classify_signal: the VH-delta -> built-change band decision
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "delta,expected",
    [
        (None, "none"),
        (float("nan"), "none"),
        (float("inf"), "none"),   # non-finite is rejected, not scored
        (-5.0, "none"),
        (0.0, "none"),
        (WEAK_DB - 0.01, "none"),
        (WEAK_DB, "weak"),
        (WEAK_DB + 0.5, "weak"),
        (STRONG_DB - 0.01, "weak"),
        (STRONG_DB, "strong"),
        (STRONG_DB + 4.0, "strong"),
    ],
)
def test_classify_signal_bands(delta, expected):
    assert classify_signal(delta) == expected


def test_negative_delta_never_reads_as_built():
    # A VH drop is never a built structure, however large.
    assert classify_signal(-10.0) == "none"
    assert classify_signal(-WEAK_DB) == "none"


# ---------------------------------------------------------------------------
# _valid_ph_coord: the in-Philippines coordinate gate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lat,lon,expected",
    [
        (14.6, 120.98, True),   # Metro Manila
        (4.4, 116.7, True),     # bbox corner (inclusive)
        (21.3, 126.7, True),    # bbox corner (inclusive)
        (None, 120.0, False),
        (14.0, None, False),
        (float("nan"), 120.0, False),
        (51.5, -0.12, False),   # London
        (0.0, 0.0, False),
        (22.0, 121.0, False),   # just north of the bbox
    ],
)
def test_valid_ph_coord(lat, lon, expected):
    assert _valid_ph_coord(lat, lon) is expected


# ---------------------------------------------------------------------------
# _windows: pre/post window derivation and ordering guards
# ---------------------------------------------------------------------------


def test_windows_well_ordered():
    w = _windows("2022-01-01", "2022-06-30")
    assert w is not None
    pre0, pre1, post0, post1 = w
    assert pre0 < pre1 <= "2022-01-01"
    assert "2022-06-30" <= post0 < post1
    # Pre window ends before start; post window begins after completion.
    assert pre1 < "2022-01-01"
    assert post0 > "2022-06-30"


def test_windows_rejects_completion_before_start():
    assert _windows("2022-06-30", "2022-01-01") is None


def test_windows_rejects_unusable_dates():
    assert _windows("not-a-date", "2022-01-01") is None
    assert _windows("2022-01-01", None) is None
    assert _windows(None, None) is None


# ---------------------------------------------------------------------------
# _eligible_projects: completed + in-PH + dated filter (no network)
# ---------------------------------------------------------------------------


def test_eligible_projects_filter(monkeypatch, tmp_path):
    """Drive _eligible_projects with a stubbed adapter so no parquet/network
    is touched; assert only the completed, in-PH, dated row survives."""
    import pandas as pd

    import pipeline.satellite_verify as sv

    rows = [
        # Completed, in PH, dated -> kept.
        {
            "project_id": "FC-OK",
            "status": "completed",
            "latitude": 14.6,
            "longitude": 120.98,
            "start_date": "2021-01-01",
            "completion_date": "2021-12-01",
        },
        # Ongoing -> dropped.
        {
            "project_id": "FC-ONGOING",
            "status": "ongoing",
            "latitude": 14.6,
            "longitude": 120.98,
            "start_date": "2021-01-01",
            "completion_date": "2021-12-01",
        },
        # Completed but no coords -> dropped.
        {
            "project_id": "FC-NOCOORD",
            "status": "completed",
            "latitude": None,
            "longitude": None,
            "start_date": "2021-01-01",
            "completion_date": "2021-12-01",
        },
        # Completed, coords outside PH -> dropped.
        {
            "project_id": "FC-LONDON",
            "status": "completed",
            "latitude": 51.5,
            "longitude": -0.12,
            "start_date": "2021-01-01",
            "completion_date": "2021-12-01",
        },
        # Completed, in PH, but completion before start -> dropped.
        {
            "project_id": "FC-BADDATES",
            "status": "completed",
            "latitude": 14.6,
            "longitude": 120.98,
            "start_date": "2021-12-01",
            "completion_date": "2021-01-01",
        },
    ]

    class _StubAdapter:
        def fetch(self, _output_dir):
            return tmp_path / "snapshot.parquet"

        def parse(self, _snapshot):
            return pd.DataFrame(rows)

    monkeypatch.setattr(sv, "FloodControlAdapter", lambda: _StubAdapter())

    out = _eligible_projects(limit=None, max_ids=None)
    ids = [p["id"] for p in out]
    assert ids == ["FC-OK"]
    assert out[0]["lat"] == 14.6 and out[0]["lon"] == 120.98
    assert len(out[0]["windows"]) == 4


# ---------------------------------------------------------------------------
# cache idempotency / merge contract
# ---------------------------------------------------------------------------


def test_write_cache_is_sorted_and_byte_identical(monkeypatch, tmp_path):
    import pipeline.satellite_verify as sv

    cache_path = tmp_path / "_satellite_verify_cache.json"
    monkeypatch.setattr(sv, "CACHE", cache_path)

    by_id = {
        "FC-B": {
            "satellite_checked": True,
            "built_change_signal": "weak",
            "vh_delta_db": 2.123456,
        },
        "FC-A": {
            "satellite_checked": True,
            "built_change_signal": "none",
            "vh_delta_db": None,
        },
    }
    sv._write_cache(by_id, n_checked=2, ee_ran=True)
    first = cache_path.read_bytes()
    doc = json.loads(first)

    # Keys are sorted and the float is rounded to 3 dp.
    assert list(doc["by_id"].keys()) == ["FC-A", "FC-B"]
    assert doc["by_id"]["FC-B"]["vh_delta_db"] == 2.123
    assert doc["by_id"]["FC-A"]["vh_delta_db"] is None
    assert doc["_meta"]["disclaimer"].startswith("Indicative corroboration")
    assert doc["_meta"]["ee_collection"] == "COPERNICUS/S1_GRD"

    # A second write with the same ids reproduces identical by_id ordering and
    # values (only the generated_utc stamp may differ -> compare by_id only).
    sv._write_cache(by_id, n_checked=2, ee_ran=True)
    second = json.loads(cache_path.read_bytes())
    assert second["by_id"] == doc["by_id"]


def test_merge_preserves_prior_ids():
    """The merge contract: new ids extend, existing ids are not re-checked.

    This mirrors run()'s skip set without invoking EE: a prior cache id stays
    untouched and a new id is appended.
    """
    prior = {"FC-OLD": {"satellite_checked": True, "built_change_signal": "strong",
                         "vh_delta_db": 4.0}}
    by_id = dict(prior)
    already = set(by_id)

    candidate_ids = ["FC-OLD", "FC-NEW"]
    todo = [i for i in candidate_ids if i not in already]
    assert todo == ["FC-NEW"]

    by_id["FC-NEW"] = {
        "satellite_checked": True,
        "built_change_signal": "none",
        "vh_delta_db": 0.2,
    }
    assert by_id["FC-OLD"] == prior["FC-OLD"]
    assert set(by_id) == {"FC-OLD", "FC-NEW"}


def test_ee_and_shapely_optional_for_network_path():
    # The deterministic logic above needs neither; the network path does.
    pytest.importorskip("ee")
    pytest.importorskip("shapely")
    import pipeline.satellite_verify as sv

    assert hasattr(sv, "_robust_mean_vh")
    assert Path(sv.__file__).name == "satellite_verify.py"
