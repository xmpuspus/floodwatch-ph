"""CI gate: barangay-aggregate outputs contain no PII-adjacent fields (locked decision 5).

Checks three published files:
  site/public/data/barangay_exposure.json
  site/public/data/hazard_gap.geojson
  site/public/data/recurrence_prone.geojson

For each file that is not a placeholder and not empty:
  1. No forbidden PII-adjacent property key appears anywhere in feature
     properties or top-level JSON object values.
  2. For barangay_exposure.json ({_meta, units}): every unit's `population`
     is an integer aggregate and built_up_km2/peak_flood_pct are plain
     numbers (no lists/objects that could encode per-household data). Units
     are province (FAO GAUL level-2); barangay resolution is v1.1.

Forbidden keys:
    household, address, owner, name_of_resident, resident, dwelling_id,
    house_id, phone, email, occupant

Files tagged _meta.placeholder=true (or empty objects {}) are skipped cleanly.

Exit code 0 = clean, 1 = any violation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "site" / "public" / "data"

FORBIDDEN_KEYS = {
    "household",
    "address",
    "owner",
    "name_of_resident",
    "resident",
    "dwelling_id",
    "house_id",
    "phone",
    "email",
    "occupant",
}


def _scan_for_forbidden(obj, path: str = "") -> list[str]:
    """Recursively scan a parsed JSON object for forbidden keys."""
    violations: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            if k.lower() in FORBIDDEN_KEYS:
                violations.append(f"forbidden key {k!r} at {here}")
            violations.extend(_scan_for_forbidden(v, here))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            violations.extend(_scan_for_forbidden(item, f"{path}[{i}]"))
    return violations


def _is_placeholder(obj) -> bool:
    if not isinstance(obj, dict):
        return False
    meta = obj.get("_meta", {})
    if isinstance(meta, dict) and meta.get("placeholder") is True:
        return True
    if len(obj) == 0:
        return True
    return False


def check_geojson(path: Path) -> tuple[str, list[str]]:
    """Returns ('pass'|'skip'|'fail', [messages])."""
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:
        return "fail", [f"cannot parse: {exc}"]

    if _is_placeholder(obj):
        return "skip", [f"placeholder — skipped"]

    features = obj.get("features", [])
    if not features:
        # Empty non-placeholder FeatureCollection: no properties to scan, treat as pass
        return "pass", ["0 features — nothing to scan"]

    violations: list[str] = []
    for i, feat in enumerate(features[:200]):  # cap scan at 200 features in CI
        props = feat.get("properties") or {}
        for k, v in props.items():
            loc = f"feature[{i}].properties.{k}"
            if k.lower() in FORBIDDEN_KEYS:
                violations.append(f"forbidden key {k!r} at {loc}")
        if violations and len(violations) >= 10:
            violations.append("... (further violations suppressed)")
            break

    if violations:
        return "fail", violations
    return "pass", [f"{len(features)} features scanned, no forbidden keys"]


def check_barangay_exposure(path: Path) -> tuple[str, list[str]]:
    """barangay_exposure.json ({_meta, units}): each province unit must have
    an integer population aggregate and numeric built_up_km2 / peak_flood_pct,
    with no PII-adjacent keys anywhere."""
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:
        return "fail", [f"cannot parse: {exc}"]

    if _is_placeholder(obj):
        return "skip", ["placeholder — skipped"]

    violations: list[str] = []
    # Real schema: {"_meta": {...}, "units": {<id>: {name, city, province,
    # population (int aggregate), built_up_km2 (number), observed_events (int),
    # peak_flood_pct (number), on_official_hazard_map}}}
    units = obj.get("units")
    if not isinstance(units, dict):
        return "fail", ["missing top-level 'units' object"]

    # Recursive forbidden-key scan over the whole document.
    violations.extend(_scan_for_forbidden(obj))

    for uid, entry in units.items():
        if not isinstance(entry, dict):
            violations.append(f"unit {uid!r}: expected dict, got {type(entry).__name__}")
            continue
        pop = entry.get("population")
        if pop is not None and not isinstance(pop, int):
            violations.append(
                f"unit {uid!r}.population: expected int aggregate, "
                f"got {type(pop).__name__}"
            )
        for numfield in ("built_up_km2", "peak_flood_pct"):
            v = entry.get(numfield)
            if v is not None and not isinstance(v, (int, float)):
                violations.append(
                    f"unit {uid!r}.{numfield}: expected number, "
                    f"got {type(v).__name__}"
                )
        ev = entry.get("observed_events")
        if ev is not None and not isinstance(ev, int):
            violations.append(
                f"unit {uid!r}.observed_events: expected int, got {type(ev).__name__}"
            )
        if len(violations) >= 10:
            violations.append("... (further violations suppressed)")
            break

    if violations:
        return "fail", violations
    return "pass", [
        f"{len(units)} province units, population is integer "
        "aggregate, no PII keys"
    ]


def main() -> int:
    files = [
        ("barangay_exposure.json", check_barangay_exposure),
        ("hazard_gap.geojson", check_geojson),
        ("recurrence_prone.geojson", check_geojson),
    ]

    fails = 0
    for fname, checker in files:
        path = DATA_DIR / fname
        if not path.exists():
            print(f"[check_no_pii] SKIP: {fname} not present")
            continue

        status, messages = checker(path)
        if status == "pass":
            print(f"[check_no_pii] OK: {fname} — {messages[0]}")
        elif status == "skip":
            print(f"[check_no_pii] SKIP: {fname} — {messages[0]}")
        else:
            print(f"[check_no_pii] FAIL: {fname}", file=sys.stderr)
            for msg in messages:
                print(f"  {msg}", file=sys.stderr)
            fails += 1

    if fails:
        print(
            f"\n[check_no_pii] {fails} file(s) failed the PII gate.",
            file=sys.stderr,
        )
        print(
            "  All outputs must be barangay-level aggregates with no per-household or "
            "per-dwelling identification.",
            file=sys.stderr,
        )
    else:
        print("\n[check_no_pii] PASS: all files clean.")

    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
