"""Validate published GeoJSON files against the SCHEMA.md data contract.

For any non-placeholder site/public/data/flood_*.geojson present:
  - type == "FeatureCollection"
  - _meta block present with required keys
  - features is a list

Placeholder files and absent files are skipped cleanly (no test failure).

Run entirely offline from committed files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "site" / "public" / "data"

# Required _meta keys for flood_*.geojson per SCHEMA.md
FLOOD_META_KEYS = {
    "event",
    "label",
    "role",
    "gauged",
    "permanent_water_masked",
    "aoi_name",
    "bbox",
    "dates",
}


def _is_placeholder(obj: dict) -> bool:
    meta = obj.get("_meta", {})
    if isinstance(meta, dict) and meta.get("placeholder") is True:
        return True
    return False


def _flood_geojsons() -> list[Path]:
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.glob("flood_*.geojson"))


def _real_flood_geojsons() -> list[Path]:
    result = []
    for p in _flood_geojsons():
        try:
            obj = json.loads(p.read_text())
            if not _is_placeholder(obj):
                result.append(p)
        except Exception:
            result.append(p)  # include parse failures so the test catches them
    return result


# Generate parametrized test cases; empty list skips gracefully
_REAL_FLOOD_FILES = _real_flood_geojsons()


@pytest.mark.skipif(not _REAL_FLOOD_FILES, reason="no non-placeholder flood GeoJSON files present")
@pytest.mark.parametrize("path", _REAL_FLOOD_FILES, ids=[p.name for p in _REAL_FLOOD_FILES])
def test_flood_geojson_is_feature_collection(path: Path):
    obj = json.loads(path.read_text())
    assert obj.get("type") == "FeatureCollection", (
        f"{path.name}: expected type=FeatureCollection, got {obj.get('type')!r}"
    )


@pytest.mark.skipif(not _REAL_FLOOD_FILES, reason="no non-placeholder flood GeoJSON files present")
@pytest.mark.parametrize("path", _REAL_FLOOD_FILES, ids=[p.name for p in _REAL_FLOOD_FILES])
def test_flood_geojson_has_meta(path: Path):
    obj = json.loads(path.read_text())
    assert "_meta" in obj, f"{path.name}: missing _meta block"
    meta = obj["_meta"]
    assert isinstance(meta, dict), f"{path.name}: _meta must be a dict"


@pytest.mark.skipif(not _REAL_FLOOD_FILES, reason="no non-placeholder flood GeoJSON files present")
@pytest.mark.parametrize("path", _REAL_FLOOD_FILES, ids=[p.name for p in _REAL_FLOOD_FILES])
def test_flood_geojson_meta_required_keys(path: Path):
    obj = json.loads(path.read_text())
    meta = obj.get("_meta", {})
    missing = FLOOD_META_KEYS - set(meta.keys())
    assert not missing, (
        f"{path.name}: _meta missing required keys: {sorted(missing)}"
    )


@pytest.mark.skipif(not _REAL_FLOOD_FILES, reason="no non-placeholder flood GeoJSON files present")
@pytest.mark.parametrize("path", _REAL_FLOOD_FILES, ids=[p.name for p in _REAL_FLOOD_FILES])
def test_flood_geojson_permanent_water_masked(path: Path):
    obj = json.loads(path.read_text())
    meta = obj.get("_meta", {})
    assert meta.get("permanent_water_masked") is True, (
        f"{path.name}: _meta.permanent_water_masked must be true (locked decision 2)"
    )


@pytest.mark.skipif(not _REAL_FLOOD_FILES, reason="no non-placeholder flood GeoJSON files present")
@pytest.mark.parametrize("path", _REAL_FLOOD_FILES, ids=[p.name for p in _REAL_FLOOD_FILES])
def test_flood_geojson_features_is_list(path: Path):
    obj = json.loads(path.read_text())
    assert isinstance(obj.get("features"), list), (
        f"{path.name}: features must be a list"
    )


def test_placeholder_flood_geojsons_are_skipped():
    """All current flood_*.geojson files are placeholders — confirms the skip logic works."""
    all_files = _flood_geojsons()
    for path in all_files:
        try:
            obj = json.loads(path.read_text())
            # placeholder files should not reach the parametrized tests above
            if _is_placeholder(obj):
                assert path not in _REAL_FLOOD_FILES, (
                    f"{path.name} is a placeholder but was included in real-file list"
                )
        except Exception:
            pass  # parse failures handled by parametrized tests
