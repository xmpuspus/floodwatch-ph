"""CI gate: the "337 collision" can never be conflated in shipped copy.

FloodWatch publishes uncharted_count = "337" = modeled-prone, under-observed
*provinces* (its own pipeline number). COA separately reported "337 confirmed
ghosts" — an unrelated figure FloodWatch does not ingest. The two must never
appear adjacent or conflatable in any shipped copy, tile, chart, or data
artifact.

FAIL if the token 337 co-occurs with any of {ghost, confirmed ghost, ghost
project, non-existent} on the same line, within 240 characters, or in the same
markdown/DOM block, anywhere in shipped copy:
  - site/src/**            (every text-bearing source file)
  - site/public/data/*.json
  - docs/**                rendered/published copy

The collision is *defined* in the governance and planning docs (00-master.md,
recenter-plan.md, the wave briefs, this script, the WBD/WA status notes, the
ghostwatch study). Those documents must state the rule, so they are an explicit
allowlist — they describe the collision, they do not ship it. Everything else
is scanned strictly.

Exit 0 = clean, 1 = any conflation found (every location printed).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Docs that DEFINE the collision rule. They must talk about "337" and "ghost"
# in the same breath; that is their job. They are not shipped site copy.
ALLOWLIST = {
    REPO / "docs" / "research" / "recenter-plan.md",
    REPO / "docs" / "research" / "ghostwatch-study.md",
    REPO / "docs" / "research" / "flood-control-data-feasibility.md",
    REPO / "docs" / "plans" / "recenter" / "00-master.md",
    REPO / "docs" / "plans" / "recenter" / "10-wb-data-brief.md",
    REPO / "docs" / "plans" / "recenter" / "20-wa-site-brief.md",
    REPO / "docs" / "plans" / "recenter" / "30-wbi-integrity-brief.md",
    REPO / "docs" / "plans" / "recenter" / "_wbd-status.md",
    REPO / "docs" / "plans" / "recenter" / "_wa-status.md",
    REPO / "docs" / "plans" / "recenter" / "_wbi-status.md",
    # Phase-2 verification report: its 337/ghost mentions are the gate
    # itself being described and verified ("337 never adjacent to
    # ghost/confirmed", "check_337_collision.py exit 0"), not a conflation
    # in shipped copy. Same class as the wave briefs / 00-master above.
    REPO / "docs" / "plans" / "recenter" / "_agentF-report.md",
}

# Word-boundaried so a place name like the Baguio "Holy Ghost" barangay
# (it appears verbatim in DPWH project titles) is not a false collision.
# "confirmed ghost", "ghost project", "ghost projects" are the COA-conflation
# phrasings we actually guard against; a lone "ghost" inside a hyphenated
# place name ("holyghost") is excluded by the boundary.
_RE_GHOST = re.compile(
    r"\b(?:ghost\s+projects?|confirmed\s+ghosts?|ghosts?\b|"
    r"non[-\s]?existent)\b"
)
WINDOW = 240
TEXT_EXT = {".astro", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".mdx",
            ".html", ".svelte", ".vue", ".txt"}

_RE_337 = re.compile(r"(?<!\d)337(?!\d)")


def _iter_targets() -> list[Path]:
    targets: list[Path] = []
    src = REPO / "site" / "src"
    if src.is_dir():
        targets += [p for p in src.rglob("*") if p.is_file() and p.suffix in TEXT_EXT]
    data = REPO / "site" / "public" / "data"
    if data.is_dir():
        targets += sorted(data.glob("*.json"))
    docs = REPO / "docs"
    if docs.is_dir():
        targets += [p for p in docs.rglob("*") if p.is_file() and p.suffix in TEXT_EXT]
    return targets


def _blocks(text: str, suffix: str) -> list[str]:
    """Split into blocks. Markdown: blank-line-separated paragraphs. Other:
    the whole file (the sliding-window check below catches in-file proximity)."""
    if suffix in (".md", ".mdx"):
        return re.split(r"\n[ \t]*\n", text)
    return [text]


def _has_collision(segment: str) -> str | None:
    """Return a short reason if 337 and a ghost token co-occur within WINDOW
    chars of each other in this segment, else None."""
    if "337" not in segment:
        return None
    low = segment.lower()
    if not _RE_GHOST.search(low):
        return None
    ghost_spans = [m.span() for m in _RE_GHOST.finditer(low)]
    for m in _RE_337.finditer(segment):
        i = m.start()
        for gs, ge in ghost_spans:
            # Closest edge-to-edge distance between the 337 token and a
            # ghost token.
            if gs > i:
                dist = gs - (i + 3)
            else:
                dist = i - ge
            if 0 <= dist <= WINDOW or (gs <= i <= ge):
                frag = low[gs:ge]
                return f'"337" within {WINDOW} chars of {frag!r}'
    return None


def main() -> int:
    fails: list[str] = []
    scanned = 0

    for path in _iter_targets():
        if path.resolve() in {p.resolve() for p in ALLOWLIST}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN: cannot read {path}: {exc}", file=sys.stderr)
            continue
        scanned += 1
        rel = path.relative_to(REPO)

        lines = text.splitlines()
        # The "same line" rule only means something for line-oriented human
        # copy. A minified single-line JSON has one "line" = the whole file,
        # where an unrelated station chainage and a place name 30k records
        # apart are not a conflation; the 240-char window below is the honest
        # proximity test there.
        single_line_blob = len(lines) <= 1 and len(text) > 2000
        if not single_line_blob:
            for ln, line in enumerate(lines, 1):
                low = line.lower()
                if _RE_337.search(line) and _RE_GHOST.search(low):
                    fails.append(
                        f"{rel}:{ln} — 337 and a ghost token on the same line"
                    )

        # Same block / within 240 chars.
        for bi, block in enumerate(_blocks(text, path.suffix)):
            reason = _has_collision(block)
            if reason:
                fails.append(f"{rel} (block {bi}) — {reason}")

    # De-dupe while keeping order.
    seen: set[str] = set()
    uniq = [f for f in fails if not (f in seen or seen.add(f))]

    if uniq:
        print(
            "[check_337_collision] FAIL: the 337 / ghost collision appears in "
            "shipped copy:",
            file=sys.stderr,
        )
        for f in uniq:
            print(f"  {f}", file=sys.stderr)
        print(
            "\n  FloodWatch's 337 is modeled-prone provinces; COA's 337 is "
            "confirmed ghosts. They must never be conflatable in shipped copy "
            "or data.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[check_337_collision] PASS: scanned {scanned} files, no 337/ghost "
        "conflation in shipped copy or data."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
