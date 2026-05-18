"""v1.5 temporal + confidence field tests.

Network-free. The adapter's date coercion is the highest-risk new piece (a
missing date32 arrives from pandas as a truthy NaN float, which silently
broke the first temporal join), so it gets explicit cases. The parse()
contract check runs against the committed offline parquet cache when present;
it import-skips cleanly where the cache or pandas/pyarrow are absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from floodwatch_ph.adapters.flood_control import FloodControlAdapter

CACHE = Path(__file__).resolve().parents[1] / "pipeline" / "_dpwh_flood_control_cache.parquet"


@pytest.mark.parametrize(
    "val,expected",
    [
        ("2024-07-30", "2024-07-30"),
        ("2024-07-30T00:00:00", "2024-07-30"),
        ("", None),
        ("nan", None),
        ("NaT", None),
        ("not-a-date", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_maybe_date(val, expected):
    assert FloodControlAdapter._maybe_date(val) == expected


def test_maybe_date_on_date_object():
    import datetime

    assert FloodControlAdapter._maybe_date(datetime.date(2022, 2, 27)) == "2022-02-27"


def test_post_completion_is_chronological_string_compare():
    # The temporal join relies on ISO YYYY-MM-DD sorting lexicographically.
    passes = ["2024-07-10", "2024-07-22", "2024-07-30", "2024-08-03"]
    completion = "2024-07-25"
    after = [d for d in passes if d > completion]
    assert after == ["2024-07-30", "2024-08-03"]


def test_parse_emits_temporal_columns():
    pytest.importorskip("pyarrow")
    if not CACHE.exists():
        pytest.skip("offline parquet cache not present")
    df = FloodControlAdapter().parse(CACHE)
    for col in ("completion_date", "start_date", "infra_year"):
        assert col in df.columns, f"parse() must emit {col}"
    # completion_date is either an ISO string or NA-like; never a stray float
    # that would pass a truthiness guard.
    sample = df["completion_date"].dropna().head(20).tolist()
    for v in sample:
        assert isinstance(v, str) and len(v) == 10 and v[4] == "-"
