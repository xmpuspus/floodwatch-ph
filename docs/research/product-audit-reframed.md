# Product audit — reframed lens — FloodWatch.PH

Date: 2026-05-17. Live: https://floodwatch-ph-five.vercel.app (v1.3.1).
Inputs: docs/research/skeptic-walkthrough.md, 23 screenshots in
docs/screenshots/skeptic/, docs/research/related-work.md §3 (yardstick),
memory: floodwatch-ph-weather-app-drift, floodwatch-honesty-vs-strategy-lesson.

This is NOT the standard polish/reliability/security sweep. Per the brief, code
quality and reliability are fine and out of scope. Each of the 8 dimensions is
re-cast through ONE disqualifying question:

> **Does this product have a defensible reason to exist distinct from a weather
> app, and is that reason FOREGROUND or BURIED under realtime rain + cinematic
> chrome?**

Score per dimension = **prominence of the recurrence-vs-record civic spine
relative to the rain/cinematic surface**, NOT capability. A capability that
exists but is buried scores low here by design — that is the whole point of the
audit.

§3 yardstick: the distinct contribution is a reproducible, permanent-water-
masked, single-repo PH pipeline surfacing the observed-extent + recurrence-vs-
historical-record gap, for the pluvial/urban class forecasters exclude and the
open-data gap hazard authorities leave. §3 explicitly says FloodWatch is NOT a
forecaster, warning system, hazard map, or weather surface.

---

## SCORES (prominence of the defensible spine, 0–100)

```
  UX (purpose legible in 10s?)          22/100   ▓▓░░░░░░░░
  Intelligence (is the smart thing      38/100   ▓▓▓▓░░░░░░
    showcased, or the rain clock?)
  Observability-of-purpose              28/100   ▓▓▓░░░░░░░
  Operational (reproducibility =        30/100   ▓▓▓░░░░░░░
    the §3 differentiator — visible?)
  Feature differentiation               24/100   ▓▓░░░░░░░░
    (vs RainViewer/Flood Hub/NOAH)
  ---
  Spine capability (does it EXIST?)     88/100   ▓▓▓▓▓▓▓▓▓░   (built, strong)
  Reliability / Perf / Code             ~85/100  (fine — out of scope, not scored)
  ---
  STRATEGIC PROMINENCE (weighted)       28/100   ▓▓▓░░░░░░░
```

Weighting: UX, Observability-of-purpose, Operational-prominence, and
Feature-differentiation carry the audit (1.5x). Spine-capability is reported
separately to make the core finding unmissable: **the spine is built well
(88) and surfaced badly (28).** This is not a quality problem. It is a
foregrounding problem. Exactly the [[floodwatch-honesty-vs-strategy-lesson]]
failure mode: every pixel honest, the thesis diluted.

The disqualifying question, answered in one line:
**Reason to exist: YES, real and well-built. Foreground: NO — buried under a
RainViewer-sourced rain banner and a null expressway table on the only two
pages a new visitor sees.**

---

## Per-dimension findings

### 1. UX — 22/100. Disqualifying.
- **[Critical]** `/` and `/map` both lead with: *"Freshest observation: rain
  radar … updated 10 min ago … PAGASA via RainViewer."* The first sentence of
  the product foregrounds the one signal it does not produce. Evidence:
  skeptic-walkthrough thesis (a); screenshots 01-home-sec1, 02-map-default.
- **[Critical]** `/map` default tab = "Now (latest observed pass)" = weather +
  10-row null Corridor watch. The civic hazard-gap layer is only on the
  **non-default** "2024 Carina demo" tab. The default route hides the spine.
- **[High]** Homepage spine ("Where the model says it floods, but the record
  barely shows it", 337 under-observed) is block 7 of ~10, ~68% scroll depth.
  Time-to-unique-value > 23s of deliberate scrolling. Fails the 10s test.
- Impact: a skeptic with RainViewer leaves in 10s having seen a rain map that
  admits it isn't live. The reason to exist never rendered.

### 2. Intelligence — 38/100.
- The genuinely smart artifact (Track B AlphaEarth + event-disjoint holdout,
  the gap classification `under_observed_prone`) is real and strong — but it is
  *documented* (/recurrence, /methodology, /faq), not *showcased*. Capability
  high; showcased-prominence low.
- **[High]** The most prominent "freshness/intelligence" signal on entry is a
  rain timestamp that is not FloodWatch's intelligence at all. The 337-province
  gap is a single faint stat tile, not the headline number.
- Impact: the product's smartest output reads as a footnote; an incumbent's
  data reads as the headline.

### 3. Observability-of-purpose — 28/100.
- Reframed from "can you debug it" to "can a visitor observe WHY this exists
  distinct from a weather app." The precise civic definition
  (`under_observed_prone` is not an allegation; gap = model vs GFD record) is
  only legible on `/faq` and `/safety` — terminal nav items.
- **[High]** On the surfaces seen first, the most observable fact is the rain
  clock. The civic finding is not observable without 4 nav hops or deep scroll.

### 4. Operational — 30/100 (reproducibility prominence).
- Reframed: single-repo bit-exact reproducibility is, per §3, the sharpest
  differentiator vs Copernicus GFM (institutional pipeline) and vs every closed
  forecaster. "Bit-exact, hash-verified, ~30s train, no GPU, SolarMap analog"
  is a strong, checkable, distinct claim.
- **[Critical]** It appears **only** on `/recurrence` (4 clicks deep). It is
  absent from `/` hero, `/map`, and the entry banner. The single most defensible
  thing about the project is invisible to a first-time visitor.

### 5. Feature differentiation vs incumbents — 24/100. Disqualifying.
- Mapped against the four incumbents the skeptic already uses:

  | Incumbent | FloodWatch's distinct value (§3) | Foregrounded on entry? |
  |---|---|---|
  | RainViewer | none on rain — RainViewer *is* the source | leads with it (worst) |
  | Google Flood Hub | observed pluvial/urban extent Hub excludes | not stated on `/` or `/map` |
  | NASA Worldview | reproducible single-repo, masked, recurrence | buried in /recurrence |
  | Project NOAH / PAGASA | open data where they are token-gated; recurrence-vs-record gap | "use them instead" stated 4x |
- **[Critical]** The product **leads with its weakest competitive ground**
  (rain, which RainViewer owns outright) and **buries its strongest** (recurrence
  -vs-record gap + reproducibility + the forecaster-excluded pluvial class). It
  competes where it loses and hides where it wins.

### 6–8. Reliability / Performance / Security-as-code — out of scope.
- Confirmed fine per brief. One reframed note: the client-side, never-
  transmitted lookup + RA 10173 province-only posture + CI PII gate is itself
  a *differentiator* (privacy-preserving reproducible civic tool), currently
  filed as a privacy disclosure on `/privacy` rather than promoted as part of
  the spine. Not a defect — an under-used asset.

---

## Cross-cutting themes

1. **The spine is built, not broken.** /methodology, /recurrence, /safety,
   /faq, /privacy, the /map Carina tab, and the /lookup evidence matrix already
   are exactly what §3 describes. No new capability is needed to be defensible.
2. **The dilution is 100% entry-surface and default-state.** Two pages (`/`,
   `/map`), one default tab, one global freshness banner, and scroll order are
   the entire problem. Five components, not a rebuild.
3. **The product leads with borrowed freshness.** "via RainViewer" / "via
   PAGASA" is the freshest, highest, first thing — attribution honesty turned
   into strategic self-sabotage. Honest, and wrong to foreground.
4. **The realtime feature's steady state is null.** Corridor watch = 10×
   "no overlap this pass." The realtime framing is empty most of the time *and*
   invites a commuter the copy then turns away.
5. **v1.3 cinematic basemap is off by default** — sunk cost, zero audience,
   safe to formally retire as a default concern.

---

## TOP 5 ACTIONS (impact/effort — re-centering, not features)

1. **Demote the rain banner from lead to context.** Replace the top "Freshest
   observation: rain radar via RainViewer" with a spine-first line (the
   recurrence-vs-record finding + reproducibility), rain moved to a labelled
   context strip lower down. Fixes findings in UX/Intelligence/Feature-diff.
   Effort: S (copy + component order).
2. **Make `/map` default to the civic view, not Now/weather.** Default tab =
   the hazard-gap/observed view; "Now (rain + expressway)" becomes the second,
   clearly-context tab. Fixes the worst Critical. Effort: S (tab default + copy).
3. **Promote the homepage spine above the fold.** "Where the model says it
   floods but the record barely shows it" + 337 + bit-exact reproducibility
   becomes the H1/hero; "where the water went" extent and rain demote below.
   Effort: M (hero rewrite + section reorder).
4. **State the gap as a finding, not rows to infer.** In `/lookup` and on the
   map, synthesize "modeled-prone + thin historical record →
   under-observed-prone" as one explicit, conservative sentence per result,
   instead of leaving the user to read it across two of five rows.
   Effort: M (synthesis line + conservative-language review).
5. **Formally retire the realtime/cinematic prominence.** Demote Corridor watch
   to a context module (not a headline), drop the cinematic basemap as a
   default concern, keep rain only as dated context. Less surface, sharper
   thesis. Effort: S–M (mostly deletion/demotion).

All five are demotions, reorders, and reframes. None adds a feature. This
matches the governing constraint: re-centre on the differentiator, which means
demoting recently-added surface, not adding more. Direction must be locked via
AskUserQuestion before any build (same gate discipline as the v1.2 wave).
