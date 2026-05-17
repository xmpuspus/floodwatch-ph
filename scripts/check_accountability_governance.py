"""CI gate: the flood-control accountability artifacts are correctly governed.

The disclaimer is un-strippable because it is baked into the published JSON and
this gate fails the build if it is missing or altered. Mirrors ghostwatch's
disclaimer-presence test, adapted to a static-site data layer.

Checks site/public/data/flood_control_accountability.json and
flood_control_by_id.json:

  1. _meta.disclaimer equals floodwatch_ph.accountability.governance.DISCLAIMER
     byte-for-byte, and _meta.public_record_block equals PUBLIC_RECORD_BLOCK.
  2. Every aggregation record (by_province / by_type / by_tranche) carries the
     same exact disclaimer; every by-id project record carries it too.
  3. The aggregate file is aggregation-only: no project-name / contractor /
     title key at by_province / by_type / by_tranche record level, and no
     top-level array of named flagged projects ("list all flagged" shape).
  4. The by-id map is a dict keyed by project id, never a list.

Files absent  -> PASS (Phase-1-only builds still pass).
Files present but governance broken -> FAIL (exit 1).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "site" / "public" / "data"

# Keys that would leak a named project into an aggregate. Aggregates are
# region / type / budget-tranche only; a name here breaks the ghostwatch
# aggregation-only contract.
FORBIDDEN_AGG_KEYS = {"title", "name", "contractor", "project_name", "project_id"}

AGG_KEYS = ("by_province", "by_type", "by_tranche")


def _load_disclaimer_constants() -> tuple[str, str]:
    """Import the canonical constants. The gate pins against these, so a
    tampered string in the JSON cannot pass by also editing the JSON."""
    sys.path.insert(0, str(REPO))
    from floodwatch_ph.accountability import governance

    return governance.DISCLAIMER, governance.PUBLIC_RECORD_BLOCK


def _check_aggregate(path: Path, disclaimer: str, public_block: str) -> list[str]:
    """Return a list of violation strings for the aggregate file (empty = ok)."""
    v: list[str] = []
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return [f"cannot parse: {exc}"]

    if not isinstance(obj, dict):
        return ["top-level JSON is not an object"]

    meta = obj.get("_meta")
    if not isinstance(meta, dict):
        v.append("missing _meta object")
    else:
        if meta.get("disclaimer") != disclaimer:
            v.append("_meta.disclaimer missing or altered vs governance.DISCLAIMER")
        if meta.get("public_record_block") != public_block:
            v.append(
                "_meta.public_record_block missing or altered vs "
                "governance.PUBLIC_RECORD_BLOCK"
            )

    # No top-level array of named flagged projects (the "list all flagged"
    # shape). Aggregates are dicts/lists of aggregate rows only.
    if isinstance(obj.get("projects"), list):
        v.append("'projects' is a list (list-all-flagged shape forbidden here)")
    for k, val in obj.items():
        if k in AGG_KEYS or k == "_meta":
            continue
        if isinstance(val, list) and val and isinstance(val[0], dict):
            if FORBIDDEN_AGG_KEYS & set(val[0].keys()):
                v.append(
                    f"top-level array {k!r} carries a named-project key "
                    f"(forbidden in the aggregate file)"
                )

    for key in AGG_KEYS:
        rows = obj.get(key)
        if rows is None:
            continue
        if not isinstance(rows, list):
            v.append(f"{key} must be a list of aggregate rows")
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                v.append(f"{key}[{i}] is not an object")
                continue
            leaked = FORBIDDEN_AGG_KEYS & set(row.keys())
            if leaked:
                v.append(f"{key}[{i}] leaks named-project key(s): {sorted(leaked)}")
            if row.get("disclaimer") != disclaimer:
                v.append(f"{key}[{i}].disclaimer missing or altered")
            # Stop the spew but keep enough to act on.
            if len(v) >= 12:
                v.append("... (further violations suppressed)")
                return v
    return v


def _check_by_id(path: Path, disclaimer: str, public_block: str) -> list[str]:
    """Return a list of violation strings for the by-id map (empty = ok)."""
    v: list[str] = []
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return [f"cannot parse: {exc}"]

    if not isinstance(obj, dict):
        return ["top-level JSON is not an object"]

    meta = obj.get("_meta")
    if not isinstance(meta, dict):
        v.append("missing _meta object")
    else:
        if meta.get("disclaimer") != disclaimer:
            v.append("_meta.disclaimer missing or altered vs governance.DISCLAIMER")
        if meta.get("public_record_block") != public_block:
            v.append("_meta.public_record_block missing or altered")

    projects = obj.get("projects")
    if projects is None:
        v.append("missing 'projects' map")
    elif not isinstance(projects, dict):
        v.append("'projects' must be a dict keyed by id, not a list")
    else:
        checked = 0
        for pid, rec in projects.items():
            if not isinstance(rec, dict):
                v.append(f"projects[{pid}] is not an object")
            elif rec.get("disclaimer") != disclaimer:
                v.append(f"projects[{pid}].disclaimer missing or altered")
            checked += 1
            if len(v) >= 12:
                v.append("... (further violations suppressed)")
                break
        if checked == 0:
            v.append("'projects' map is empty")
    return v


def main() -> int:
    agg_path = DATA_DIR / "flood_control_accountability.json"
    byid_path = DATA_DIR / "flood_control_by_id.json"

    if not agg_path.exists() and not byid_path.exists():
        print(
            "[check_accountability_governance] SKIP: neither accountability "
            "file present (Phase-1-only build) — PASS"
        )
        return 0

    disclaimer, public_block = _load_disclaimer_constants()
    fails = 0

    if agg_path.exists():
        problems = _check_aggregate(agg_path, disclaimer, public_block)
        if problems:
            print(
                "[check_accountability_governance] FAIL: "
                "flood_control_accountability.json",
                file=sys.stderr,
            )
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            fails += 1
        else:
            print(
                "[check_accountability_governance] OK: "
                "flood_control_accountability.json — disclaimer + public-record "
                "block intact, aggregation-only, every record governed"
            )
    else:
        print(
            "[check_accountability_governance] SKIP: "
            "flood_control_accountability.json absent"
        )

    if byid_path.exists():
        problems = _check_by_id(byid_path, disclaimer, public_block)
        if problems:
            print(
                "[check_accountability_governance] FAIL: "
                "flood_control_by_id.json",
                file=sys.stderr,
            )
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            fails += 1
        else:
            print(
                "[check_accountability_governance] OK: "
                "flood_control_by_id.json — dict keyed by id, every record "
                "carries the exact disclaimer"
            )
    else:
        print("[check_accountability_governance] SKIP: flood_control_by_id.json absent")

    if fails:
        print(
            f"\n[check_accountability_governance] {fails} file(s) failed the "
            "governance gate. The disclaimer is a legal gate; the build must "
            "not ship without it.",
            file=sys.stderr,
        )
        return 1
    print("\n[check_accountability_governance] PASS: accountability surface governed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
