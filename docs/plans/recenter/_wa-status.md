# Agent-WA status — wave A narrative re-center + accountability surface UI + plain-English pass

Status: DONE. `pnpm install --frozen-lockfile && pnpm typecheck && pnpm build`
all green (0 errors, 0 warnings, 0 hints; 9 pages built).

## Files changed (site/** only — no Python/scripts/tests/.github/Makefile touched)

New:
- `site/src/components/AccountabilitySurface.astro` — the wave B payoff UI.
  Client-fetch of `/data/flood_control_accountability.json`, aggregates only,
  variants `home` / `map` / `lookup`, graceful degrade when JSON absent.

Modified:
- `site/src/pages/index.astro` — spine-first hero (new H1), P2/P3 stated on
  hero, destination thesis as in-progress roadmap line, extent demoted to a
  supporting section (D6), realtime collapsed to one labelled secondary
  context block, FreshnessBanner removed from the home lead, lookup promoted
  in the nav cards, accountability section added.
- `site/src/pages/map.astro` — default tab flipped to the hazard-gap /
  observed view; the realtime view is tab 2 labelled "Rainfall + expressway
  context (RainViewer / PAGASA)"; accountability `map` panel added under the
  Carina view; FreshnessBanner demoted (no longer the page lead).
- `site/src/components/FreshnessBanner.astro` — removed the "Freshest
  observation: rain radar via RainViewer" lead; rain is now rainfall context
  only, fully attributed, never the headline, never "freshest".
- `site/src/components/CorridorWatch.astro` — Tier-1 header relabelled from
  "Freshest observation" to "Rainfall context (RainViewer / PAGASA)"; gloss
  reframed as explicitly-secondary context; all 7 em-dashes removed.
- `site/src/components/AreaLookup.astro` — leads each result with one
  conservative synthesized sentence (`synthesizeGap`); evidence rows kept as
  the dated detail behind it; accountability `lookup` line embedded; heading
  reframed to the recurrence-vs-record gap.
- `site/src/components/Header.astro` — nav order: `area lookup` promoted to
  position 2 (immediately after home, before `the map`); `recurrence` moved
  ahead of `methodology`.
- `site/src/lib/areaLookup.ts` — added `synthesizeGap(EvidenceBundle)`: ONE
  conservative sentence from the recurrence + GFD layers ("modeled-prone +
  thin record = under-observed-prone; warrants verification"), never an
  accusation, never a forecast.
- `site/src/lib/freshnessClock.ts` — global ticker relabelled "Freshest
  layer:" -> "Most recent context layer:"; em-dashes removed from
  honest-empty / disabled-toggle / missing-timestamp strings.
- `site/src/pages/lookup.astro` — header reframed to the spine-as-a-tool.
- `site/src/pages/privacy.astro` — `&mdash;` removed (4); "Corridor watch"
  phrasing aligned to "rainfall and expressway context".
- `site/src/pages/methodology.astro` — `&mdash;` removed (1).
- `site/src/components/MapView.astro` — em-dashes removed (2, basemap caption
  + disabled-toggle text). No logic change; default-tab readiness preserved.

## Exact new homepage H1

`Where the model says it floods, but the record barely shows it.`

(Eyebrow: "FloodWatch.PH · the recurrence-vs-record gap". Hero body states
the {uncharted_count} provinces gap as step 1 of the accountability question,
P2 = single-repo bit-exact reproducibility ~30s no GPU, P3 = the pluvial /
urban class Google Flood Hub does not model. The destination thesis,
verbatim, is named as an in-progress roadmap line in AccountabilitySurface:
`Where flood-control money was spent, and where the water still came.`)

## New /map default

Default (visible at first paint, `aria-selected="true"`) =
`#panel-carina` — the **hazard-gap + observed flood-extent view** (the
Carina demonstration + the province hazard-gap layer). Button label:
"Hazard gap + observed extent". The realtime view (`#panel-now`,
NowView / Corridor watch) is tab 2, hidden at first paint, labelled
"Rainfall + expressway context (RainViewer / PAGASA)".

`window.__fwReady===true` on the default tab: MapView.astro's
`maybeInitCarina()` runs as soon as `#panel-carina` is not `.hidden`
(it is the default visible panel), and MapView sets
`window.__fwReady = true` on `map.once("idle")`. The inline switcher calls
`show(true)` on load (Carina visible), so the default tab paints and sets
the flag without the Now tab being activated. NowView stays lazy
(`data-now-active` flips only when the context tab is opened). Agent-WBI
should re-point qa_live's "default tab" assertion at the hazard-gap view
(`#view-carina` / `#panel-carina`), not the old Now view.

## How the accountability section degrades when the JSON is absent

`AccountabilitySurface.astro` never imports the JSON at build time — it is a
client `fetch("/data/flood_control_accountability.json")` only (mirrors the
existing `road_flood_exposure.geojson` `_meta` null-guard in index.astro).
`getAcct()` returns `null` when: fetch is non-ok (file absent), JSON is
malformed, or `_meta.disclaimer` is missing/blank (governance guard). On
`null` the client returns early and the **server-rendered roadmap copy
stands**: the verbatim thesis H2 plus the honest in-progress roadmap
paragraph ("the destination, stated as an in-progress roadmap line, not a
backed claim"). The build never breaks because nothing is imported; the
section is always present in HTML at first paint. When the JSON IS present
(it currently is — Agent-WBD landed `flood_control_accountability.json`,
44,983 projects, 82 by_province / 45 warrants_investigation / 5 by_tranche,
shape matches 10-wb-data-brief §3), the client replaces the roadmap body
with aggregates only (by_tranche table + one conservative per-province
sentence + the un-strippable `_meta.disclaimer` and `public_record_block`).
No named flagged-project list is ever rendered, on any variant.

## Constraint compliance

- "337" appears only as the `uncharted_count` token in `metrics.ts`,
  interpolated everywhere as `{M.uncharted_count}`; zero "ghost" anywhere
  in site/; "337" never adjacent to "ghost"/"confirmed".
- 0 em-dashes / `&mdash;` site-wide. 0 AI-fingerprint words.
- All numbers interpolated from `metrics.ts` or the fetched JSON `_meta`;
  no hardcoded prose figures.
- Disclaimer + public-record block rendered on every accountability surface
  (home / map / lookup) when the JSON is present; conservative
  "warrants independent investigation" language only; no efficacy/causality.
