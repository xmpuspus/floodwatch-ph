# Agent-WBI brief — wave B integrity, CI gates, tests (Phase 2, after WA + WBD verified)

You own: `scripts/**`, `tests/**`, `.github/workflows/ci.yml`, `Makefile` (if present),
`scripts/qa_live.py`, `scripts/verify_release.py`. Do NOT touch `site/src/**` copy or
`pipeline/flood_control.py` logic (read them; coordinate via status files).

Read first: `docs/plans/recenter/00-master.md`, `_wbd-status.md`, `_wa-status.md`,
`docs/research/ghostwatch-study.md` §VI (CI gates), `flood-control-data-feasibility.md`.
Study real ghostwatch tests:
- `/Users/xavier/Desktop/ghostwatch/tests/test_api.py` lines 279-306 (disclaimer-presence gate)
- `/Users/xavier/Desktop/ghostwatch/tests/test_classifier.py` 96-166 (truth-table tests)

## Build

1. `scripts/check_accountability_governance.py` — CI gate (exit 1 on violation):
   - Loads `site/public/data/flood_control_accountability.json` +
     `flood_control_by_id.json`. Fails if `_meta.disclaimer` missing or != the canonical
     `floodwatch_ph.accountability.governance.DISCLAIMER`, or if any aggregation record
     lacks `disclaimer`, or if `public_record_block` missing on the aggregate file.
   - Fails if the aggregate file contains any project-name/contractor key (aggregation-
     only assertion: forbid keys `title|name|contractor|project_name` at by_province/
     by_type/by_tranche level).
   - Fails if a "list all flagged" shape exists (no top-level array of named flagged
     projects; by-id map must be a dict keyed by id, not a list).
   - Skips cleanly (PASS) if files absent (so Phase-1-only builds still pass), but FAILS
     if files present and governance broken.
2. `scripts/check_337_collision.py` — release grep gate:
   - Scan `site/src/**`, `site/public/data/*.json`, `docs/**` rendered copy. FAIL if the
     token `337` occurs within the same line OR within 240 chars OR same DOM/markdown
     block as any of: `ghost`, `confirmed ghost`, `ghost project`, `non-existent`. Also
     FAIL if the COA-337 figure is cited at all alongside FloodWatch's own
     `uncharted_count`. Print every offending location.
3. `scripts/check_ai_fingerprints.py` — release grep gate over `site/src/**` user-visible
   copy + `docs/research/recenter-plan.md`-adjacent new docs + commit-message file if
   present: FAIL on the no-ai-jargon.md Category-1..5 banned list (delve, leverage(v),
   seamless, robust(filler), comprehensive(inflating), underscore, testament, realm,
   tapestry, "navigate the", "in today's", "it's important to note", "let me", "I'd be
   happy", em-dash in .astro user strings, etc.). Word-boundary matched; allow the
   documented technical exceptions. Print file:line for each hit.
4. `tests/test_flood_control_adapter.py` + `tests/test_accountability_governance.py`:
   - Adapter truth-table: category filter keeps flood-control / drops roads-bridges;
     status normalization variants; geolocation_confidence 1.0 vs 0.6 fallback.
   - Governance: `assert_governed` raises on missing/altered disclaimer; every emitted
     aggregate record carries the exact DISCLAIMER; by-id map is dict-keyed not list.
   - Cross-reference: a project in a modeled-prone province with observed passes sets
     `warrants_investigation=True`; one with zero allocation / not-prone sets False.
   - No mocking the thing under test; per-function lightweight inputs (no network).
5. Wire gates into `.github/workflows/ci.yml` `gates:` job (after the existing 4) and into
   `scripts/verify_release.py` (add gates 7/8/9, same `_gate` pattern, counted).
6. `scripts/qa_live.py`: the `/map` default flipped to the civic/observed view (per
   `_wa-status.md`). Update the behavioral flow: the DEFAULT panel is now the
   civic/Carina/hazard-gap map (slider, hazard-gap-fill, province click) — it must paint
   `window.__fwReady`/`__fwCarinaMap` as default; the realtime "Now" view is now tab 2.
   Re-point the tab clicks accordingly. Add an accountability-surface check: the homepage
   accountability section renders the disclaimer text and at least one by_province
   aggregate (or, if JSON absent, the honest roadmap line). Keep honest-empty == PASS.
7. If a `Makefile` exists, add a `flood-control` target + a `governance-verify` target;
   keep `hash-verify` deterministic (the parquet cache must be touched in dependency
   order like the embeddings cache, see ci.yml model job comment).

## Constraints
- Every gate exits non-zero on violation and is wired into CI so the build fails.
- Plain English, no AI fingerprints in code/comments/docstrings.
- Tests must pass: `pytest tests/ -q`. Run them; fix until green.
- Status -> `docs/plans/recenter/_wbi-status.md` with the exact gate commands + results.
</content>
