"""Build the compiled COA/Ombudsman flagged flood-control dataset.

This is the highest legal-sensitivity workstream in FloodWatch. The output is
a hand-verified, in-code table of audit findings on DPWH flood-control
projects. Every row is sourced from one public article that names the
project, its location, and the cited COA/Ombudsman finding. FloodWatch does
not independently verify and makes no accusation; rows quote the cited
public record only.

Posture rules baked in here:
- Controlled finding vocab only: flagged_review | site_mismatch |
  pre_existing | defective. No "ghost", "fraud", "thief", "guilty",
  "corrupt" anywhere.
- Every row carries a fetchable http(s) source_url, a source_org, and a
  source_published date. Rows without all three are dropped.
- province is the GAUL name used as the `city` property of
  site/public/data/hazard_gap.geojson, so the downstream fuzzy join keys
  on a name FloodWatch already maps.
- contract_id is null unless a DPWH contractId is actually known. We never
  invent one; the description_key carries the fuzzy-join signal instead.

Run:
  python3 pipeline/coa_extract.py

Deterministic and network-free: the compiled table is in this file. There is
no fetch at run time, so CI output is byte-stable except for generated_utc.

Sourcing QA notes (which source produced which rows, and why each is
defensible) live in tmp/v1.5-coa-qa/run-notes.md.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "_coa_flagged.json"

# Controlled vocabulary for coa_finding. The check_coa_cited gate and the
# tests both import this; it is the single source of truth.
FINDING_VOCAB = ("flagged_review", "site_mismatch", "pre_existing", "defective")

# Words that must never appear anywhere in the emitted file. Accusatory or
# verdict language is out of bounds for a civic-tech accountability layer
# that only quotes the public record.
BANNED_WORDS = ("ghost", "fraud", "thief", "guilty", "corrupt")

DISCLAIMER = (
    "COA/Ombudsman findings per the cited public sources; FloodWatch does "
    "not independently verify and makes no accusation."
)

# Curated, hand-verified table. Each entry is one project as named by one
# fetchable public source. Province uses the GAUL name FloodWatch already
# maps (hazard_gap.geojson `city`). description_key is normalized at emit
# time from `description`. No amounts are stored: the accountability story
# is "flagged per source", not a money claim, and amounts are the most
# error-prone field to transcribe.
_CURATED: tuple[dict[str, str | None], ...] = (
    # --- S1: Wikipedia, well-cited; COA Sep-26 2025 Ombudsman referrals ---
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Angat River flood control structure, Barangay Santo Cristo, Pulilan",
        "coa_finding": "flagged_review",
        "source_url": "https://en.wikipedia.org/wiki/Flood_control_projects_scandal_in_the_Philippines",
        "source_org": "COA",
        "source_published": "2025-09-26",
    },
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Riverbank Protection Structure Package A, Barangay Bulihan, Plaridel",
        "coa_finding": "flagged_review",
        "source_url": "https://en.wikipedia.org/wiki/Flood_control_projects_scandal_in_the_Philippines",
        "source_org": "COA",
        "source_published": "2025-09-26",
    },
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Bocaue River slope protection, Barangay Bambang, Bocaue",
        "coa_finding": "flagged_review",
        "source_url": "https://en.wikipedia.org/wiki/Flood_control_projects_scandal_in_the_Philippines",
        "source_org": "COA",
        "source_published": "2025-09-26",
    },
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Bocaue River slope protection, Barangay Turo, Bocaue",
        "coa_finding": "flagged_review",
        "source_url": "https://en.wikipedia.org/wiki/Flood_control_projects_scandal_in_the_Philippines",
        "source_org": "COA",
        "source_published": "2025-09-26",
    },
    # Note: the GMA 2025-11-12 P344M batch (Baliuag / Malolos / Balagtas)
    # was fetched and is individually defensible, but its only canonical
    # URL contains an accusatory token in the slug. Re-citing those four
    # findings to a clean public URL was attempted and no clean source
    # covers that specific batch. Per posture, an uncitable-by-clean-URL
    # row is dropped, not force-fitted. See tmp/v1.5-coa-qa/run-notes.md.
    # --- S3: GMA News, 2025-09-18, fetched cleanly ---
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Angat River control structure, Sipat Section, Plaridel",
        "coa_finding": "site_mismatch",
        "source_url": (
            "https://www.gmanetwork.com/news/topstories/nation/959619/"
            "coa-dpwh-bulacan-flood-control-projects-p390-million/story/"
        ),
        "source_org": "GMA",
        "source_published": "2025-09-18",
    },
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Slope protection and waterways, Barangay Bunsuran, Pandi",
        "coa_finding": "site_mismatch",
        "source_url": (
            "https://www.gmanetwork.com/news/topstories/nation/959619/"
            "coa-dpwh-bulacan-flood-control-projects-p390-million/story/"
        ),
        "source_org": "GMA",
        "source_published": "2025-09-18",
    },
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Bocaue River slope protection item 1, Barangay Bambang, Bocaue",
        "coa_finding": "pre_existing",
        "source_url": (
            "https://www.gmanetwork.com/news/topstories/nation/959619/"
            "coa-dpwh-bulacan-flood-control-projects-p390-million/story/"
        ),
        "source_org": "GMA",
        "source_published": "2025-09-18",
    },
    {
        "contract_id": None,
        "province": "Bulacan",
        "description": "Bocaue River slope protection item 2, Barangay Bambang, Bocaue",
        "coa_finding": "pre_existing",
        "source_url": (
            "https://www.gmanetwork.com/news/topstories/nation/959619/"
            "coa-dpwh-bulacan-flood-control-projects-p390-million/story/"
        ),
        "source_org": "GMA",
        "source_published": "2025-09-18",
    },
)

_SOURCE_META = (
    "compiled from public COA/Ombudsman releases + reputable news, "
    "every row cited"
)

_WS = re.compile(r"[^a-z0-9]+")


def description_key(text: str) -> str:
    """Normalize a free-text project description into a stable fuzzy-join key.

    Lowercase, strip punctuation, collapse whitespace to single underscores,
    drop generic filler tokens that carry no join signal. Deterministic and
    idempotent: description_key(description_key(x)) == description_key(x).
    """
    low = _WS.sub(" ", str(text).lower()).strip()
    drop = {"the", "of", "and", "a", "an", "along", "at", "in", "barangay",
            "brgy", "city", "section", "item", "project", "purok"}
    toks = [t for t in low.split(" ") if t and t not in drop]
    return "_".join(toks)


def _row_valid(row: dict) -> str | None:
    """Return a reason string if the row is not defensible, else None."""
    fid = row.get("coa_finding")
    if fid not in FINDING_VOCAB:
        return f"coa_finding {fid!r} not in controlled vocab"
    url = row.get("source_url") or ""
    if not (url.startswith("http://") or url.startswith("https://")):
        return "source_url missing or not http(s)"
    if not row.get("source_published"):
        return "source_published missing"
    if not row.get("source_org"):
        return "source_org missing"
    blob = json.dumps(row, ensure_ascii=False).lower()
    for w in BANNED_WORDS:
        if w in blob:
            return f"banned word {w!r} present in row"
    return None


def build_rows() -> list[dict]:
    """Validate every compiled entry and shape it into the emitted schema.

    A compiled entry that fails validation is dropped, not patched. Shipping
    a smaller high-confidence set is the correct posture.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[dict] = []
    for raw in _CURATED:
        reason = _row_valid(raw)
        if reason is not None:
            print(f"  DROP: {raw.get('description')!r}: {reason}",
                  file=sys.stderr)
            continue
        out.append(
            {
                "contract_id": raw["contract_id"],
                "province": raw["province"],
                "description_key": description_key(raw["description"]),
                "coa_finding": raw["coa_finding"],
                "source_url": raw["source_url"],
                "source_org": raw["source_org"],
                "source_published": raw["source_published"],
                "extracted_utc": now,
            }
        )
    return out


def main() -> int:
    rows = build_rows()
    if not rows:
        print("[coa_extract] FAIL: no defensible rows survived validation",
              file=sys.stderr)
        return 1
    payload = {
        "_meta": {
            "source": (
                "Public COA/Ombudsman releases and reputable PH news "
                "(Wikipedia-cited COA filings, GMA News). See "
                "tmp/v1.5-coa-qa/run-notes.md for the per-row source map."
            ),
            "method": _SOURCE_META,
            "generated_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "n_rows": len(rows),
            "disclaimer": DISCLAIMER,
        },
        "rows": rows,
    }
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
        + "\n",
        encoding="utf-8",
    )
    print(f"[coa_extract] wrote {OUT.relative_to(HERE.parent)}: "
          f"{len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
