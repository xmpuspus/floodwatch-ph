# Agent-WA brief — wave A narrative re-center + accountability surface UI + plain-English pass

You own: `site/**` ONLY. Do NOT touch Python, scripts, tests, .github, Makefile.

Read first: `docs/plans/recenter/00-master.md`, `docs/research/recenter-plan.md`
(DEMOTE/PROMOTE/REFRAME tables + Wave A section + LOCKED table), `skeptic-walkthrough.md`,
`product-audit-reframed.md`, `docs/research/SCHEMA-flood-control.md` (Agent-WBD commits it
first; code the accountability UI against it).

Current files you will change (read them): `site/src/pages/index.astro`,
`site/src/pages/map.astro`, `site/src/pages/lookup.astro`,
`site/src/components/NowView.astro`, `site/src/components/MapView.astro`,
`site/src/components/FreshnessBanner.astro`, `site/src/components/AreaLookup.astro`,
`site/src/components/Header.astro`, `site/src/data/metrics.ts`,
`site/src/lib/areaLookup.ts`, plus `methodology.astro`/`recurrence.astro`/`faq.astro`/
`safety.astro` copy where AI fingerprints exist.

## Wave A changes (recenter-plan.md is the spec; this is the net)

1. **Split identity.** `/` and `/map` lead with the spine (recurrence-vs-record gap).
   ALL realtime (rain banner, Corridor watch / NowView, cinematic GIBS) collapses to ONE
   explicitly-secondary, fully-attributed context surface. Rain is always
   "rainfall context (source: RainViewer / PAGASA, not produced by FloodWatch)". Never
   "freshest". No FW-branded freshness clock as a lead. FreshnessBanner: demote from the
   first thing on `/` and `/map`; reframe to "most recent observed pass, lagged, the open
   reproducible record, not a live feed".
2. **Homepage hero (index.astro).** New H1 = the recurrence-vs-record spine framed as
   **step 1 of the accountability question** (P1/R1). State P2 (single-repo bit-exact
   reproducibility, ~30s, no GPU) and P3 (the pluvial/urban class Google Flood Hub says
   it does not model, observed after the fact, openly) on the hero. Name the destination
   thesis verbatim, as an explicit **in-progress roadmap line, not a backed claim**:
   "Where flood-control money was spent, and where the water still came." until wave B
   data renders, then it becomes the data-backed section (see 6). Demote the old
   "Where the water actually went." extent H1 to a supporting section (D6).
3. **`/map` default flip (map.astro).** Civic/observed + hazard-gap view = the DEFAULT
   tab (currently the "2024 Carina demo" panel content + hazard-gap). The "Now (rain +
   expressways)" view = the SECOND tab, labelled "rainfall + expressway context (source:
   RainViewer / PAGASA)". Keep both maps working; the JS `show()` default and
   `aria-selected` flip. NowView/CorridorWatch demoted to a small context module, not a
   headline H2. The default tab must paint `window.__fwReady===true` (qa_live depends on
   it; Agent-WBI re-points qa_live to the new default — coordinate via status file).
4. **`/lookup` synthesis (R2).** AreaLookup result must state the gap as ONE explicit
   conservative sentence per result ("modeled-prone + thin historical record =
   under-observed-prone; warrants verification"), not five rows to infer. Keep the
   evidence rows but lead each result with the synthesized sentence. Promote `/lookup`
   in nav order (P4) and link it prominently from the spine hero.
5. **Retire cinematic basemap as a default concern (D4/D5).** GIBS/SAR-raster off by
   default; do not foreground; drop "Freshest" superlative from the layer stack.
6. **Accountability surface (the wave B payoff).** Add a homepage section + a `/map`
   layer/tab + a `/lookup` line that consumes `flood_control_accountability.json` via a
   client fetch (mirror the `road_flood_exposure.geojson` inline-script pattern in
   index.astro lines 75-116). Render aggregates ONLY (by_province / by_type / by_tranche)
   and the per-province conservative sentence: "₱{allocation} allocated to flood control
   in {province}; the recurrence model rates it modeled-prone and Sentinel-1 observed
   flooding on {n} dated passes here. Per DPWH/BetterGovPH records; warrants independent
   investigation." Show the file's `_meta.disclaimer` and `public_record_block` visibly
   near the result and in the footer. NEVER render a list of named flagged projects.
   Project-level detail only when a queried area resolves to a province in /lookup, using
   `flood_control_by_id.json` keyed lookup. If the JSON is absent at build (Phase 1 before
   WBD lands), the section must degrade to the honest in-progress roadmap line (graceful,
   like the existing `_meta` null guards) so the build never breaks.
7. **Plain-English / no-AI-fingerprint pass over ALL site copy.** Apply
   `~/.claude/rules/no-ai-jargon.md` as a hard ban. No em-dashes in user-visible strings
   (frontend rule). No "delve/leverage/seamless/robust/comprehensive/landscape/
   underscore/testament/realm/navigate(metaphor)/in today's/it's important to note", no
   helpfulness theater, no AI structures. Rewrite anything that reads like ChatGPT into
   Xavier's direct technical voice. This includes copy you are not otherwise changing.

## Constraints
- Astro static site. `pnpm typecheck` + `pnpm build` must pass (run them in `site/`).
- Conservative language everywhere; disclaimer + public-record block on the accountability
  surface. No efficacy/causality. No COA-337 figure. Never put "337" next to "ghost".
- Numbers come from `metrics.ts` / the fetched JSON `_meta`, never hardcoded prose
  (interpolate constants — data-integrity.md).
- Status -> `docs/plans/recenter/_wa-status.md` (list every file changed + the new H1 +
  the /map default + how the accountability section degrades when JSON absent).
</content>
