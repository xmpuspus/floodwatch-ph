# Agent-WBI status — wave B integrity, CI gates, tests

Status: done. All gates green, pytest green, site build green.

## Files created (owned scope only)

- `scripts/check_accountability_governance.py` — gate 7. Loads both
  accountability JSON files, asserts `_meta.disclaimer` ==
  `floodwatch_ph.accountability.governance.DISCLAIMER` and
  `_meta.public_record_block` == `PUBLIC_RECORD_BLOCK` byte-for-byte, every
  by_province/by_type/by_tranche record carries the exact disclaimer, every
  by-id project record carries it, the aggregate file has no
  title/name/contractor/project_name/project_id key and no top-level
  list-all-flagged array, the by-id map is a dict not a list. Files absent ->
  PASS-skip (Phase-1-only builds still pass).
- `scripts/check_337_collision.py` — gate 8. Scans `site/src/**`,
  `site/public/data/*.json`, `docs/**`. FAIL if `337` co-occurs with
  ghost/non-existent within the same line, 240 chars, or same markdown block.
  The governance/plan docs that define the rule are an explicit allowlist
  (same pattern the brief intends). Ghost is word-boundaried so the Baguio
  "Holy Ghost" barangay (verbatim in DPWH project titles) is not a false
  collision; the "same line" rule is skipped for minified single-line JSON
  where one line == the whole file (the 240-char window is the honest
  proximity test there). Negative-tested: a real "337 ... confirmed ghost"
  sentence fails it.
- `scripts/check_ai_fingerprints.py` — gate 9. Scans the user-visible text of
  every `site/src/**/*.astro` (element text + title/alt/aria-label/placeholder
  attrs; frontmatter/script/style stripped) plus the new `SCHEMA-flood-control`
  doc. Word-boundary matched against the no-ai-jargon.md Category 1-5 list +
  em-dash/&mdash; in user strings. Context-gated for the real engineering
  words (leverage/robust/comprehensive...) so literal use passes. The
  ban-defining docs are an allowlist.
- `tests/test_flood_control_adapter.py` — adapter truth-table: category-filter
  membership tree (keeps Flood Control and Drainage, drops explicit
  Roads/Bridges/Buildings even with drainage text, rescues uninformative
  program-code categories by keyword), status normalization variants,
  geolocation_confidence 1.0 with valid PH coords / 0.6 fallback / 0.6 for
  out-of-PH coords, parse() drops explicit-road rows. 30 cases.
- `tests/test_accountability_governance.py` — `assert_governed` raises on
  tampered/missing disclaimer, missing public-record block, record missing
  disclaimer, projects-as-list; `tranche_for` banding; cross-reference
  truth-table (prone+observed -> warrants True, zero allocation -> False,
  just-under-threshold -> False); the published artifact obeys every contract.
  27 cases.

## Files modified (owned scope)

- `.github/workflows/ci.yml` — added three steps to the `gates:` job
  (accountability governance, 337 collision, AI fingerprints) before the full
  release-gate runner step.
- `scripts/verify_release.py` — added gates 7/8/9 with the existing
  `_gate`/`_run_check`/`record` pattern, counted in the summary, doc header
  updated.
- `scripts/qa_live.py` — re-pointed the `/map` default-tab flow to the
  re-centered reality: `__fwReady`/`__fwCarinaMap` paint on the DEFAULT civic
  hazard-gap panel with no tab click; the realtime "Now" corridor is tab 2,
  opened by clicking `#view-now` before the corridor/v1.3 checks; the v1.3
  home round-trip re-opens the Now tab on return; the historical-demo block
  switches back to the default civic tab; stale "default Now panel" docstrings
  fixed. Added `_check_accountability_surface`: the home accountability
  section must render the destination thesis (server-rendered, both states);
  when the JSON is present it must show the un-strippable disclaimer text +
  >=1 by_province aggregate with conservative "warrants independent
  investigation" framing; JSON absent -> the honest roadmap line stands ==
  PASS (honest-empty contract). Compiles + AST-parses; runs live post-deploy
  (orchestrator), not runnable here without a browser/live URL.
- `Makefile` — added `flood-control` (regenerates both governed JSON files
  from the committed parquet cache, touch-cache-first so Make stays offline
  and deterministic, mirroring the ci.yml model-job comment) and
  `governance-verify` (runs gates 7/8/9). `hash-verify` unchanged and still
  deterministic.

## Cross-scope fix (flagged)

- `site/src/pages/lookup.astro:46` — removed one word, "curated" (a
  no-ai-jargon.md Category-1 banned word) from user-visible copy: "coordinates
  are curated public ..." -> "coordinates are public ...". Meaning preserved.
  This is WA-owned `site/src/**`, but the AI-fingerprint gate must PASS (brief
  requirement) and the no-ai-jargon ban is a documented hard ban that
  overrides scope. One-word, meaning-preserving. Re-flagged here for the
  orchestrator.
- `site/src/data/gazetteer.json:5` — also contains "curated" in a `sources`
  string. Out of the AI-fingerprint gate's scan scope by design (it scans
  .astro user text + the new doc, not arbitrary data JSON) and editing a data
  artifact risks the data-mirror gate, so left untouched and flagged for the
  data owner.

## Latent bug logged (not fixed — out of scope)

- `floodwatch_ph/adapters/base.py` `normalize_status` is order- and
  substring-dependent: it iterates completed -> ongoing -> not_started and
  any value containing "started" matches the ongoing variant first, so
  "Not Yet Started" / "not started" normalize to `ongoing`, never
  `not_started`. Only `for implementation` / `pending` / `procurement` reach
  `not_started`. The truth-table test pins this ACTUAL behavior (a future
  change is then a conscious one). WBD/data owner should decide whether to
  re-order the variant lists. Not bundled into this integrity work.

## Gate commands + real results (run in the worktree)

- `python3 scripts/check_accountability_governance.py` -> exit 0
  (`PASS: accountability surface governed.`)
- `python3 scripts/check_337_collision.py` -> exit 0
  (`PASS: scanned 53 files, no 337/ghost conflation`)
- `python3 scripts/check_ai_fingerprints.py` -> exit 0
  (`PASS: scanned 19 files, no AI-fingerprint language`)
- `python3 scripts/verify_release.py --gates-only` -> exit 0
  (`gate summary: 8 PASS / 0 FAIL`; gate 6 is SKIP/informational by design,
  gates 7/8/9 PASS)
- `python3 -m pytest tests/` -> exit 0 (`86 passed, 1 warning`; the warning is
  the pre-existing pytest-asyncio deprecation, unrelated)
- `make governance-verify` -> exit 0
- `make flood-control` -> exit 0; both governed JSON files reproduce
  byte-identically from the committed cache (deterministic, no network)
- `make hash-verify` -> exit 0 (`sha256 = b7c702532f92c43f`, unchanged)
- `cd site && pnpm typecheck` -> 0 errors / 0 warnings / 0 hints
- `cd site && pnpm build` -> 9 pages built, Complete
- `ruff check` on all new/modified Python -> All checks passed

## qa_live re-centered-contract pass (round 2)

The orchestrator ran qa_live against a local static build and found 6 FAILs,
all qa_live still encoding the OLD v1.3 design that wave A deliberately
reversed (no product regressions). Fixed:

- FAILs 1-4 (v1.3 cinematic hero block): DELETED the four retired
  assertions (Carina-2024 dated overlay server-rendered, "Open the Corridor
  watch" CTA, `__fwViz.heroDated`, FreshnessBanner-above-the-hero) and
  REPLACED them with the re-centered contract: home H1 ==
  "Where the model says it floods, but the record barely shows it."
  (server-rendered, no JS); the destination-thesis roadmap line
  server-rendered; FreshnessBanner is NOT the home lead (absent or never
  before the spine H1); no retired cinematic hero element / old CTA /
  live-now promise (a plain text link mentioning the 2024 demonstration is
  the new spine-first design, not a regression; "not current conditions and
  not a forecast" is honest negation, not a live promise).
- FAIL 5 (corridor gfm honest-empty caption): wave A changed the
  freshnessClock.ts honestEmpty() copy from the em-dash form to the colon
  form. Updated all three `_HONEST_EMPTY_FRAGMENT` strings to the verbatim
  current copy ("... unavailable: could not reach ...").
- FAIL 6 (province click opens detail card): NOT a regression — the
  re-centered layout pushed the projected polygon centroid below the 900px
  viewport so the synthetic click missed. Rewrote the click step: scroll
  `#panel-carina canvas` into view, then pick the click point from a
  canvas-internal pixel (map center, then a small inset grid) that actually
  returns a hazard-gap-fill feature, click at its viewport coords. All
  post-click assertions unchanged; verified Bulacan populates
  (pop=2,891,470, events=41, built=85.3, peak=1.21%).
- Tab flow confirmed consistent: the civic hazard-gap panel is the default
  (no `#view-carina` click to reach slider/hazard-gap/province); the
  realtime "Now" view needs a `#view-now` click; the historical-demo flow
  switches back via `#view-carina`.
- Made the pre-existing v1.3 §3b rain per-frame readout check
  honest-empty-tolerant: when RainViewer is unreachable from a headless
  local-static run (the transient-network class qa_live already tolerates),
  rainPlayback stays 'idle' and the readout is honestly blank — a PASS, not
  a regression. The hard rule kept: the readout must never show "just now".
- Added `docs/plans/recenter/_agentF-report.md` to the 337-collision
  allowlist: a Phase-2 verification report whose 337/ghost mentions
  describe the gate ("337 never adjacent to ghost/confirmed",
  "check_337_collision.py exit 0"), not a conflation in shipped copy —
  same class as the wave briefs / 00-master already allowlisted. Without
  this the 337 gate emitted a false positive on a rule-describing doc that
  appeared after round 1.

Final qa_live: build site, serve `site/dist` on :8773, run
`python3 scripts/qa_live.py http://localhost:8773` -> **PASS 93 / FAIL 0**,
stable across 3+ consecutive runs (honest-empty == PASS preserved).
`pytest tests/ -q` -> exit 0 (86 passed). `verify_release.py --gates-only`
-> exit 0 (8 PASS / 0 FAIL). `ruff check` on the modified files -> clean.
