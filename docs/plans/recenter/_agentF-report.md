# Agent-F honesty + data-integrity gate — verdict

Run by orchestrator directly (the dispatched reviewer agent isolated into a stale
worktree checkout and returned incomplete; gates re-run against final HEAD 159a201).

## Verdict: SHIP

Branch `feat/northstar-recenter` @ 159a201. All honesty + data-integrity gates pass.

| # | Gate | Result | Evidence |
|---|------|--------|----------|
| 1 | No false live/forecast/verdict; rain attributed, not "freshest", not lead | PASS | FreshnessBanner reframed "most recent observed pass, lagged, not a live feed"; rain = "rainfall context (source: RainViewer / PAGASA)"; index.astro/map.astro lead with the spine |
| 2 | Every layer dated/as-of stamped | PASS | as_of strips on realtime; `_meta.dates` on extent; accountability `_meta.generated_utc` + per-pass dates |
| 3 | Complementary-not-replacement intact, not net-deflecting | PASS | "complementary / never a replacement" present on index, map, lookup (3/3); positive "what FloodWatch is for" line on hero |
| 4 | Accountability conservative only; zero accusatory/efficacy/causality | PASS | grep site/src + accountability JSON for ghost/fraud/failed/caused/prevented = 0 (the only hit, safety.astro:52, is an explicit "inappropriate phrasing" negative example in the conservative-language guide) |
| 5 | Disclaimer + RA 10173 public-record block rendered on every accountability surface + byte-identical in JSON _meta | PASS | AccountabilitySurface.astro renders `_meta.disclaimer` + `public_record_block` (17 refs); `assert_governed` byte-match both JSON files |
| 6 | Aggregation-only; never a named flagged-project list in UI | PASS | AccountabilitySurface renders by_province/by_type/by_tranche only; aggregate JSON has no name/title keys; by-id is a keyed dict, no list-all shape (check_accountability_governance.py exit 0) |
| 7 | Geolocation ~10-15% MYPS uncertainty stated, not hidden | PASS | DISCLAIMER constant carries "an estimated 10 to 15 percent carry coordinate uncertainty per COA"; rendered via _meta.disclaimer; per-result "Per DPWH/BetterGovPH records" framing |
| 8 | Specific numbers interpolated from JSON, not hardcoded prose | PASS | AccountabilitySurface formats from fetched `_meta`/records; numbers (36,711 / ₱1.74T) computed by pipeline, captured in _wbd-computed.txt |
| 9 | The 337 collision: COA-337 never used; "337" never adjacent to ghost/confirmed | PASS | check_337_collision.py exit 0; metrics.ts `uncharted_count "337"` is the only 337; zero "ghost" in site/ |
| 10 | Destination thesis = in-progress roadmap where data absent, data-backed where JSON renders, not overclaimed | PASS | AccountabilitySurface server-renders the roadmap line; aggregates replace it only when the governed JSON is present |
| 11 | Plain English / no AI fingerprints across user-visible copy | PASS | check_ai_fingerprints.py exit 0; gazetteer "curated"->"compiled"; 0 em-dashes in .astro user strings |

Supporting gate runs (final HEAD): governance=0, 337=0, ai-fingerprints=0,
verify_release `8 PASS / 0 FAIL`, pytest `92 passed`, site typecheck=0 build=0,
`make hash-verify` deterministic (b7c702532f92c43f unchanged).

No must-fix items. The two latent items WBI flagged were resolved (status-
normalization defect fixed in c4c8835; "curated" copy fixed in 159a201).
</content>
