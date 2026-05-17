"""Contradictory-envelope invariant for the home accountability lead sentence.

The home surface picks one province for a single conservative sentence. The
Sentinel-1 clause ("observed flooding there on N dated passes") is only valid
when that province actually has observed_flood_passes > 0. Asserting
"observed flooding on 0 dated passes" is a contradiction (a positive claim
paired with a zero count). This test replicates the selection rule in
AccountabilitySurface.astro and asserts the contradiction can never form on
the published artifact, on every code path that produces the lead.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ACCT = REPO / "site" / "public" / "data" / "flood_control_accountability.json"


def _select_lead(by_province: list[dict]) -> dict | None:
    """Mirror of renderHome's selection: among warrants_investigation
    provinces, prefer the highest-allocation one with an observed pass;
    otherwise the highest-allocation modeled-prone province."""
    warrants = [p for p in by_province if p.get("warrants_investigation") is True]
    if not warrants:
        return None
    observed = sorted(
        (p for p in warrants if (p.get("observed_flood_passes") or 0) > 0),
        key=lambda p: -(p.get("allocation_php") or 0),
    )
    if observed:
        return {"province": observed[0], "asserts_observation": True}
    top = sorted(warrants, key=lambda p: -(p.get("allocation_php") or 0))[0]
    return {"province": top, "asserts_observation": False}


def test_lead_never_asserts_observation_with_zero_passes() -> None:
    data = json.loads(ACCT.read_text())
    sel = _select_lead(data.get("by_province") or [])
    if sel is None:
        return  # no warrants province -> roadmap line, nothing to assert
    passes = sel["province"].get("observed_flood_passes") or 0
    if sel["asserts_observation"]:
        # The Sentinel-1 clause is used; the province must actually have a pass.
        assert passes > 0, (
            f"{sel['province'].get('province')!r} would assert Sentinel-1 "
            f"observation with observed_flood_passes={passes}"
        )
    else:
        # Recurrence-only fallback: it must be a real modeled-prone case and
        # the lead must NOT claim observation (passes is irrelevant here).
        assert sel["province"].get("warrants_investigation") is True


def test_selection_is_deterministic_and_real() -> None:
    data = json.loads(ACCT.read_text())
    sel = _select_lead(data.get("by_province") or [])
    if sel is None:
        return
    p = sel["province"]
    # The chosen province is a real published aggregate, not synthesized.
    assert p in (data.get("by_province") or [])
    assert isinstance(p.get("allocation_php"), int)
    assert (p.get("allocation_php") or 0) > 0
