"""CI gate: no AI-fingerprint language in shipped copy.

Enforces ~/.claude/rules/no-ai-jargon.md Category 1-5 over what ships to a
reader: the user-visible text of every site/src/**/*.astro page/component, plus
the new wave-B research/plan docs authored in this re-center. The canonical
rules file lives in the user's home, outside the repo, so the banned list is
inlined here and kept in sync by hand; this gate is self-contained so CI can
run it with no external file.

Rules:
  - Word-boundary matched (so "user" never trips "use ... utilize").
  - The documented technical exceptions are allowed (literal engineering use:
    "spin up the container", "ship the release", "data pipeline", ...).
  - .astro files: only the user-visible text is scanned (element text and the
    human-facing attributes title/alt/aria-label/placeholder), not code,
    imports, class names, or script blocks. Em-dash in any user string is a
    fail (em-dashes in copy read as machine-written).
  - The governance/plan docs that DEFINE the ban necessarily quote the banned
    words; they are an explicit allowlist, exactly like check_337_collision.

Exit 0 = clean, 1 = any hit (file:line printed for each).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Category 1-5 banned terms from no-ai-jargon.md. Multi-word phrases are
# matched as a flexible run of whitespace. Single words are \b-anchored.
BANNED = [
    # Category 1: AI fingerprint words
    "delve", "delve into", "tapestry", "in the realm of", "pivotal",
    "paramount", "multifaceted", "testament", "bustling", "meticulously",
    "intricate", "intricacies", "elevate", "unveil", "showcase",
    "underscore", "glimpse into", "dive into", "dive deep", "myriad",
    "plethora", "sprawling", "holistic", "seamless", "seamlessly",
    "cutting-edge", "state-of-the-art", "game-changer", "paradigm shift",
    "revolutionize", "transformative", "groundbreaking",
    "embark on a journey", "navigate the complexities", "stark contrast",
    "stark reminder", "ever-evolving", "ever-changing", "curated",
    "daunting",
    # Category 2: helpfulness theater
    "great question", "excellent point", "i'd be happy to", "i'd love to",
    "let me help", "let me explain", "let me clarify", "let me walk you",
    "hope this helps", "feel free to", "i'm here to help",
    # Category 3: formulaic AI structures
    "in today's", "it's important to note", "it's worth noting",
    "it should be noted", "there are several key factors",
    "these are just a few examples", "the possibilities are endless",
    "in conclusion", "in essence",
    # Category 4: corporate jargon
    "circle back", "touch base", "sync up", "low-hanging fruit",
    "move the needle", "boil the ocean", "take this offline",
    "punch above", "at the end of the day",
    # Category 5: eng-bro / PM speak
    "double-click on", "first-class citizen", "single pane of glass",
    "tiger team", "table stakes",
]

# Terms that are real engineering words in literal use. They are flagged only
# when no literal-context token is nearby (within the same line). Keeps
# "ship the release" / "data pipeline" / "spin up the container" passing.
CONTEXT_GATED = {
    "leverage": (re.compile(r"\bleverage\b", re.I),
                 ("ratio", "financ", "debt", "load", "torque")),
    "utilize": (re.compile(r"\butilize[sd]?\b", re.I), ()),
    "robust": (re.compile(r"\brobust\b", re.I),
               ("test", "retry", "error", "fault", "pipeline", "schema")),
    "comprehensive": (re.compile(r"\bcomprehensive\b", re.I), ()),
    "foster": (re.compile(r"\bfoster\b", re.I), ()),
    "harness": (re.compile(r"\bharness\b", re.I), ()),
    "empower": (re.compile(r"\bempower\b", re.I), ()),
    "facilitate": (re.compile(r"\bfacilitate[sd]?\b", re.I), ()),
    "streamline": (re.compile(r"\bstreamline[sd]?\b", re.I), ()),
}

# Docs that define / quote the ban list. They must contain the banned words;
# that is their purpose. Same allowlist pattern as check_337_collision.
DOC_ALLOWLIST = {
    REPO / "docs" / "research" / "copy-audit.md",
    REPO / "docs" / "research" / "recenter-plan.md",
    REPO / "docs" / "research" / "ghostwatch-study.md",
    REPO / "docs" / "research" / "product-audit-reframed.md",
    REPO / "docs" / "research" / "skeptic-walkthrough.md",
    REPO / "docs" / "research" / "flood-control-data-feasibility.md",
    REPO / "docs" / "plans" / "recenter" / "00-master.md",
    REPO / "docs" / "plans" / "recenter" / "10-wb-data-brief.md",
    REPO / "docs" / "plans" / "recenter" / "20-wa-site-brief.md",
    REPO / "docs" / "plans" / "recenter" / "30-wbi-integrity-brief.md",
    REPO / "docs" / "plans" / "recenter" / "_wbd-status.md",
    REPO / "docs" / "plans" / "recenter" / "_wa-status.md",
    REPO / "docs" / "plans" / "recenter" / "_wbi-status.md",
}

# The new wave-B docs that DO ship as prose a reader sees and are not the
# ban-defining docs above.
NEW_DOCS = [
    REPO / "docs" / "research" / "SCHEMA-flood-control.md",
]


def _compile(term: str) -> re.Pattern[str]:
    if " " in term:
        parts = [re.escape(p) for p in term.split()]
        return re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.I)
    return re.compile(r"\b" + re.escape(term) + r"\b", re.I)


_BANNED_RE = [(t, _compile(t)) for t in BANNED]
_EMDASH = re.compile(r"[—–]|&mdash;|&ndash;")

# Extract user-visible text from .astro: element text nodes + human-facing
# attribute values. Skip --- frontmatter, <script>, <style>, and code.
_FRONTMATTER = re.compile(r"^---.*?---", re.S)
_SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_HUMAN_ATTR = re.compile(
    r'\b(?:title|alt|aria-label|placeholder)\s*=\s*"([^"]*)"', re.I
)


def _astro_user_text(src: str) -> str:
    body = _FRONTMATTER.sub("", src, count=1)
    body = _SCRIPT_STYLE.sub(" ", body)
    attr_text = " ".join(m.group(1) for m in _HUMAN_ATTR.finditer(body))
    text_nodes = _TAG.sub("\n", body)
    return text_nodes + "\n" + attr_text


def _scan(label: str, text: str) -> list[str]:
    hits: list[str] = []
    lines = text.splitlines()
    for ln, line in enumerate(lines, 1):
        low = line.lower()
        for term, rx in _BANNED_RE:
            if rx.search(line):
                hits.append(f"{label}:{ln} banned term {term!r} :: {line.strip()[:90]}")
        for term, (rx, ctx) in CONTEXT_GATED.items():
            if rx.search(line) and not any(c in low for c in ctx):
                hits.append(
                    f"{label}:{ln} filler {term!r} (no literal-eng context) "
                    f":: {line.strip()[:90]}"
                )
        if _EMDASH.search(line):
            hits.append(f"{label}:{ln} em-dash / &mdash; in user string "
                         f":: {line.strip()[:90]}")
    return hits


def main() -> int:
    all_hits: list[str] = []
    scanned = 0

    src = REPO / "site" / "src"
    if src.is_dir():
        for p in sorted(src.rglob("*.astro")):
            scanned += 1
            text = _astro_user_text(p.read_text(encoding="utf-8", errors="replace"))
            all_hits += _scan(str(p.relative_to(REPO)), text)

    for p in NEW_DOCS:
        if p.is_file() and p.resolve() not in {d.resolve() for d in DOC_ALLOWLIST}:
            scanned += 1
            all_hits += _scan(
                str(p.relative_to(REPO)),
                p.read_text(encoding="utf-8", errors="replace"),
            )

    if all_hits:
        print(
            "[check_ai_fingerprints] FAIL: AI-fingerprint language in shipped "
            "copy:",
            file=sys.stderr,
        )
        for h in all_hits:
            print(f"  {h}", file=sys.stderr)
        print(
            "\n  Rewrite in plain English (see ~/.claude/rules/"
            "no-ai-jargon.md).",
            file=sys.stderr,
        )
        return 1

    print(
        f"[check_ai_fingerprints] PASS: scanned {scanned} files, no "
        "AI-fingerprint language in shipped copy."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
