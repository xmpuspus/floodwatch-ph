"""Governance constants for the flood-control accountability surface.

FloodWatch is a static site plus a Python pipeline. There is no API layer to
inject a disclaimer at request time, so the disclaimer is a hardcoded constant
here. The pipeline imports it and writes it into the top-level _meta and into
every record of each generated accountability file. Clients cannot strip it
because it is baked into the published artifact, and CI fails the build if it
is missing or altered.

Posture: conservative civic-tech-ph. "warrants independent investigation",
never an accusation. No efficacy or causation language anywhere downstream.
"""

from __future__ import annotations

from typing import Any

# Hardcoded, un-strippable. The pipeline writes this verbatim into _meta and
# every record. assert_governed checks equality byte-for-byte. If you change
# this string you must also bump any test that pins it.
DISCLAIMER = (
    "Statistical indicators derived from public data. Patterns may have "
    "legitimate explanations. Flood-control project locations are per "
    "DPWH/BetterGovPH records (MYPS planning coordinates; an estimated 10 to "
    "15 percent carry coordinate uncertainty per COA). This surface reports "
    "where money was allocated and where Sentinel-1 still observed flooding. "
    "It is not a finding of fraud, project failure, or causation. Specific "
    "allegations require independent investigation and corroboration."
)

# The all-data-is-public-record block. Same un-strippable treatment as the
# disclaimer: written into _meta of every accountability file.
PUBLIC_RECORD_BLOCK = (
    "All figures here are computed from public records released by DPWH and "
    "mirrored by BetterGovPH under CC0, cross-referenced against FloodWatch's "
    "own open satellite signal. No private or personal data is collected, "
    "stored, or published. Project-level detail is reachable only by direct "
    "id lookup, never as a ranked list. This is a transparency surface over "
    "the government's own data, consistent with RA 10173. Corrections and "
    "source disputes should be raised with DPWH and the originating audit "
    "bodies."
)

# Budget tranches in pesos. Order is the render order; the pipeline emits
# by_tranche in this order and the UI renders it as given. Each tuple is
# (label, lower_inclusive, upper_exclusive_or_None).
BUDGET_TRANCHES: list[tuple[str, float, float | None]] = [
    ("<₱10M", 0.0, 10_000_000.0),
    ("₱10-50M", 10_000_000.0, 50_000_000.0),
    ("₱50-100M", 50_000_000.0, 100_000_000.0),
    ("₱100-500M", 100_000_000.0, 500_000_000.0),
    (">₱500M", 500_000_000.0, None),
]


def tranche_for(amount: float | None) -> str | None:
    """Return the tranche label for an allocation amount, or None if unknown.

    An amount of None or <= 0 has no tranche. The first matching band wins;
    the open-ended top band catches anything at or above its lower bound.
    """
    if amount is None or amount <= 0:
        return None
    for label, low, high in BUDGET_TRANCHES:
        if amount >= low and (high is None or amount < high):
            return label
    return None


def assert_governed(obj: Any) -> None:
    """Raise if the file object is not correctly governed.

    Checks the top-level _meta disclaimer and public-record block equal the
    hardcoded constants byte-for-byte, and that every record dict carries the
    same disclaimer. Walks by_province / by_type / by_tranche lists and the
    projects map. Called by the pipeline before any accountability file is
    written.
    """
    if not isinstance(obj, dict):
        raise ValueError("governed object must be a dict")

    meta = obj.get("_meta")
    if not isinstance(meta, dict):
        raise ValueError("governed object missing _meta dict")

    if meta.get("disclaimer") != DISCLAIMER:
        raise ValueError("_meta.disclaimer missing or altered")
    if meta.get("public_record_block") != PUBLIC_RECORD_BLOCK:
        raise ValueError("_meta.public_record_block missing or altered")

    for key in ("by_province", "by_type", "by_tranche"):
        rows = obj.get(key)
        if rows is None:
            continue
        if not isinstance(rows, list):
            raise ValueError(f"{key} must be a list")
        for i, row in enumerate(rows):
            if not isinstance(row, dict) or row.get("disclaimer") != DISCLAIMER:
                raise ValueError(f"{key}[{i}] disclaimer missing or altered")

    projects = obj.get("projects")
    if projects is not None:
        if not isinstance(projects, dict):
            raise ValueError("projects must be a dict keyed by project_id")
        for pid, rec in projects.items():
            if not isinstance(rec, dict) or rec.get("disclaimer") != DISCLAIMER:
                raise ValueError(f"projects[{pid}] disclaimer missing or altered")
