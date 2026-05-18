"""Truth-table tests for the COA-flagged curated extract.

Mirrors test_flood_control_adapter.py: enumerate the validation decision
tree (controlled vocab, citation requirement, banned-word scan) and the
description_key normalization, all network-free on in-memory rows. The
curated table in pipeline/coa_extract.py is exercised through build_rows()
and the public helpers; nothing is mocked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

coa = pytest.importorskip("pipeline.coa_extract")


# ---------------------------------------------------------------------------
# description_key: normalization is stable, idempotent, filler-stripped
# ---------------------------------------------------------------------------


def test_description_key_lowercases_and_strips_punctuation():
    assert (
        coa.description_key("Angat River Control Structure, Sipat!")
        == "angat_river_control_structure_sipat"
    )


def test_description_key_drops_generic_filler_tokens():
    # "Barangay", "Bocaue" kept (place token), "the/of/along/at" dropped.
    assert (
        coa.description_key("Slope protection along the Bocaue River at Brgy Bambang")
        == "slope_protection_bocaue_river_bambang"
    )


def test_description_key_is_idempotent():
    once = coa.description_key("Riverbank Protection Structure Package A, Bulihan")
    assert coa.description_key(once) == once


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Bocaue River slope protection, Barangay Turo", "bocaue_river_slope_protection_turo"),
        ("  Multiple   Spaces  ", "multiple_spaces"),
        ("City of Malolos Caingin", "malolos_caingin"),
        ("Item 1 / Item 2", "1_2"),
    ],
)
def test_description_key_truth_table(raw, expected):
    assert coa.description_key(raw) == expected


# ---------------------------------------------------------------------------
# _row_valid: controlled vocab, citation, banned-word decision tree
# ---------------------------------------------------------------------------


def _good_row() -> dict:
    return {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Bocaue River slope protection, Barangay Bambang",
        "coa_finding": "site_mismatch",
        "source_url": "https://example.org/coa-report",
        "source_org": "COA",
        "source_published": "2025-09-18",
    }


def test_row_valid_accepts_a_well_formed_row():
    assert coa._row_valid(_good_row()) is None


@pytest.mark.parametrize("finding", sorted(coa.FINDING_VOCAB))
def test_every_controlled_vocab_value_is_accepted(finding):
    row = _good_row()
    row["coa_finding"] = finding
    assert coa._row_valid(row) is None


@pytest.mark.parametrize(
    "bad", ["ghost", "fraud", "Ghost Project", "valid", "", None, "mismatch"]
)
def test_out_of_vocab_finding_is_rejected(bad):
    row = _good_row()
    row["coa_finding"] = bad
    assert coa._row_valid(row) is not None


@pytest.mark.parametrize(
    "url", ["", None, "ftp://x/y", "example.org/report", "www.example.org"]
)
def test_non_http_source_url_is_rejected(url):
    row = _good_row()
    row["source_url"] = url
    assert coa._row_valid(row) is not None


def test_missing_source_published_is_rejected():
    row = _good_row()
    row["source_published"] = ""
    assert coa._row_valid(row) is not None


def test_missing_source_org_is_rejected():
    row = _good_row()
    row["source_org"] = ""
    assert coa._row_valid(row) is not None


@pytest.mark.parametrize("word", coa.BANNED_WORDS)
def test_banned_word_anywhere_in_row_is_rejected(word):
    row = _good_row()
    row["description"] = f"a {word} project description"
    assert coa._row_valid(row) is not None


def test_banned_word_in_source_url_is_rejected():
    row = _good_row()
    row["source_url"] = "https://example.org/ghost-projects"
    assert coa._row_valid(row) is not None


# ---------------------------------------------------------------------------
# build_rows: the curated table itself is defensible end to end
# ---------------------------------------------------------------------------


def test_build_rows_emits_only_clean_in_vocab_cited_rows():
    rows = coa.build_rows()
    assert rows, "curated table produced zero rows"
    for r in rows:
        assert r["coa_finding"] in coa.FINDING_VOCAB
        assert r["source_url"].startswith(("http://", "https://"))
        assert r["source_published"]
        assert r["source_org"]
        assert r["description_key"] == coa.description_key(r["description_key"])
        blob = json.dumps(r, ensure_ascii=False).lower()
        for w in coa.BANNED_WORDS:
            assert w not in blob


def test_curated_rows_carry_no_invented_contract_ids():
    # Every curated row uses province + description_key for the fuzzy join;
    # contract_id stays null unless a real DPWH id is known. None are.
    for r in coa.build_rows():
        assert r["contract_id"] is None
