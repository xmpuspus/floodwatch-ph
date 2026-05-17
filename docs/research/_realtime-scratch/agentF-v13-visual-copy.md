# Agent F — v1.3 CINEMATIC-VISUAL honesty + copy spec (single source of truth)

Status: SIGNED-OFF SOURCE OF TRUTH for the v1.3 "cinematic satellite-first"
wave. The frontend build (P1) and docs (P3) wire these strings VERBATIM and
edit no `site/` source until this file is approved. Agent F edits no `site/` or
other `docs/` source — this is the only file produced.

This file does NOT relax the v1.2 lock. It is additive. Everything in
`agentF-v1.2-copy.md` (the headline + gloss, the four guardrail blocks, the
tier headers, the per-layer labels, the freshness clock, the §5 patch table,
the privacy copy) stays in force VERBATIM. v1.3 only adds copy for the four new
*visual* surfaces (satellite basemap, SAR-as-raster, animated rain, satellite
hero) and the hard rules that keep showing real pixels from regressing the
posture.

Register, unchanged and enforced everywhere: observation-archive / past +
present-perfect ("the {date} pass observed", "what has been observed", "the
{date} mosaic"). Never "live", never "now" as a standalone status, never
"will/won't flood", no routing or safety instruction, no per-segment verdict,
zero superlatives (no first/only/best/most). Passes the no-AI-jargon ban and
the civic-tech-ph conservative-language rule.

Placeholders interpolated by the frontend exactly as written:
`{dateUTC}` `{datetimeUTC}` `{frameUTC}` `{firstFrameUTC}` `{lastFrameUTC}`
`{nFrames}` `{acqDateUTC}` `{age}`. Times are UTC, format `YYYY-MM-DD HH:MM`
unless a section says date-only (`YYYY-MM-DD`).

A new placeholder this wave introduces, with a HARD rule:
`{basemapDateUTC}` — the acquisition date of the active satellite basemap
mosaic. It is NEVER allowed to be empty, "today", "latest", or a relative
phrase. If the date cannot be resolved the basemap must not render as
true-color at all (fall back to the plain OSM basemap) — see §1 and §6.

---

## 1. Satellite basemap label + overclaim mitigation

The cinematic basemap is NASA GIBS true-color corrected-reflectance
(`VIIRS_SNPP_CorrectedReflectance_TrueColor`, or
`MODIS_Terra_CorrectedReflectance_TrueColor` as the documented fallback). This
is itself a DATED daily mosaic — one near-global pass per day, not a live or
continuous view. It carries its own acquisition date independently of every
data layer drawn on top of it.

### 1a. Persistent on-map basemap caption (verbatim, always visible when the satellite basemap is active)

Rendered in the existing bottom-right credit strip position (the
`absolute bottom-1 right-2` chip on CorridorWatch + MapView), on its own line
ABOVE the existing OSM/SAR/rain credit line, never collapsible, never
hover-only:

> Satellite basemap: NASA GIBS true-colour, {basemapDateUTC} — daily mosaic,
> one pass per day, not live.

### 1b. Cloud caveat (verbatim, mandatory one-liner, same chip, directly under 1a)

True-colour is optical and is the same class of data typhoon cloud blanks —
the exact reason SAR is the primary observed-water layer. This MUST be stated
wherever the true-colour basemap is offered:

> True-colour is optical: typhoon cloud often hides the ground on the very
> dates flooding matters. It is a backdrop, not the observed-water layer.

### 1c. Exact NASA GIBS attribution (verbatim, mandatory)

NASA GIBS imagery is US-government public domain but GIBS requests explicit
credit. Append to the existing credit chip's source line, so the full chip
reads (verbatim):

> Satellite basemap: NASA GIBS true-colour, {basemapDateUTC} — daily mosaic,
> one pass per day, not live. True-colour is optical: typhoon cloud often
> hides the ground on the very dates flooding matters. It is a backdrop, not
> the observed-water layer.
> © OpenStreetMap contributors. Satellite imagery courtesy NASA EOSDIS GIBS
> / Worldview / LANCE. SAR: Copernicus / Sentinel-1. Rain: RainViewer /
> PAGASA, NASA GPM IMERG. NRT optical: NASA GIBS.

(When the OSM basemap is active instead of satellite, the basemap line + cloud
caveat are removed and the credit reverts to the existing v1.2 chip text
unchanged. The "Satellite imagery courtesy NASA EOSDIS GIBS" clause appears
only while GIBS tiles are actually drawn.)

### 1d. Toggle / control label for the basemap (verbatim)

> Satellite backdrop (NASA GIBS true-colour, dated daily mosaic)

Default state decision (copy judgment call, see end of file): the satellite
backdrop is **OFF by default**; the map opens on the plain OSM basemap and the
visitor opts into the satellite backdrop. Rationale in §6 / §7.

### 1e. HARD rules (build, non-negotiable)

1. The basemap date `{basemapDateUTC}` is shown whenever the satellite
   basemap is active. No satellite basemap renders without its visible date in
   the same viewport.
2. `{basemapDateUTC}` is resolved from the GIBS `WMTSCapabilities.xml`
   (the same one-curl pattern v1.2 uses for VIIRS) — never the client clock,
   never the build time, never hardcoded.
3. If the date cannot be resolved, do NOT draw true-colour tiles. Fall back to
   the plain OSM basemap. A dated mosaic with no visible date is the single
   highest-risk regression in this wave (see §6).
4. The basemap is drawn at the BOTTOM of the layer stack, below every observed
   layer. It never tints, recolours, or sits above the SAR flood, the GFM
   layer, the roads, or the rainfall context. The locked z-order (context →
   roads → observed flood LAST/on top) is unchanged.
5. The word "live" never appears near the basemap. "Current", "real-time",
   "today's view" are banned for the basemap.

---

## 2. Sentinel-1 SAR shown as textured imagery

v1.3 may render the observed SAR/flood as an actual textured raster (the GFM
`dlr_flood_extent` COG via titiler, or the existing Track-A extent rasterised)
instead of a thin vector polygon. A filled, textured flood image reads more
literally than an outline — it must carry an explicit "this is a detection,
dated, not a photograph" frame. The v1.2 §3b / §3d label wording is reused
verbatim and is extended, not replaced.

### 2a. GFM faster-observed SAR as raster — caption (verbatim)

Reuses the v1.2 §3b string verbatim, with one appended sentence for the
raster rendering:

> Faster observed SAR flood: Copernicus EMS Global Flood Monitoring,
> Sentinel-1 pass {datetimeUTC}, delivered within about 8 hours of
> acquisition. 20 m, all-weather radar. Observed, not a forecast; blank where
> no recent Sentinel-1 pass exists. The shaded water is a radar
> backscatter-low detection on that pass, not a photograph of the flood.

The v1.2 GFM licence one-liner (Copernicus EMS / GFM PUM, CC BY 4.0; the EODC
STAC `license: proprietary` note) is rendered directly beneath, VERBATIM and
unchanged from v1.2 §3b.

### 2b. Track-A Sentinel-1 extent as raster — caption (verbatim)

Reuses the v1.2 §3d string verbatim, with one appended sentence:

> Latest usable Sentinel-1 SAR pass: {acqDateUTC}. Sentinel-1A + Sentinel-1C,
> ~6-day revisit, ~24 h product latency. Dated ground truth — not live, not a
> forecast. The shaded water is a SAR detection on that single pass, not a
> photograph and not a continuous view.

### 2c. HARD rules

1. The appended "detection, not a photograph" sentence is mandatory wherever
   the SAR is rendered as a filled/textured raster (it is NOT required where
   the SAR stays a thin outline — that is the v1.2 form and keeps the v1.2
   string unchanged).
2. The raster keeps the locked hero z-order: drawn LAST / on top of context
   and roads, exactly as the v1.2 vector did. Rasterising changes appearance
   only, never order, never the as-of clock, never the scan_status
   honest-empty path.
3. No SAR raster renders without its acquisition date in the same viewport
   (the per-layer freshness clock from v1.2 §4 already supplies this; it
   stays).
4. Banned near the SAR raster: "photo", "photograph", "image of the flood",
   "satellite photo", "what it looked like", "live", "current".

---

## 3. Animated rain playback

The loop animates RainViewer `radar.past` frames ONLY (observation). It never
touches `radar.nowcast` (forecast/extrapolation). The animation is observed
history replayed, never a prediction.

### 3a. Playback caption (verbatim, persistent under the rain control)

> Observed rain radar, last {nFrames} frames {firstFrameUTC} → {lastFrameUTC}
> UTC — PAGASA via RainViewer, ~10-min source, observed not a forecast.

### 3b. Per-frame timestamp readout (verbatim, updates every frame as it plays)

Rendered adjacent to the play control, always visible while playing AND while
paused (the current frame's own time, never blank, never relative):

> Frame {frameUTC} UTC — observed

### 3c. Play / pause control labels (verbatim)

- Idle / paused state label: `Play observed rain loop`
- Playing state label: `Pause`
- Static fallback (animation unsupported / single frame only): the control is
  hidden and the single-frame v1.2 RainViewer caption (§3a of the v1.2 spec)
  is shown unchanged.

### 3d. HARD rules (build, non-negotiable)

1. Only `radar.past` frames are ever loaded into the loop.
   `radar.nowcast` is never fetched, never appended, never interpolated for
   the animation. (FreshnessBanner already documents this invariant in code;
   it is restated here as a copy-spec gate.)
2. The animation never extrapolates. No frame is synthesised, tweened into a
   future position, or held in a way that implies "where the rain is going".
   Cross-fade between two real observed frames is allowed; inventing an
   intermediate "predicted" frame is banned.
3. The loop wraps from the last observed frame back to the FIRST observed
   frame with a visible reset — never a forward continuation past
   `{lastFrameUTC}`. The per-frame readout (§3b) must visibly jump backward
   on wrap so a viewer can never read the loop as time marching forward into a
   forecast.
4. The frame readout (§3b) shows the frame's own UTC time at all times,
   including the first paint and while paused. Never "just now", never
   relative-only, never blank.
5. The word "forecast", "nowcast", "predicted", "expected", "next" never
   appears anywhere on the rain animation surface. "Loop" and "playback" are
   acceptable; "forecast loop" / "prediction" are banned.
6. No autoplay during an obvious-storm read: the loop does not auto-start. The
   visitor presses play. (Copy judgment call, see end of file — an
   auto-running rain sweep is the strongest "this is a forecast" misread.)

---

## 4. Satellite hero (home)

The home hero may be a striking dated satellite/SAR flood image. The only
honest options are (a) the real DATED Sentinel-1 Carina 2024 observed extent
over Metro Manila, or (b) a dated GIBS true-colour mosaic of Metro Manila. It
is NEVER an undated, implied-current, or generic "satellite flood" hero.

### 4a. Hero overlay text — option (a), the Carina 2024 SAR observed extent (verbatim)

A persistent overlay on the hero image, not hover-only, not behind a click:

> 2024 demonstration — Super Typhoon Carina, observed Sentinel-1 SAR flood
> extent, Metro Manila, 24–25 July 2024. A dated historical observation, not
> current conditions and not a forecast.

### 4b. Hero overlay text — option (b), the dated GIBS true-colour mosaic (verbatim)

> Satellite backdrop: NASA GIBS true-colour mosaic of Metro Manila,
> {basemapDateUTC}. A dated daily mosaic, one pass per day — not live and not
> a forecast. The observed flood layers are in the Corridor watch.

### 4c. Hero CTA into the Corridor watch (verbatim)

> Open the Corridor watch — what the satellites and radar have observed over
> the expressways

(Links to `/map`. The CTA never says "see live", "check now", "current
conditions", or anything implying the destination is a live feed.)

### 4d. HARD rules

1. The hero overlay (4a or 4b) is rendered server-side as static text on the
   page, present at first paint with no JavaScript — it can never fail to
   render and leave a dramatic undated image bare.
2. Option (a) is preferred (the Carina extent is unambiguously a 2024
   demonstration and matches the existing FreshnessBanner `carina` variant
   wording). Option (b) is acceptable only if its `{basemapDateUTC}` is
   server-resolvable at build; if not, use option (a).
3. The hero never carries a date that is "today" or implied-current. The only
   dates allowed are the literal 2024 Carina acquisition dates (option a) or a
   resolved GIBS mosaic date (option b).
4. The existing `FreshnessBanner variant="site"` stays at the very top of the
   home page, ABOVE the hero, unchanged (it already leads with the freshest
   observed signal — the v1.2.1 freshest-first banner; see §5).
5. Banned on the hero: "live", "now" (as status), "current", "real-time",
   "happening", "today" (as the image date), any superlative.

---

## 5. Guardrail non-regression (placement after the cinematic redesign)

All four locked guardrail blocks and the freshness clock/ticker and the
v1.2.1 freshest-first banner remain present, VERBATIM, and correctly placed
after the redesign. The cinematic visuals must not push any of them below the
fold or let imagery visually overpower them.

### 5a. The four blocks — exact placement on the redesigned Corridor watch

- **Block 1 — Lookup-result header** (v1.2 §6 verbatim): top of every corridor
  lookup/result panel, before any layer or evidence row. Unchanged. The
  satellite basemap or SAR raster never renders above it inside a result
  panel.
- **Block 2 — Evidence framing** (v1.2 §6 verbatim, including the corridor
  (4)/(5) extension and the verbatim "A thin record is not proof of safety; a
  high score is not a prediction." closing clause): wrapping the corridor's
  returned layers. Unchanged.
- **Block 3 — Mandatory PAGASA/MMDA/DRRMO redirect (HARD GATE)** (v1.2 §6
  verbatim): rendered VERBATIM, co-located with the expressway visual, in or
  immediately adjacent to the SAME visual block that shows the corridor map /
  expressway segments. On the redesigned Corridor watch this is the block
  currently at `CorridorWatch.astro:65-75` — it MUST remain inside the same
  bordered card as the corridor visual, ABOVE the fold relative to that visual,
  and visually un-subordinated to the satellite basemap or any animation. A
  cinematic satellite map or rain loop that pushes Block 3 below the fold, or
  renders it visually weaker than the imagery, is a SHIP-BLOCKING defect. The
  redirect card's coral hairline border (`border-accent-coral/40`) is the
  maximum emphasis allowed — it is never restyled to compete with the imagery
  by going brighter, and never weakened to a faint caption to "not break the
  cinematic mood".
- **Block 4 — Public-records disclaimer** (v1.2 §6 verbatim): footer of the
  CorridorWatch surface and footer of any corridor result panel. Unchanged.
  Remains plain text, never overlaid on imagery where the image could reduce
  its legibility.

### 5b. Freshness clock + global ticker

The per-layer freshness clock (v1.2 §4a) and the global ticker (v1.2 §4b)
remain present and unchanged on the redesigned Corridor watch, in their v1.2
positions (the ticker strip near the top, each layer's clock under its
toggle). The new satellite basemap gets its OWN dated caption (§1) — it does
NOT borrow another layer's clock and is NOT counted as the "freshest layer" in
the global ticker (a daily mosaic must never be named the freshest observed
signal). The §4c colour/urgency rule (neutral grey default, amber only when a
layer is staler than its own cadence, never red, never pulsing) is unchanged
and now also governs the basemap date chip (neutral, informational).

### 5c. v1.2.1 freshest-first banner

The `FreshnessBanner` (v1.2.1 — leads with the freshest observed signal, rain
radar over the corridor with its UTC time, falling back honestly when rain did
not resolve) remains present and unchanged on the home page (`variant="site"`,
top, above the hero) and on the map page (`variant="now"` / `"carina"`). The
cinematic hero is rendered BELOW the site banner, never replacing it and never
above it. Its embedded Block-3 redirect paragraph (`FreshnessBanner.astro:42-48`)
stays verbatim.

### 5d. HARD GATE restated

A corridor surface that shows a textured SAR flood raster or a true-colour
satellite basemap or an animated rain loop, without (i) the Block 3 redirect
co-located and visually un-subordinated, (ii) each observed layer's as-of date
visible in the same viewport, and (iii) the basemap's own date visible while
it is active — is the configuration that makes the routing-verdict /
live-feed misread unrecoverable. Treated as a hard ship gate.

---

## 6. The cinematic overclaim sweep (futureproof)

Every NEW way the cinematic visuals can imply live / current / forecast /
safe-to-drive that the v1.2 text version did not. Each has a mandatory
mitigation that is a hard build rule. **12 findings. Ranked; F1 is the single
highest risk.**

| # | New overclaim vector (introduced by cinematic visuals) | Why the text version did not have it | Mandatory mitigation (HARD build rule) |
|---|---|---|---|
| **F1** | **True-colour satellite basemap with no visible date reads as a live/current satellite view.** A glowing photographic Earth backdrop is the single strongest "this is happening now" signal a non-technical visitor can receive — far stronger than a text grid. | v1.2 had a flat OSM basemap; no one mistakes road tiles for a live satellite. | §1e rules 1–3 ENFORCED: `{basemapDateUTC}` visible whenever satellite is active; resolved from GIBS capabilities, never the clock; **if the date cannot resolve, true-colour does not render at all (fall back to OSM)**. Plus §1d: satellite backdrop is OFF by default. This is the highest-risk item — a dated mosaic with no date is indistinguishable from a live feed. |
| **F2** | **Smooth rain animation reads as a forecast loop** ("watch the rain move → where it's going"). | v1.2 showed one static rain frame; a single frame cannot imply motion-into-the-future. | §3d rules 1–6 ENFORCED: `radar.past` only; never `radar.nowcast`; no extrapolation/synthetic frames; visible backward reset on wrap; per-frame UTC readout always shown; no autoplay. The word "forecast/nowcast/predicted/next" banned on the surface. |
| **F3** | **Dramatic satellite/SAR hero with no "2024 demo" label reads as current flooding.** | v1.2 home had text + a freshness banner, no dramatic flood image. | §4d rules 1–3 ENFORCED: server-rendered static overlay present at first paint (4a or 4b verbatim); option (a) Carina-2024 preferred; only literal 2024 dates or a resolved GIBS date allowed; never implied-current. |
| **F4** | **Textured/filled SAR flood raster reads as a literal photograph of "the flood right now".** A filled glowing water mass looks like a camera image; an outline reads as analysis. | v1.2 SAR was a thin vector polygon — visibly an analytical overlay. | §2c rules 1–4 ENFORCED: mandatory appended "the shaded water is a SAR detection on that pass, not a photograph" sentence wherever SAR is a filled raster; "photo/photograph/image of the flood" banned. |
| **F5** | **Satellite imagery anywhere implies continuous real-time monitoring of the corridor.** Pixels feel "watched"; vectors feel "computed". | A text grid of expressway names never implied a satellite is watching the road. | §1a + §2a/2b captions state "one pass per day" / "single pass" / "not a continuous view" verbatim. The v1.2 gloss ("the most recent observed passes, not a live feed and not a forecast") stays in the same visual block as the headline (v1.2 §1, unchanged). |
| **F6** | **A cinematic basemap makes a flooded-looking expressway segment read as a real-time "don't drive SLEX" verdict** — the imagery amplifies the routing-verdict misread the text version already guarded. | The misread existed in v1.2 but a flat map made it weaker. | Block 3 redirect co-located + visually un-subordinated to the imagery (§5a, HARD GATE). Per-segment as-of date visible (§5d). No per-segment verdict copy anywhere (v1.2 register, unchanged). |
| **F7** | **The satellite basemap's date gets visually lost behind the cinematic imagery** (small grey text on a busy photographic background = effectively no date). | v1.2 credit text sat on a plain light map; always legible. | The basemap caption (§1a/1b) renders in the existing solid `bg-white/85` credit chip (never directly on the photographic tiles), at the existing chip font size or larger, never lower-contrast than the existing OSM credit. Legibility of the date is a build-acceptance check, not best-effort. |
| **F8** | **GIBS true-colour during a typhoon shows cloud, not flood — a viewer reads "no flood visible = roads are clear".** Showing an optical backdrop on exactly the cloudy dates flooding matters invites an all-clear misread. | v1.2 never offered an optical backdrop. | §1b cloud caveat MANDATORY and verbatim wherever the true-colour basemap is offered. The basemap is explicitly "a backdrop, not the observed-water layer". The existing v1.2 "not a clear-conditions signal" scan_status strings stay unchanged. |
| **F9** | **Animated rain auto-playing on load reads as an active alert / something is happening now.** Motion on load = urgency. | v1.2 had no motion. | §3d rule 6: no autoplay. The loop is visitor-initiated. Motion never starts itself. |
| **F10** | **A cinematic hero CTA ("see it live", "check now") implies the destination is a live feed.** | v1.2 CTAs were plain ("Open the Now view"). | §4c CTA verbatim ("Open the Corridor watch — what the satellites and radar have observed over the expressways"); "live/now/current" banned in all hero CTA copy. The existing home expressway-callout copy (index.astro) keeps its v1.2 wording. |
| **F11** | **The hero or basemap visually overpowers the FreshnessBanner / Block 3, so the honest framing is present but ignored.** Cinematic weight beats text weight. | v1.2's strongest visual was a flat map; the banner held its own. | §5a/§5c: FreshnessBanner stays at the very top above the hero; Block 3 keeps its bordered card and is never weakened to "preserve the mood"; imagery never rendered above a guardrail block within a result panel. Visual-subordination of any guardrail to imagery is a ship-blocking defect. |
| **F12** | **Rasterising the SAR loses the per-pass as-of date that the vector layer's clock carried, because the image "looks complete on its own".** | v1.2 vector always sat next to its freshness clock; rasterising can tempt a "clean image, no chrome" treatment. | §2c rule 3 + §5d: no SAR raster renders without its acquisition date in the same viewport; the v1.2 §4 per-layer clock stays attached to the rasterised layer exactly as it was to the vector. |

**Highest-risk finding: F1** — a true-colour satellite basemap rendered with
no visible acquisition date is visually indistinguishable from a live satellite
feed and is the single change in this wave most able to make a non-technical
visitor believe FloodWatch shows current conditions. Mitigation is
non-negotiable and fail-safe: the date is resolved from GIBS capabilities and
shown whenever satellite is active, the backdrop is off by default, and **if
the date cannot be resolved the true-colour basemap does not render at all** —
it degrades to the plain OSM basemap rather than ever showing an undated
photographic Earth.

---

## 7. Colour / cinematic honesty rule

Cinematic ≠ alarmist. The wow is allowed to be dark, deep, and to show the
motion of OBSERVED data. It is never allowed to look like an alert, a forecast
sweep, or an undated glow.

### 7a. The honest visual register for "wow" (allowed)

- Dark / satellite-toned basemap, depth, and contrast — visual richness from
  real dated imagery, not from invented urgency.
- Motion ONLY of observed history: the RainViewer `radar.past` loop and the
  existing Carina time-slider cross-fade (both are replays of dated
  observations, both already visitor-controlled).
- The observed SAR water rendered as a textured, dated detection layer, on
  top, with its as-of date adjacent.
- A striking but explicitly dated hero.

### 7b. Banned (a false claim, ship-blocking)

- Red / pulsing / blinking / flashing hazard styling on any element. The v1.2
  §4c rule stands: neutral grey default, amber dot only when a layer is
  staler than its own cadence, never red, never animated. FloodWatch is not
  an alert system.
- A predictive sweep: any animation that moves rain or water forward past the
  last observed frame, or a "radar nowcast" loop. Observed history only,
  with a visible backward reset on wrap.
- An undated glow: any photographic / satellite / SAR imagery rendered without
  its acquisition date visible in the same viewport.
- Siren, warning-triangle, or alert iconography anywhere. "Corridor watch" is
  never styled red and never given an alert affordance (v1.2 §1 rule,
  unchanged).
- "Cinematic urgency" copy: dramatic ≠ urgent. No "happening now", "active
  flood here", "alert", "warning" framing on any FloodWatch-authored element.
  The freshness clock and the basemap date chip stay strictly informational.

### 7c. One-line restatement

Make it striking with dark satellite tone, depth, and the motion of dated
observed data — never with red, never with a forward/predictive sweep, never
with an undated photographic glow. Drama comes from real dated pixels, not
from faux-alert styling.

---

## Copy judgment calls made (not pre-decided by the lock)

1. **Satellite backdrop OFF by default** (§1d/§1e/§6 F1). The lock required a
   visible basemap date and an honest caveat but did not state the default
   on/off state. Judgment: a glowing true-colour Earth is the strongest
   live-feed misread in the wave (F1); defaulting it OFF, with the visitor
   opting in, keeps the first-paint surface unambiguous while still making the
   cinematic view one click away. The map opens on plain OSM.
2. **Rain loop does not autoplay** (§3c/§3d rule 6 / §6 F9). The lock required
   no extrapolation and a per-frame UTC readout but did not state autoplay
   behaviour. Judgment: motion on load reads as "something is happening now";
   the loop is visitor-initiated, matching the existing visitor-controlled
   Carina slider.
3. **Hero option (a) — Carina 2024 SAR — preferred over (b)** (§4d rule 2).
   The lock offered both as honest. Judgment: the Carina 2024 extent is
   unambiguously a dated historical demonstration, already has matching
   approved FreshnessBanner `carina` wording, and does not depend on a
   build-time GIBS date resolving; option (b) is the fallback only.
4. **Spelling "true-colour"** (UK spelling) used consistently to match the
   existing site copy register elsewhere in the v1.2 spec; the frontend may
   normalise to "true-color" if the rest of `site/` uses US spelling — meaning
   is unaffected, the date/caveat rules are spelling-independent.
5. **"NASA GIBS true-colour basemap" is a NEW source not in the v1.2 research
   matrix** (which only covered GIBS VIIRS *flood*, not the CorrectedReflectance
   true-colour basemap). It is NASA EOSDIS, US-gov public domain, same
   `gibs.earthdata.nasa.gov` CSP origin already approved in v1.2 — so no new
   CSP origin and no new privacy-page sentence is required. The attribution in
   §1c follows NASA EOSDIS GIBS standard citation guidance ("imagery courtesy
   NASA EOSDIS GIBS"); flagged here so P3 records it rather than assuming it
   was pre-cleared.
