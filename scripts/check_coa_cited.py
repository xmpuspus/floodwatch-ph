"""CI gate: every COA-flagged row is cited, in-vocab, and accusation-free.

pipeline/_coa_flagged.json is the highest legal-sensitivity artifact in
FloodWatch. It quotes COA/Ombudsman findings on DPWH flood-control projects
from public sources only. This gate enforces the posture that makes that
defensible:

  - the file parses as JSON with the expected shape
  - every row carries a non-empty http(s) source_url
  - every row carries a source_published date
  - every row's coa_finding is in the controlled vocab
  - no banned word (ghost, fraud, thief, guilty, corrupt) appears anywhere
    in the file, including _meta

Any violation prints the offending row and exits non-zero. On success it
prints `[check_coa_cited] PASS: N rows, all cited`.

Exit 0 = clean, 1 = any violation found (every violation printed).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "pipeline" / "_coa_flagged.json"

FINDING_VOCAB = {"flagged_review", "site_mismatch", "pre_existing", "defective"}
BANNED_WORDS = ("ghost", "fraud", "thief", "guilty", "corrupt")
_RE_HTTP = re.compile(r"^https?://", re.IGNORECASE)


def main() -> int:
    if not TARGET.is_file():
        print(
            f"[check_coa_cited] FAIL: {TARGET.relative_to(REPO)} not found "
            "(run python3 pipeline/coa_extract.py first)",
            file=sys.stderr,
        )
        return 1

    raw = TARGET.read_text(encoding="utf-8")

    # Banned-word scan over the entire file text, _meta included. Done on the
    # raw bytes so a banned word smuggled into a URL or a key is still caught.
    low = raw.lower()
    banned_hits = [w for w in BANNED_WORDS if w in low]
    if banned_hits:
        print(
            "[check_coa_cited] FAIL: banned accusation word(s) in "
            f"{TARGET.relative_to(REPO)}: {', '.join(sorted(banned_hits))}",
            file=sys.stderr,
        )
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(
            f"[check_coa_cited] FAIL: {TARGET.relative_to(REPO)} does not "
            f"parse: {exc}",
            file=sys.stderr,
        )
        return 1

    if not isinstance(payload, dict) or "rows" not in payload:
        print(
            "[check_coa_cited] FAIL: top-level object missing 'rows'",
            file=sys.stderr,
        )
        return 1

    rows = payload["rows"]
    if not isinstance(rows, list) or not rows:
        print(
            "[check_coa_cited] FAIL: 'rows' is empty or not a list",
            file=sys.stderr,
        )
        return 1

    fails: list[str] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            fails.append(f"row {i}: not an object")
            continue
        url = row.get("source_url") or ""
        if not isinstance(url, str) or not _RE_HTTP.match(url):
            fails.append(f"row {i}: source_url missing or not http(s)")
        if not row.get("source_published"):
            fails.append(f"row {i}: source_published missing")
        if not row.get("source_org"):
            fails.append(f"row {i}: source_org missing")
        finding = row.get("coa_finding")
        if finding not in FINDING_VOCAB:
            fails.append(
                f"row {i}: coa_finding {finding!r} not in controlled vocab "
                f"{sorted(FINDING_VOCAB)}"
            )

    if fails:
        print(
            "[check_coa_cited] FAIL: uncited or out-of-vocab rows in "
            f"{TARGET.relative_to(REPO)}:",
            file=sys.stderr,
        )
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"[check_coa_cited] PASS: {len(rows)} rows, all cited")
    return 0


if __name__ == "__main__":
    sys.exit(main())
