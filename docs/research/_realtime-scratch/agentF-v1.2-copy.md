# Agent F — v1.2 "Corridor watch" EXACT COPY SPEC (single source of truth)

Status: SIGNED-OFF SOURCE OF TRUTH. P1 (frontend) and P3 (docs) wire these
strings VERBATIM and edit nothing until this file is approved. Agent F edits
no `site/` or `docs/` source — this is the only file produced.

Register, enforced everywhere: observation-archive / past + present-perfect
("the pass observed", "what has been observed", "last seen on the {date}
pass"). Never "is flooding", "will/won't flood", "live", "now" as a standalone
status, no routing/safety instruction, no per-segment verdict. Passes the
no-AI-jargon ban and the civic-tech-ph conservative-language rule.

Placeholders below are interpolated by the frontend exactly as written:
`{frameUTC}` `{age}` `{acqDateUTC}` `{datetimeUTC}` `{dateUTC}` `{rebuiltUTC}`
`{attemptUTC}` `{freshLayer}` `{freshAcqUTC}`. Times are UTC, format
`YYYY-MM-DD HH:MM` unless a section says otherwise.

---

## 1. Headline + gloss (D1-A)

**Headline string (verbatim, exact):**

> Corridor watch

**Mandatory observation gloss subtitle (verbatim, always rendered immediately
under the headline, same visual block, never collapsible):**

> What the satellites and radar have observed over the expressways — the most
> recent observed passes, not a live feed and not a forecast.

**Supporting line (verbatim, extends the shipped NowView voice; rendered as the
question lead-in under the gloss, optional placement but text is fixed if used):**

> Did the latest satellite pass see water on the expressways?

**Rule statement (hard, non-negotiable):**

> The word "watch" never appears without its gloss in the same visual block.
> "Corridor watch" is never styled red, never given a pulsing / blinking /
> alert affordance, never an icon that reads as a siren or warning triangle.
> "Watch" here means an observation log, not a PAGASA-style advisory. If the
> gloss cannot render, the headline must fall back to plain text
> "Expressway observation log" rather than show "Corridor watch" bare.

---

## 2. Tier headers (D2-B) — KIND not priority

Three tier headers, each with a fixed one-line sub-caption stating what KIND of
observation it is (not its importance). Labels describe kind; they never imply
one tier is the answer or that lower tiers are stale/unimportant.

**Tier 1 header (verbatim):**

> Freshest observation

**Tier 1 sub-caption (verbatim):**

> Ground-radar rainfall, refreshed every few minutes. Shows where rain has
> most recently been falling, not where roads are flooded.

**Tier 2 header (verbatim):**

> Dated ground truth

**Tier 2 sub-caption (verbatim):**

> Radar satellite flood extent from the most recent usable passes. This is the
> observed-water layer; each pass is hours to days old by the time it lands.

**Tier 3 header (verbatim):**

> Supplementary, cloud-limited

**Tier 3 sub-caption (verbatim):**

> Optical satellite flat-water signal, off by default. Typhoon cloud usually
> blanks it; it never overrides the radar layer.

**Context flag (NOT a tier — the existing rainfall-accumulation flag keeps its
v1.1.0 role, rendered as a labeled context item, not promoted into a tier):**

> Rainfall accumulation context — dated, processed once a day. Context for the
> radar-revisit gap, not a score and not a forecast.

**Rule statement:** Tier headers are descriptive of kind only. No tier header
or sub-caption may say "primary", "main", "best", "most reliable", or "the
answer". Tier 2 (observed flood) keeps the v1.1.0 locked hero z-order —
rendered last / on top — regardless of its tier position in the list.

---

## 3. Per-layer honest labels (verbatim final strings)

Each is the complete caption string for that layer. `{placeholders}` are
interpolated by the frontend. No "live", no forecast verb anywhere.

### 3a. RainViewer rain radar (Tier 1)

> Rain radar: PAGASA national radar via RainViewer — last frame {frameUTC},
> updated {age} ago. Ground-radar observation, not a forecast. Source:
> RainViewer / PAGASA.

### 3b. Copernicus GFM faster-observed SAR (Tier 2)

> Faster observed SAR flood: Copernicus EMS Global Flood Monitoring, Sentinel-1
> pass {datetimeUTC}, delivered within about 8 hours of acquisition. 20 m,
> all-weather radar. Observed, not a forecast; blank where no recent Sentinel-1
> pass exists.

**GFM licence transparency note (SEPARATE one-liner, rendered directly beneath
the GFM caption — mandatory, verbatim):**

> Licence: Copernicus EMS / GFM Product User Manual, CC BY 4.0. The EODC STAC
> catalogue's `license: proprietary` field is a catalogue default, not the
> governing Copernicus EMS policy.

### 3c. NASA VIIRS NRT optical (Tier 3, default OFF)

> Supplementary observed flat-water signal: NASA LANCE VIIRS near-real-time
> flood, {dateUTC} one-day composite. Optical, about 250 m, cloud-limited —
> typhoon cloud often blanks it. Not the primary layer, not live, not a
> forecast.

### 3d. Existing Track A Sentinel-1 layer (Tier 2 — corrected revisit wording)

> Latest usable Sentinel-1 SAR pass: {acqDateUTC}. Sentinel-1A + Sentinel-1C,
> ~6-day revisit, ~24 h product latency. Dated ground truth — not live, not a
> forecast.

### 3e. Existing GPM rainfall-accumulation context flag (role unchanged — wording confirmed)

> Rainfall context: GPM IMERG accumulation as of {acqDateUTC} UTC. Satellite
> rainfall estimate, not a gauge reading and not a forecast.

(Confirmed: this is the shipped v1.1.0 string; role and wording unchanged in
v1.2. It stays a labeled context flag, not a tier.)

---

## 4. Freshness-clock wording (research §5; "now-ish" DROPPED per gate 4)

### 4a. Per-layer caption template (verbatim, ticking age recomputed every 30 s)

> {LAYER NAME}
> {ticking age} · acquired {acqDateUTC} UTC
> source: {source} · {latency class label}

Ticking-age strings (exact, client-recomputed every 30 s):
- `< 60 min` → `updated {n} min ago`
- `< 24 h`  → `updated {h} h {m} min ago`
- `< 7 d`   → `updated {n} days ago (last Sentinel-1 pass)`
- `>= 7 d`  → `last pass {n} days ago` + amber dot

Latency class labels (exact, one of): `nowcast` · `near-real-time` · `daily`
· `archival`. Per-layer specifics:
- RainViewer: `nowcast (~10-min source)`
- GFM SAR: `near-real-time (delivered within ~8 h of the pass)`
- Track A Sentinel-1: `daily build of the latest pass (~6-day revisit, ~24 h product latency)`
- VIIRS: `near-real-time (same-day, cloud-permitting)`
- GPM rainfall context: `daily (rainfall window, processed once a day)`

The word "now-ish" is DROPPED entirely (gate 4). No layer caption uses it. The
ticking relative age carries recency; no present-tense softener is added.

### 4b. Global ticker template (header/footer strip, verbatim)

> Freshest layer: {freshLayer} — updated {age} ago ({freshAcqUTC} UTC).
> Site rebuilt {rebuiltUTC} UTC. Layers refresh independently — see each
> layer's own clock.

`{freshLayer}` = the layer with the most recent acquisition time, recomputed
every 30 s. Names the layer and its absolute timestamp; never asserts
site-wide currency; never the word "live".

### 4c. Colour / urgency rule statement (hard)

> Default: neutral grey, no dot. The clock is informational, not a hazard
> signal. An amber dot appears ONLY when a layer is staler than its own
> expected cadence (Sentinel-1 > 12 days; RainViewer client fetch > 30 min;
> VIIRS > 48 h) and reads "this layer may be behind", never "flood danger".
> Never red. Never pulsing, blinking, or animated. FloodWatch is not an alert
> system; faux-urgency would be a false claim.

### 4d. Honest-empty strings (verbatim — never blank, never "just now")

Client-fetch failure, per layer (substitute the layer name and source):

- RainViewer:
  > Rain radar unavailable — could not reach RainViewer ({attemptUTC} UTC
  > attempt). Other layers unaffected.

- GFM SAR:
  > Faster observed SAR unavailable — could not reach the Copernicus GFM
  > catalogue ({attemptUTC} UTC attempt). Other layers unaffected.

- VIIRS:
  > Supplementary optical layer unavailable — could not reach NASA GIBS
  > ({attemptUTC} UTC attempt). Other layers unaffected.

Disabled toggle text when a client layer failed (verbatim):
> unavailable — see caption

Missing timestamp in any layer (verbatim — never "just now"):
> acquisition time unavailable

Existing cron honest-empty (UNCHANGED — reference, do not restate): the
v1.1.0 `_meta.scan_status` honest-empty path in `NowView.astro`
(`no_usable_pass` → "no Sentinel-1 acquisition with enough area coverage in
the lookback window", and the no-pass / degenerate / low-confidence messages)
is reused verbatim. v1.2 adds NO new wording to the cron layers' empty state.

---

## 5. The "~6-12 day" patch table (re-verified in THIS worktree)

Re-grep run in `/Users/xavier/Desktop/floodwatch-ph/.claude/worktrees/v1.2-corridor-watch`,
`site/dist/` excluded, the research correction-record files (this file,
`agentF-defensibility-v1.2.md`, `realtime-sources.md`, `copy-audit.md`)
excluded as they correctly quote the old value as stale.

Replacement strings:
- LONG form: `~6-day revisit (Sentinel-1A + Sentinel-1C, restored ~May 2025), ~24 h product latency`
- SHORT form (space-constrained captions/rows/inline): `~6-day revisit, ~24 h product latency`

| # | File | Line (re-verified) | Current text (exact) | Replacement | Form + why |
|---|---|---|---|---|---|
| 1 | site/src/components/FreshnessBanner.astro | 6 | `// OBSERVED satellite pass, lagged by the Sentinel-1 revisit (~6-12 days).` | `// OBSERVED satellite pass, lagged by the Sentinel-1 revisit (~6-day revisit, ~24 h product latency).` | SHORT — code comment, keep it one line |
| 2 | site/src/components/FreshnessBanner.astro | 105 | `` `(revisit ~6 to 12 days; this is the most recent observed pass, not live).`; `` | `` `(~6-day revisit, ~24 h product latency; this is the most recent observed pass, not live).`; `` | SHORT — runtime banner line, length-sensitive |
| 3 | site/src/components/FreshnessBanner.astro | 139 | `"Sentinel-1 revisit is ~6 to 12 days; this is observed satellite data for that window, not a live feed and not a forecast. " +` | `"Sentinel-1 has a ~6-day revisit (Sentinel-1A + Sentinel-1C, restored ~May 2025) with ~24 h product latency; this is observed satellite data for that window, not a live feed and not a forecast. " +` | LONG — detail/expander text, space available, this is the canonical explainer |
| 4 | site/src/components/NowView.astro | 43 | `Observed, lagged by the Sentinel-1 revisit (~6 to 12 days). Not a` | `Observed, lagged by the Sentinel-1 revisit (~6-day revisit, ~24 h product latency). Not a` | SHORT — inline callout, mid-sentence, keep compact |
| 5 | site/src/components/NowView.astro | 286 | `` `revisit is ~6 to 12 days and conditions change between passes.`; `` | `` `revisit is ~6 days with ~24 h product latency and conditions change between passes.`; `` | SHORT — runtime "no expressway flooded" line, length-sensitive |
| 6 | site/src/components/AreaLookup.astro | 300 | `"Observed, NOT live, ~6-12 day revisit",` | `"Observed, NOT live, ~6-day revisit, ~24 h product latency",` | SHORT — evidence-row value cell, tight column |
| 7 | site/src/lib/areaLookup.ts | 359 | `` ...no observation was possible. Sentinel-1 revisit is ~6-12 days.` `` | `` ...no observation was possible. Sentinel-1 has a ~6-day revisit with ~24 h product latency.` `` | SHORT — lookup detail string, sentence-final, keep tight |
| 8 | site/src/lib/areaLookup.ts | 371 | `...Observed, NOT live, NOT a forecast (revisit ~6-12 days).` | `...Observed, NOT live, NOT a forecast (~6-day revisit, ~24 h product latency).` | SHORT — parenthetical in a result line |
| 9 | site/src/pages/lookup.astro | 43 | `recent Sentinel-1 SAR pass (Copernicus, ~6-12 day revisit, observed not` | `recent Sentinel-1 SAR pass (Copernicus, ~6-day revisit, ~24 h product latency, observed not` | SHORT — parenthetical inside a prose enumeration |
| 10 | site/src/pages/index.astro | 101 | `...not an all-clear: the satellite revisit is about 6 to 12 days and conditions change between passes.` | `...not an all-clear: the satellite has a ~6-day revisit with ~24 h product latency and conditions change between passes.` | SHORT — runtime home corridor line, length-sensitive |
| 11 | site/src/pages/index.astro | 108 | `"Observed pass as of " + m.as_of + " (Sentinel-1 revisit ~6 to 12 days, not live).";` | `"Observed pass as of " + m.as_of + " (Sentinel-1 ~6-day revisit, ~24 h product latency, not live).";` | SHORT — as-of line, tight |
| 12 | README.md | 30 | `Sentinel-1 has a multi-day revisit (roughly 6 to 12 days); the Now view and every slider frame is a real past acquisition labeled with its as-of date, not a live feed.` | `Sentinel-1 has a ~6-day revisit (Sentinel-1A + Sentinel-1C, restored ~May 2025) with ~24 h product latency; the Now view and every slider frame is a real past acquisition labeled with its as-of date, not a live feed.` | LONG — README scope bullet, the canonical public statement, space available |
| 13 | docs/launch/linkedin-draft.md | 14 | `The layer is labeled the most recent satellite pass, revisit roughly 6 to 12 days, not a live feed.` | `The layer is labeled the most recent satellite pass, ~6-day revisit with ~24 h product latency, not a live feed.` | SHORT — social copy, keep the sentence tight (full refresh guidance in §9) |
| 14 (internal) | docs/ops/runbook.md | 19 | `Why daily: Sentinel-1 revisits the Philippines every ~6-12 days, so a new SAR` | `Why daily: Sentinel-1 revisits the Philippines about every 6 days (Sentinel-1A + Sentinel-1C, restored ~May 2025) with ~24 h product latency, so a new SAR` | LONG — internal ops note, cite the real cron reason fully |
| 15 (internal) | docs/research/SCHEMA-latest.md | 14 | `Sentinel-1 revisit over the Philippines is\n~6–12 days.` | `Sentinel-1 revisit over the Philippines is\n~6 days (Sentinel-1A + Sentinel-1C, restored ~May 2025), with ~24 h product latency.` | LONG — schema doc, canonical reference (note: en-dash `–` in current text, not hyphen) |

**Count: 13 public/shipped instances** (FreshnessBanner ×3, NowView ×2,
AreaLookup ×1, areaLookup.ts ×2, lookup.astro ×1, index.astro ×2, README ×1,
linkedin-draft ×1) **+ 2 internal docs** (runbook ×1, SCHEMA-latest ×1).
Matches the prior audit's count exactly. Line numbers: all 15 re-verified in
this worktree and all match the prior audit's numbers — no discrepancy.

**Mandatory post-patch re-grep (must return ZERO shipped/public instances):**

```
cd /Users/xavier/Desktop/floodwatch-ph/.claude/worktrees/v1.2-corridor-watch && \
grep -rn -E '6.{0,3}(to|–|-).{0,3}12 ?day|6-12 ?day|~6.{0,4}12|six.{0,4}twelve' \
  site/src/ README.md docs/launch/linkedin-draft.md docs/ops/runbook.md \
  docs/research/SCHEMA-latest.md \
  --include='*.astro' --include='*.ts' --include='*.md' 2>/dev/null \
  | grep -v 'site/dist/'
```

Expected output after patch: empty (zero lines). The research
correction-record files are not in the grep path, so they correctly retain the
old value as the "stale" record.

---

## 6. Guardrail-block placement (finalized — verbatim text + exact location)

All four blocks are confirmed present in the shipped surface and MUST be
carried, unmodified, onto the v1.2 corridor surface. Verbatim text below is the
shipped source of truth.

### Block 1 — Lookup-result header

**Verbatim:**

> This is **observed and modeled evidence as of dated satellite layers, not a
> forecast and not a safety instruction.** It does not say this area will or
> will not flood.

**Placement on v1.2:** At the top of every corridor lookup/result panel,
before any layer or evidence row. If the CorridorWatch surface has its own
result panel, it gets its own copy of this block. Unchanged.

### Block 2 — Evidence framing

**Verbatim (base, unchanged clause):**

> For the area you entered, FloodWatch shows: (1) observed Sentinel-1 SAR flood
> extent on its dated acquisition passes, (2) the Track B modeled
> recurrence-prone score (300 m grid, 2017 embedding), and (3) the historical
> Global Flood Database record. These are observations and a model, each
> as-of-dated. A thin record is not proof of safety; a high score is not a
> prediction.

**Corridor extension (verbatim, appended after item (3) and before "These are
observations" — names the new layers with their as-of class, keeps the
verbatim closing clause):**

> , (4) ground-radar rain via RainViewer on its latest frame (nowcast), and
> (5) Copernicus EMS GFM faster-observed Sentinel-1 flood extent on its most
> recent pass (near-real-time, delivered within ~8 h)

So the corridor evidence-framing block reads, in full: "For the area you
entered, FloodWatch shows: (1) … (2) … (3) the historical Global Flood
Database record, (4) ground-radar rain via RainViewer on its latest frame
(nowcast), and (5) Copernicus EMS GFM faster-observed Sentinel-1 flood extent
on its most recent pass (near-real-time, delivered within ~8 h). These are
observations and a model, each as-of-dated. A thin record is not proof of
safety; a high score is not a prediction."

**Placement on v1.2:** Wrapping the corridor's returned layers. The "A thin
record is not proof of safety; a high score is not a prediction." clause is
verbatim and never altered.

### Block 3 — Mandatory PAGASA/MMDA/DRRMO redirect (HARD GATE)

**Verbatim:**

> **Not a forecast.** For live conditions, warnings, and routing during an
> active flood, use PAGASA (bagong.pagasa.dost.gov.ph), MMDA Flood Control,
> and your LGU DRRMO. FloodWatch is complementary to and never a replacement
> for these and Project NOAH / Google Flood Hub.

**Placement on v1.2 (HARD GATE — non-negotiable):** Rendered VERBATIM on the
CorridorWatch surface itself, **co-located with the expressway visual** (in or
immediately adjacent to the same visual block that shows expressway segments /
the corridor map), exactly as `NowView.astro:43-52` already does it — not only
in the global FreshnessBanner. This is the single block that neutralizes the
routing-verdict misread (a commuter reading a red expressway segment as "don't
drive SLEX"). A corridor surface that shows an expressway segment without this
block adjacent to it is a SHIP-BLOCKING defect. Also repeated at the top of any
corridor result panel.

### Block 4 — Public-records disclaimer

**Verbatim:**

> Observed flood extent derived from public satellite data. Patterns may have
> legitimate explanations; figures warrant independent verification.

**Placement on v1.2:** Footer of the CorridorWatch surface and the footer of
any corridor result panel. Verbatim, the site's standard line.

**Additional hard gate (from §6 of the audit):** Every corridor layer carries
its own as-of clock (§4 of this file). A corridor surface that shows a red /
flooded expressway segment without an adjacent as-of date AND the Block 3
redirect is the single configuration that makes the routing-verdict misread
unrecoverable — treated as a hard ship gate.

---

## 7. Privacy-page copy for the +6 CSP origins

For `site/src/pages/privacy.astro`. Add under the "Telemetry, cookies,
analytics, and the area lookup" section (or a new adjacent paragraph). One
sentence per origin family; the "no information about what you searched"
reaffirmation is mandatory in each. The lookup-never-leaves-the-browser
invariant stays literally true (these are fixed all-PH map tiles; no user
input is ever in any of these requests).

**Lead sentence (verbatim):**

> The "Corridor watch" view loads a few map-tile layers directly from public
> meteorological and government sources. These requests carry no information
> about what you searched — every visitor's browser fetches the same fixed
> nationwide tiles, and the area lookup still runs entirely in your browser
> and is never transmitted.

**Per-origin sentences (verbatim, one per family):**

> - **RainViewer (api.rainviewer.com, *.rainviewer.com, tilecache.rainviewer.com):**
>   ground-radar rain tiles relayed from PAGASA. The request contains no
>   information about what you searched — the same map for every visitor.
> - **NASA GIBS (gibs.earthdata.nasa.gov):** NASA's near-real-time optical
>   flood imagery tiles. The request contains no information about what you
>   searched — the same map for every visitor.
> - **EODC STAC / titiler (stac.eodc.eu, titiler.services.eodc.eu):** the
>   Copernicus EMS Global Flood Monitoring satellite flood-extent tile index
>   and tile server. The request contains no information about what you
>   searched — the same map for every visitor.

**Closing reaffirmation (verbatim):**

> None of these layers receive, see, or could infer the place or route you
> looked up. The lookup stays in-browser; these are read-only map tiles,
> identical bytes for every visitor.

**Addition to the "What we don't publish" list (verbatim — append as a new
`<li>`):**

> Any new outbound user data via the Corridor watch layers. The added map-tile
> sources receive only fixed nationwide tile coordinates, never your lookup
> query.

---

## 8. GloFAS document-as-future sentence

For the methodology / SCHEMA doc. Verbatim, includes the riverine-only
exclusion drawn from `related-work.md` §1 (Google's own FAQ wording for the
riverine class FloodWatch deliberately does not surface):

> FloodWatch deliberately does not surface GloFAS or any riverine flood
> forecast. GloFAS is a riverine forecast product, and the floods that close
> SLEX/NLEX and inundate Metro Manila during a typhoon are overwhelmingly
> pluvial and compound-urban — the rainfall-driven class that riverine
> forecasting "covers only riverine floods, as opposed to flash/coastal
> floods" explicitly excludes (flash, coastal, urban, and pluvial floods are
> not covered). A forecast pixel on the corridor map would also blur the one
> distinction FloodWatch defends: it publishes observed extent after the water
> has been seen, and never forecasts. GloFAS is recorded here as a possible
> future external link, never a default layer and never parsed into any
> FloodWatch number.

---

## 9. CHANGELOG v1.2.0 + linkedin-draft angle

### 9a. CHANGELOG.md v1.2.0 entry (verbatim — paste under `## [Unreleased]`)

> ## [1.2.0] - 2026-05-17 - Corridor watch: tiered observation surface, faster radar layers
>
> v1.2.0 restructures the Now view into a "Corridor watch" — an observation
> log of what the satellites and radar have observed over the expressways,
> organized by how fresh each observation is rather than by importance.
> Everything stays observed and dated; nothing is a forecast and nothing is
> live. The public data chain stays 100% open with no paid dependencies and no
> new server, function, or proxy; the recurrence classifier sha256 is still
> b7c702532f92c43f and the permanent-water and event-disjoint CI gates are
> unchanged.
>
> ### Added
>
> - **Corridor watch surface.** A tiered view under the "Corridor watch"
>   headline and its observation gloss: freshest observation (ground-radar
>   rain), dated ground truth (the observed Sentinel-1 flood extent plus a
>   faster Copernicus GFM SAR layer), and a supplementary cloud-limited
>   optical layer that is off by default. Tier labels describe the kind of
>   observation, not its priority; the observed-flood layer keeps its hero
>   z-order.
> - **Three client-fetched layers.** RainViewer ground-radar rain (PAGASA
>   relay), Copernicus EMS GFM faster-observed Sentinel-1 flood extent via the
>   EODC STAC catalogue, and NASA LANCE VIIRS near-real-time optical flood
>   (default off). Each is fetched in the browser at view time against fixed
>   nationwide tiles — no cron, no server, and the lookup query still never
>   leaves the browser.
> - **Per-layer freshness clock.** Every layer carries its own ticking age,
>   acquisition timestamp, source, and latency class, plus a global ticker
>   that names the freshest layer and its absolute time. Neutral grey by
>   default; an amber dot only when a layer is staler than its own cadence;
>   never red, never pulsing. A failed fetch shows an honest unavailable state,
>   never a blank map and never "just now".
>
> ### Changed
>
> - **Sentinel-1 revisit figure corrected everywhere.** The earlier "~6 to 12
>   days" revisit figure was replaced with the accurate "~6-day revisit
>   (Sentinel-1A + Sentinel-1C, restored ~May 2025), ~24 h product latency"
>   across every public and shipped surface.
> - **Privacy page.** Documents the added Corridor watch tile sources and
>   reaffirms that none of them receive the lookup query.
>
> ### Notes
>
> - GloFAS and riverine forecasting remain deliberately out of scope and are
>   recorded as document-as-future; FloodWatch never forecasts.

### 9b. linkedin-draft refresh guidance (DO NOT POST — note for P3)

P3 refreshes `docs/launch/linkedin-draft.md` toward the corridor-watch +
freshness angle. **DO NOT POST — draft only, Xavier posts manually.** Bullets
(guidance, not verbatim copy):

- Lead with the observation-archive frame: "Corridor watch" is a log of what
  the satellites and radar have observed over the expressways — not a live
  feed, not a forecast. Do not write "live" or "now" as a status.
- Explain the tiering as the honest fact made structural: rain radar refreshes
  in minutes, the observed flood extent is hours-to-days old, the optical
  layer is cloud-limited and off by default — the UI shows that asymmetry
  instead of hiding it.
- State the public-chain / no-paid-deps / privacy invariant plainly: three new
  layers fetched in-browser from public government and meteorological sources,
  the lookup query still never leaves the browser.
- Carry the redirect verbatim in spirit: complementary to and never a
  replacement for PAGASA, MMDA Flood Control, LGU DRRMO, Project NOAH, Google
  Flood Hub.
- Fold in the corrected Sentinel-1 revisit figure (~6-day revisit, ~24 h
  product latency) — patch instance #13 in §5 applies here too.
- Keep zero superlatives (no first/only/best), no emoji, no AI-jargon, no
  routing or safety instruction.
