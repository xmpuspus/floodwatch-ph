# Agent 1 status — plain-language copy rewrite (v1.4.3)

Scope: entry pages + components, user-visible copy only. Glossary followed exactly.
Build: `pnpm install --frozen-lockfile && pnpm typecheck && pnpm build` all clean
(0 errors / 0 warnings / 0 hints, 9 pages built).

New homepage H1: **Predicted to flood, but barely on record.**
New core-term phrasing in the lead: "{N} Philippine provinces are predicted to
flood by the flood-prediction model (Track B), yet show few or no events in the
past flood records."

Verbatim DO-NOT-TOUCH strings verified byte-identical and untouched: destination
thesis, "warrants independent investigation", the standing footer line (3
instances), "Expressway watch" headline, the Block-3 PAGASA redirect,
`bagong.pagasa.dost.gov.ph`, the accountability disclaimer/`public_record_block`
(data-sourced). Lead-province branching logic in AccountabilitySurface unchanged
(only the prose words in the emitted sentences changed). All JSON/data enum
values, keys, code identifiers, filenames untouched. No em-dashes or banned words
introduced.

---

## site/src/pages/index.astro

- title: `FloodWatch.PH - where the model says it floods, but the record barely shows it` -> `FloodWatch.PH - predicted to flood, but barely on record`
- eyebrow: `FloodWatch.PH · the recurrence-vs-record gap` -> `FloodWatch.PH · predicted to flood, but barely on record`
- H1: `Where the model says it floods, but the record barely shows it.` -> `Predicted to flood, but barely on record.`
- lead para: `rated flood-prone by the recurrence model yet show few or no events in the historical observed record` -> `predicted to flood by the flood-prediction model (Track B), yet show few or no events in the past flood records`; `where does it repeatedly flood` -> `where does it flood again and again`
- card: `One repo, bit-exact, hash-verified. The recurrence model retrains` -> `One repo. Anyone can re-run it and get the identical result. The flood-prediction model retrains`
- card: `The pluvial and urban flooding Google Flood Hub` -> `The rain-driven city flooding Google Flood Hub`
- button: `Open the hazard-gap map` -> `Open the prediction-vs-record map`
- finding H2: `Modeled-prone, thinly recorded.` -> `Predicted to flood, but barely on record.`
- finding para: `flood repeatedly, yet the historical observed record is uneven ... provinces the recurrence model (Track B) rates flood-prone but that appear with few or no events in the historical observed record` -> `flood again and again, yet the past flood records are uneven ... provinces the flood-prediction model (Track B) predicts will flood but that appear with few or no events in the past flood records`
- para: `Exposure and the modeled-vs-observed gap are aggregated to province (FAO GAUL level-2, ~82 Philippine provinces)` -> `Who and what is exposed (people and built-up land) and the gap between what the model predicts and what past records show are summed to province (about 82 Philippine provinces)`
- stat labels: `under-observed prone` -> `predicted, barely on record`; `provinces modeled-prone, under-observed` -> `provinces predicted to flood, barely on record`; `recurrence model F1` -> `flood-prediction model F1`; `Track B, event-disjoint holdout` -> `Track B, tested by holding out whole storms`; `WorldPop province aggregate, Carina peak` -> `population data (WorldPop) province total, Carina peak`; `bit-exact, hash-verified` -> `anyone can re-run it and get the identical result`
- Track B card eyebrow: `Track B · recurrence model` -> `Track B · the flood-prediction model`; H2 `Which places flood repeatedly` -> `Which places flood again and again`; body `Google AlphaEarth satellite embeddings (64-dim, 2017 annual) plus a logistic regression head ... Event-disjoint holdout: entire typhoon events held out, never random pixels. Bit-exact, hash-verified, no GPU.` -> `A satellite fingerprint of the land (Google AlphaEarth, 2017 annual) plus a simple, well-understood classifier ... Tested by holding out whole storms, never random points. Anyone can re-run it and get the identical result, no GPU.`
- `Track B holdout F1:` -> `Track B held-out F1:` (value unchanged)
- Track A card eyebrow: `Track A · event track` -> `Track A · the single-storm flood map`; H2 `Observed flood extent from SAR` -> `The mapped flood area, from satellite`; body `Sentinel-1 C-band SAR penetrates typhoon cloud cover. Each slider frame is a real acquisition date. Otsu threshold on the VH change image, permanent-water mask applied.` -> `Sentinel-1 radar (it sees through typhoon clouds). Each slider frame is a real satellite pass date. An automatic cutoff with no hand-tuned settings, rivers and lakes removed.`
- Track A bare metrics line `Track A IoU vs GFD/CEMS (Koppu 2015): {M.trackA_iou} · F1: {M.trackA_f1}` -> REMOVED, replaced with `Validated against an independent 2015 flood map; the overlap is low and openly reported (see methodology).`
- `Track A and Track B metrics are reported separately ... The README never averages them.` -> `Track A and Track B results are reported separately ... We never average the two.`
- supporting demo H2: `The observed substrate: where the water actually went.` -> `The satellite data the model learns from: where the water actually went.`; body `the ungauged Super Typhoon Carina 2024 event ... no promptly-public official flood-extent polygon` -> `Super Typhoon Carina 2024 ... an event with no official measured record ... no promptly-public official flood map`; link `Open the hazard-gap map and the 2024 demonstration` -> `Open the prediction-vs-record map and the 2024 demonstration`
- "what you get" list: `Hazard gap: modeled-prone provinces under-observed in the historical record` -> `Prediction-vs-record gap: provinces predicted to flood, but barely on record`; `Track B recurrence model: which land signatures predict repeat flooding` -> `Track B (the flood-prediction model): which land predicts repeat flooding`; `SAR-derived flood extent: time-slider across the Carina 2024 acquisition dates` -> `Mapped flood area: time-slider across the Carina 2024 satellite pass dates`; `Province exposure: population, built-up area, peak flood share` -> `Who and what is exposed: population, built-up area, peak flood share by province`; `Permanent-water-masked: rivers and lakes removed, only flood reported` -> `Rivers and lakes removed: only flooding is reported`
- nav card: `one conservative sentence on the recurrence-vs-record gap there` -> `one conservative sentence on the gap between what the model predicts and what past records show there`
- methodology nav card: `Two-track architecture: Track B recurrence model (AlphaEarth embeddings + logistic regression, event-disjoint holdout), Track A SAR event detection (Otsu + permanent-water mask, parameter-free). Metrics reported separately, never averaged.` -> `Two tracks: Track B (the flood-prediction model: a satellite fingerprint of the land plus a simple, well-understood classifier, tested by holding out whole storms), Track A (the single-storm flood map: an automatic cutoff with no hand-tuned settings, rivers and lakes removed). Results reported separately, we never average the two.`

## site/src/pages/map.astro

- title description: `observed flood extent and the province hazard-gap layer: where the recurrence model and the historical observed record diverge` -> `mapped flood area and the province prediction-vs-record gap layer: where the flood-prediction model and the past flood records diverge`
- eyebrow: `hazard gap · observed flood extent` -> `prediction-vs-record gap · mapped flood area`
- intro para: `observed Sentinel-1 SAR flood extent ... with the province hazard-gap layer: where modeled flood-proneness diverges from the historical observed record` -> `mapped flood area from Sentinel-1 radar (it sees through typhoon clouds) ... with the province prediction-vs-record gap layer: where what the model predicts diverges from the past flood records`
- tab button: `Hazard gap + observed extent` -> `Prediction-vs-record gap + flood map`
- civic-view para: `Sentinel-1 acquisition dates ... a real SAR acquisition. Permanent rivers and lakes removed. ... exposure figures. The hazard-gap layer shows where modeled flood-proneness diverges from the historical observed record. Exposure and the modeled-vs-observed gap are aggregated to province (FAO GAUL level-2, ~82 Philippine provinces)` -> `Sentinel-1 satellite pass dates ... a real satellite pass. Rivers and lakes removed. ... see who and what is exposed. The prediction-vs-record gap layer shows where what the model predicts diverges from the past flood records. Who and what is exposed and the gap between prediction and record are summed to province (about 82 Philippine provinces)`
- Track A bare metrics line `Track A IoU vs GFD event 4300 (Koppu 2015 validation): {M.trackA_iou} · F1: {M.trackA_f1}. The validated method is applied to the ungauged Carina 2024 demonstration.` -> REMOVED, replaced with `Validated against an independent 2015 flood map; the overlap is low and openly reported (see methodology). The validated method is applied to the Carina 2024 demonstration, an event with no official measured record.`
- footer block: `Copernicus Sentinel-1 C-band SAR). Permanent-water mask applied: figures represent flood ... Exposure figures are province aggregates (WorldPop population, Microsoft GlobalML built-up area)` -> `Copernicus Sentinel-1 radar). Rivers and lakes removed: figures represent flooding ... Who and what is exposed (people and built-up land) is summed by province (population data from WorldPop, building footprints from Microsoft)`
- cite line: `SAR data: Copernicus/Sentinel-1, open. Province boundaries: FAO GAUL level-2, public.` -> `Radar data: Copernicus/Sentinel-1, open. Province boundaries: public.`
- removed now-unused `import { METRICS }` / `const M` (dead after IoU/F1 removal; produced a typecheck hint)

## site/src/components/AreaLookup.astro

- eyebrow: `recurrence-vs-record gap · Greater Metro Manila` -> `prediction-vs-record gap · Greater Metro Manila`
- H2: `Modeled-prone, or thinly recorded, or both?` -> `Predicted to flood, barely on record, or both?`
- evidence framing: `the Track B modeled recurrence-prone score (300 m grid, 2017 embedding), (2) the historical Global Flood Database record, and (3) observed Sentinel-1 SAR flood extent on its dated acquisition passes` -> `the Track B flood-prediction score (300 m grid, a satellite fingerprint of the land from 2017), (2) the past Global Flood Database record, and (3) the mapped flood area from Sentinel-1 radar (it sees through typhoon clouds) on its dated satellite passes`
- evidence row titles/subs: `Modeled flood-recurrence` / `AlphaEarth embedding model, calibrated · 300 m grid` -> `Predicted to flood (the model)` / `A satellite fingerprint of the land, calibrated so the score reads like a real probability · 300 m grid`; `Historical observed record` -> `Past flood records`; `Most recent Sentinel-1 SAR pass` -> `Most recent Sentinel-1 pass`; rainfall sub `GPM IMERG accumulation over prone areas` -> `Rain that has already fallen over predicted-flood areas`; roads sub `OSM expressway/major-road network ∩ latest observed SAR extent` -> `Expressway and major-road network crossed with the latest mapped flood area`

## site/src/components/CorridorWatch.astro

- gloss para: `the spine is the recurrence-vs-record gap.` -> `the main question is the gap between what the model predicts and what past records show.`
- scan reason: `no Sentinel-1 acquisition with enough area coverage` -> `no Sentinel-1 pass with enough area coverage`
- status strip: `Showing the observed Sentinel-1 SAR flood extent from the {date} pass ({n} polygons)` -> `Showing the mapped flood area from the {date} Sentinel-1 pass ({n} mapped areas)`
- expressway line: `so expressway exposure could not be computed` -> `so whether the expressways are flooded could not be computed`
- road popup label: `exposure: {value}` -> `status: {value}` (data value `p.exposure` enum untouched)
- GFM caption: `delivered within about 8 hours of acquisition ... a radar backscatter-low detection on that pass` -> `delivered within about 8 hours of the pass ... a radar detection on that pass`
- S1 caption fallback: `acquisition time unavailable` -> `satellite pass date unavailable`

## site/src/components/AccountabilitySurface.astro

- home roadmap para: `The recurrence-vs-record gap above is step 1 ... where the recurrence model rates the ground prone` -> `The gap between what the model predicts and what past records show above is step 1 ... where the flood-prediction model predicts the ground will flood`
- map roadmap para: `The hazard-gap view is the observed substrate ... and the recurrence model)` -> `The prediction-vs-record view is the satellite data the model learns from ... and the flood-prediction model)`
- lead-province emitted sentences: `the recurrence model rates it modeled-prone` -> `the flood-prediction model predicts it will flood`; `which the recurrence model rates modeled-prone` -> `which the flood-prediction model predicts will flood` (branching logic unchanged; "warrants independent investigation" byte-identical)
- renderHome body: `cross-reference the observed substrate ... where the recurrence model and Sentinel-1 still indicate flooding` -> `cross-reference the satellite data the model learns from ... where the flood-prediction model and Sentinel-1 still indicate flooding`
- renderMap body: `where the recurrence model and Sentinel-1 still indicate flooding` -> `where the flood-prediction model and Sentinel-1 still indicate flooding`

## site/src/components/NowView.astro

- No user-visible copy (re-exports CorridorWatch); unchanged.

## site/src/components/Header.astro

- nav label: `recurrence` -> `flood prediction` (href `/recurrence` unchanged)

## site/src/components/Footer.astro

- intro: `public SAR satellite data. Sentinel-1 C-band, permanent-water-masked, event-disjoint validated. Track A: event flood extent. Track B: recurrence-prone classifier.` -> `public satellite data. Sentinel-1 radar (it sees through typhoon clouds), rivers and lakes removed, tested by holding out whole storms. Track A: the single-storm flood map. Track B: the flood-prediction model.`
- "what this isn't": `the gap between observed recurrent flooding and official hazard-map coverage` -> `the gap between flooding that happens again and again and what official hazard maps cover`
- legal block: `(Copernicus Sentinel-1, Google AlphaEarth, Global Flood Database, MERIT Hydro, JRC Global Surface Water, WorldPop, Microsoft GlobalML Footprints, FAO GAUL level-2 boundaries) ... All exposure figures are province-level aggregates (FAO GAUL level-2, ~82 Philippine provinces ...)` -> `(Copernicus Sentinel-1, Google AlphaEarth, Global Flood Database, public terrain and surface-water datasets, population data from WorldPop, building footprints from Microsoft, public province boundaries) ... Who and what is exposed (people and built-up land) is summed by province (about 82 Philippine provinces ...)` (the exact sentence "Patterns may have legitimate explanations; figures warrant independent verification" kept byte-identical)

## site/src/data/metrics.ts

- No change. File contains only numeric/string data values and keys; no human-readable label strings.
