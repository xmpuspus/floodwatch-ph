"""CI gate: permanent-water masking integrity (locked decision 2).

For every site/public/data/flood_*.geojson:
  - If _meta.placeholder is true: skip with a note (placeholder files are
    expected before the pipeline has run).
  - Otherwise: assert _meta.permanent_water_masked is True.

The product reports FLOOD, not rivers/lakes/sea. Every published flood GeoJSON
must carry this flag, set by event/flood_extent.py after applying the JRC +
MERIT Hydro mask.

Exit code 0 = all real files pass (or no real files exist yet), 1 = any
real flood file is missing the flag.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "site" / "public" / "data"


def check_one(path: Path) -> tuple[str, str]:
    """Return (status, message) where status is 'pass', 'skip', or 'fail'."""
    try:
        gj = json.loads(path.read_text())
    except Exception as exc:
        return "fail", f"cannot parse: {exc}"

    meta = gj.get("_meta", {})

    if meta.get("placeholder") is True:
        return "skip", "placeholder=true"

    masked = meta.get("permanent_water_masked")
    if masked is not True:
        return "fail", f"_meta.permanent_water_masked is {masked!r}, expected true"

    return "pass", f"permanent_water_masked=true"


def main() -> int:
    flood_files = sorted(DATA_DIR.glob("flood_*.geojson"))

    if not flood_files:
        print(
            f"[check_permanent_water] no flood_*.geojson files found in {DATA_DIR} "
            "(no real data yet — pass)"
        )
        return 0

    fails = 0
    for path in flood_files:
        status, msg = check_one(path)
        if status == "pass":
            print(f"[check_permanent_water] OK: {path.name} — {msg}")
        elif status == "skip":
            print(f"[check_permanent_water] SKIP: {path.name} — {msg}")
        else:
            print(
                f"[check_permanent_water] FAIL: {path.name} — {msg}",
                file=sys.stderr,
            )
            fails += 1

    if fails:
        print(
            f"\n[check_permanent_water] {fails} file(s) failed the permanent-water mask gate.",
            file=sys.stderr,
        )
        print(
            "  Every published flood GeoJSON must have _meta.permanent_water_masked == true.",
            file=sys.stderr,
        )
        print(
            "  This flag is set by event/flood_extent.py after applying the JRC + MERIT Hydro mask.",
            file=sys.stderr,
        )
    else:
        n_checked = sum(1 for p in flood_files if check_one(p)[0] == "pass")
        n_skipped = sum(1 for p in flood_files if check_one(p)[0] == "skip")
        print(
            f"\n[check_permanent_water] PASS: {n_checked} file(s) verified, "
            f"{n_skipped} placeholder(s) skipped."
        )

    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
