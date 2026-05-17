# Skeptic walkthrough — FloodWatch.PH live site

Date: 2026-05-17. Live: https://floodwatch-ph-five.vercel.app (main @ dc74651, v1.3.1).
Method: hostile-user walk of every page via /agent-browser. The skeptic already
uses RainViewer, Google Flood Hub PH, NASA Worldview, and Project NOAH.
Screenshots: docs/screenshots/skeptic/ (23 captures).

The one question asked at every screen: *Why would I use this instead of what I
already have? What here is just weather chrome? Where is the unique civic value,
and how many seconds until I see it?*

Yardstick (related-work.md §3): FloodWatch's stated distinct contribution is a
fully reproducible, permanent-water-masked, single-repo PH pipeline that surfaces
the **observed-extent + recurrence-vs-historical-record gap**, most useful where
the forecasting/hazard authorities don't model the flood type (pluvial/urban/
compound) or don't release open data. §3 says it is **not** a forecaster, **not**
a warning system, **not** a hazard map, **not** a realtime weather surface.

---

## The five skeptic theses — verdicts

**(a) "Banner + hero LEAD with rain radar = RainViewer with extra steps." — CONFIRMED.**
The literal first sentence of the site, on both `/` and `/map`, is:
*"Freshest observation: rain radar over the corridor, updated 9 min ago
(2026-05-17 17:40 PHT, PAGASA via RainViewer)."* The single most prominent,
freshest, top-of-page element on the two entry pages is rain radar, explicitly
sourced "via RainViewer." A user who has RainViewer reads this as RainViewer's
own data, restamped, then (two sentences later) is told to go to PAGASA anyway.
The freshest thing the product foregrounds is the one thing it does not produce.

**(b) "The recurrence-gap finding — the actual contribution — is a buried faint
tier." — CONFIRMED.** On the homepage the H1 is "Where the water actually went."
(extent) twice. The spine — "Where the model says it floods, but the record
barely shows it." (337 provinces modeled-prone, under-observed) — is the 7th
block, ~68% down the scroll (y≈2400 of 3527 px), in faint treatment, after two
heroes, the expressway "no overlap" card, the lookup card, and two metric cards.
The contribution that justifies the project's existence is below the fold,
below rain, below extent, below expressways.

**(c) "Corridor watch mostly says 'no overlap this pass'." — CONFIRMED, total.**
The default `/map` Now view Corridor watch reads: *"No monitored expressway
segments intersect the most recent observed flood extent (as of 2026-05-15)."*
followed by ten rows — SLEX, NLEX, Skyway, CAVITEX, NAIAX, CALAX, SCTEX, C5,
EDSA, Commonwealth — every one "no overlap this pass." The Sentinel-1 layer is
"updated 2 days ago." The only layer that moves is rain radar (RainViewer). So
the realtime *feeling* is 100% the RainViewer rain layer; the bespoke
expressway feature's steady state is a 10-row null table. RainViewer renders
the same rain better and without the empty table.

**(d) "The site tells commuters to go to PAGASA/MMDA anyway — so who is the
user?" — CONFIRMED, and unresolved.** The "Not a forecast — use PAGASA / MMDA /
LGU DRRMO" disclaimer appears on `/`, `/map` (top + Corridor watch note +
tabpanel), and in every `/lookup` result. The realtime/corridor framing courts
a commuter who wants "is my route flooding now"; the copy then correctly tells
that commuter this is not their tool. The realtime surface recruits a user it
must immediately turn away. The actual user (journalist / LGU planner /
researcher who wants the reproducible recurrence-vs-record gap) is served by
pages they have to dig for.

**(e) "The cinematic satellite basemap is dark/off-by-default — wow for whom."
— CONFIRMED (off-by-default).** Both the Now and 2024 Carina map views render
on a **light OpenStreetMap basemap** at default load and default zoom. The v1.3
"cinematic satellite-first" GIBS backdrop was not the default surface in any
state walked. Whatever wow the v1.3 cinematic wave added, the default visitor
never sees it — it is pure cost: build effort and conceptual surface that
serves neither the skeptic nor the spine. (Caveat: a basemap toggle was not
exhaustively hunted; the finding is about default state, which is what the 10s
test measures.)

---

## Per-page findings

### `/` Home — 23s+ to unique value. Diluted.
- First sentence = rain radar freshness "via RainViewer." Eyebrow + H1 ×2 =
  "Where the water actually went." (extent). The civic spine (recurrence-vs-
  record gap, 337 under-observed) is block 7 of ~10, ~68% scroll depth.
- Weather chrome: the top freshness region (rain), the "Was water seen on the
  expressways? — No..." card.
- Unique civic value present but late: the "what you get" list, Track A/B metric
  cards (IoU 0.054 / F1 0.955 honestly split), and the "Where the model says it
  floods, but the record barely shows it" section are all real and good — and
  all below the rain + extent + expressway fold.
- Skeptic's 10s verdict: "rain map that admits it isn't live and sends me to
  PAGASA." The reason to exist is not on screen in 10s.

### `/map` Now view — the worst offender for the thesis.
- Leads with the same rain banner. H1 "The flood map: what was observed, and
  when." Default tab = "Now (latest observed pass)". Default layer stack:
  Rain radar (RainViewer/PAGASA) checked, Observed flood extent (S1, "updated
  2 days ago") checked, Monitored expressways checked, GFM disabled/unavailable.
- Corridor watch = ten "no overlap this pass" rows (thesis c).
- Map canvas = light OSM basemap with RainViewer rain blobs over Metro Manila;
  no flood polygons (no overlap this pass). Visually indistinguishable from
  RainViewer with an empty overlay.
- The civic layer (hazard gap) is **not on this tab**. It lives only on the
  second tab.

### `/map` 2024 Carina demo tab — the spine, one click + one scroll away.
- Behind the non-default tab. Slider over real S1 acquisition dates
  (2024-07-10/22/30, 2024-08-03), play button, layers: Flood extent [checked],
  **Hazard gap layer [checked]**, Recurrence-prone overlay [unchecked].
- This is the strongest map surface — observed extent + the hazard-gap layer,
  validated method, honest "historical demonstration" framing. It is gated
  behind the Now/weather tab and the same leading rain banner.

### `/lookup` — the real product. Best-centered page on the site.
- The ONLY page that does not lead with the rain banner. Opens: "What dated
  flood evidence exists for a place or a route." Privacy/reproducibility framing
  up front ("runs in your browser ... never transmitted, logged, or
  republished").
- Query "Provident Village, Marikina" returns a 5-row evidence matrix:
  Modeled flood-recurrence (nearby, AlphaEarth 2017) · Historical observed
  record (intersects, GFD 2002-2017) · Most recent S1 pass (no overlap,
  2026-05-15) · Rainfall context (nearby) · Nearby monitored expressways (no
  overlap). Client-side, private, dated, caveated. This is the recurrence-vs-
  record cross-reference delivered per place — the §3 contribution, as a tool.
- Skeptic gap: even here the gap is *two adjacent rows among five*, not a
  synthesized finding. The signal "model says prone, record is thin →
  under-observed-prone" is left for the user to infer. 3 of 5 rows are the
  realtime/SAR null state. The spine is present but not stated; the weather/SAR
  nulls take equal visual weight.

### `/methodology` — spine, strong, honest. No rain.
- H1 "Two tracks, two jobs, two metrics." Otsu parameter-free, permanent-water
  CI gate, intentional SAR-only honesty. Reads as a real civic-tech method doc.
  This page already is what §3 describes. Nobody lands here first.

### `/recurrence` — spine, strong. No rain.
- H1 "Which places flood again and again." Bit-exact, hash-verified, "SolarMap
  analog," event-disjoint holdout, GFD 2002-2017 label honesty, "generalization
  to recent flooding is an open question surfaced, not hidden." This is the
  reproducibility differentiator stated plainly — and it is four nav clicks from
  the rain banner.

### `/safety` — spine framing, strong. No rain.
- "What the data supports / cannot support," appropriate vs inappropriate
  language, citation block. Exactly the journalist/LGU framing the real user
  needs. Buried in nav as "responsible use."

### `/faq` and `/privacy` — strong, civic, no rain.
- FAQ defines the hazard gap precisely ("under_observed_prone ... not an
  allegation"), Track A/B accuracy split, v1.1 deferrals stated honestly.
  Privacy: RA 10173 §3(g) posture, province-only aggregation, CI PII gate, DPO.
  Both are model civic-tech pages. Both are terminal nav items.

---

## Synthesis

The defensible spine **already exists and is well-built** — it lives in
`/methodology`, `/recurrence`, `/safety`, `/faq`, `/privacy`, the `/map` Carina
tab, and the `/lookup` evidence matrix. The drift is **not** that the spine is
missing or weak. The drift is **entirely in the entry surface**:

1. The two pages a first-time visitor and the nav default hit (`/` and `/map`)
   both **lead with rain radar sourced from RainViewer** — the one signal the
   project does not produce and an incumbent does better.
2. The map's **default tab is the weather/Now view**; the civic hazard-gap
   layer is on the **non-default tab**.
3. The spine on the homepage is **~68% scroll depth** behind rain + extent +
   a null expressway table.
4. The bespoke "Corridor watch" realtime feature's **steady state is a 10-row
   null**, which makes the realtime framing feel empty *and* makes RainViewer
   look better by comparison.
5. The v1.3 **cinematic basemap is off by default** — cost with no audience.
6. Even the best page (`/lookup`) presents the gap as **rows to infer from**,
   not as a stated civic finding, and gives weather/SAR nulls equal weight.

A skeptic with RainViewer + Flood Hub + Worldview + NOAH, in 10 seconds on the
entry pages, sees: a rain map that says it isn't live and tells them to use
PAGASA. They never reach the reason to exist. The honesty gate held (nothing
is overclaimed) and the dilution still happened — exactly the
[[floodwatch-honesty-vs-strategy-lesson]] failure mode. The fix is
**re-centering the entry surface on the spine and demoting realtime/rain to
context**, not adding features and not polishing what is already honest.
