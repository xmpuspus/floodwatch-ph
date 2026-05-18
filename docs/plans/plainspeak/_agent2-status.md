# Agent 2 status — plain-language pass (reference + lookup pages)

Branch: fix/plain-language-pass
Build: clean. `pnpm install --frozen-lockfile` up to date, `pnpm typecheck` 0 errors / 0 warnings / 0 hints, `pnpm build` 9 pages built.
Jargon gate: zero residual `modeled-prone`, `recurrence-vs-record`, `under-observed` (prose), `hazard gap` label, `acquisition date`, `substrate`, `ungauged`, `civic-tech research artifact`, `publication boundary`, `legal posture` in the 7 owned files. Raw `IoU`/`F1` present ONLY in methodology.astro body (allowed). No em-dashes, no banned words.
Verbatim DO-NOT-TOUCH strings verified byte-identical: standing footer disclaimer (methodology/recurrence/safety), "warrant independent verification" closings (faq/privacy), RA 10173 §3(g) statutory quote (privacy). Code enum values (`under_observed_prone`, `charted`, `monitored`, `low`, `_meta.permanent_water_masked`, `gap`, filenames) left unchanged.

## site/src/pages/me.astro

- meta description: "open-source observed flood extent from Sentinel-1 SAR" -> "an open research project measuring where floodwater reached during Philippine typhoons from Sentinel-1 radar"
- "open-source project measuring observed flood extent ... modeled flood-prone yet under-observed in the historical record" -> "an open research project ... using Sentinel-1 radar (it sees through typhoon clouds) ... predicted to flood, but barely on record"
- "100% public-licensed inputs, reproducible pipeline, bit-exact model hash" -> "every input is public and openly licensed ... anyone can re-run it and get the identical result"
- heading "The two-track architecture" -> "Two tracks, two jobs"; Track A/B re-glossed: "Track A (the single-storm flood map)", "Track B (the flood-prediction model)"; "per acquisition date" -> "dated by the day the satellite passed over"; "ungauged Carina 2024" -> "Carina 2024 demo, which has no official measured record"; "Parameter-free (Otsu threshold)" -> "automatic cutoff with no hand-tuned settings"; "AlphaEarth 64-dim satellite embeddings" -> "satellite fingerprint of the land (Google AlphaEarth, 2017)"; "logistic regression head" -> "simple, well-understood classifier"; "Event-disjoint holdout" -> "tested by holding out whole storms, never random points"; "Platt-calibrated. Hash-verified." -> "calibrated so it reads like a real probability. Anyone can re-run it and get the identical result."
- heading "Civic thesis" -> "Why it exists"; "the recurrence model flags as flood-prone but ... few or no events in the historical observed record" -> "the model predicts will flood, but ... few or no floods in the past record"; "Exposure and the modeled-vs-observed gap are aggregated to province (FAO GAUL level-2 ...)" -> "Who and what is exposed (people and built-up land) and the gap between what the model predicts and what past records show are summed up by province"; "token-gated or SPA-only" -> "locked behind logins or apps"; "civic vacuum" -> "That gap is exactly what the demo fills"

## site/src/pages/faq.astro

- removed unused `METRICS`/`M` import (raw IoU/F1 no longer rendered)
- meta description: "privacy posture under RA 10173, the hazard gap layer, and the recurrence model" -> "how it complies with RA 10173 (the Data Privacy Act), the prediction-vs-record gap, and the flood-prediction model"
- Q "What is FloodWatch.PH?": "A civic-tech research artifact ... recurrence-prone classifier that flags communities that are modeled flood-prone yet under-observed" -> "An open research project ... a model that finds communities predicted to flood, but barely on record"
- Q "Why Sentinel-1 SAR ...": glossed "Sentinel-1 radar (it sees through typhoon clouds)", plain-language throughout
- Q "How accurate is the flood extent detection?" -> "How accurate is the single-storm flood map?": removed raw `IoU ${M.trackA_iou}` / `F1 ${M.trackA_f1}`, replaced with "The overlap with that independent map is low and openly reported (see methodology)"; "ungauged Carina 2024" -> "Carina 2024 demo, which has no official measured record"
- Q "How accurate is the recurrence model?" -> "How accurate is the flood-prediction model?": removed raw F1/precision/recall, points to methodology page; "event-disjoint holdout" -> "holding out whole storms, never random points"
- Q "What is the hazard gap layer?" -> "What is the prediction-vs-record gap?": "modeled flood-proneness ... historical observed record" -> "what the model predicts ... what past records show"; core finding -> "predicted to flood, but barely on record"; "token-gated or single-page apps" -> "locked behind logins or apps"
- Q personal info: "exposure figures ... province-level aggregates (FAO GAUL level-2)" -> "who and what is exposed (people and built-up land) ... summed up by province"; "WorldPop" -> "population data (WorldPop)"; "Microsoft GlobalML footprints" -> "building footprints (Microsoft)"; "CI gate scripts/check_no_pii.py" -> "An automated check"
- Q Carina demo: "civic vacuum", "ungauged" replaced with plain wording
- Q permanent-water mask -> "rivers and lakes removed"; mask datasets -> "public terrain and surface-water datasets"
- Q journalism: "permanent-water-masked" -> "rivers and lakes removed"
- Q official hazard map / affiliation: "modeled flood-proneness", "v1.1 refinement" -> plain "what the model predicts", "a later step"
- Q bug/contribution: "false-positive / false-negative reports on the hazard gap layer" -> "cases where the prediction-vs-record gap looks wrong"

## site/src/pages/safety.astro

- meta description and intro: "Satellite-observed flood data is powerful" -> "A satellite flood map is useful"; "what language is appropriate" -> "what language is fair"
- "What the data supports": "modeled flood-proneness against the historical observed record to identify under-observed-prone communities" -> "what the model predicts against what past records show, to find communities predicted to flood, but barely on record"; "hazard gap layer" -> "prediction-vs-record gap"; "Exposure ... aggregated to province (FAO GAUL level-2 ...)" -> "Who and what is exposed (people and built-up land) ... summed up by province"
- "What the data cannot support": "hazard gap is a measurement of divergence" -> "prediction-vs-record gap measures a difference"; "province-level aggregate" -> "summed up by province"; "forecast" wording kept plain
- appropriate-language box: "Observed flood extent, derived from Sentinel-1 SAR" -> "Flooding seen by Sentinel-1 radar (it sees through typhoon clouds)"; "Modeled flood-prone but under-observed in the historical record" -> "Predicted to flood, but barely on record"; "Province-level aggregate exposure estimate" -> "Province-level estimate of who and what is exposed"; "recurrent flooding" -> "repeated flooding"; "Warrants independent verification" left unchanged (DO-NOT-TOUCH-adjacent, already plain)
- citation block: "Copernicus Sentinel-1 SAR (permanent-water-masked)" -> "Copernicus Sentinel-1 radar, rivers and lakes removed"; disclaimer quote in following sentence left byte-identical
- LGU section: "provinces classified as `under_observed_prone` in the hazard gap layer (high modeled recurrence score, thin historical observed record)" -> "provinces in the prediction-vs-record gap that are predicted to flood, but barely on record"; `under_observed_prone` code token NOT used in prose; "field verification" -> "field check"
- journalists section: "hazard gap layer shows divergence between modeled flood-proneness (Track B) and the historical observed record" -> "prediction-vs-record gap compares what the model predicts (Track B) against what past records show"; "Track A IoU vs GFD ... Carina 2024 is ungauged" -> "Track A (the single-storm flood map) was checked against an independent 2015 flood map; the overlap is low and openly reported (see methodology). Carina 2024 has no official measured record"; "WorldPop" -> "population data (WorldPop)"; "province aggregate level" -> "summed up by province"

## site/src/pages/privacy.astro

- meta description: "the Philippines Data Privacy Act (RA 10173) posture" -> "how it complies with RA 10173 (the Data Privacy Act)"
- intro: "civic-tech research artifact ... aggregated to province counts only (FAO GAUL level-2 ...) ... publication boundary, the legal posture under RA 10173" -> "an open research project ... summed up by province only ... what we publish and what we don't, how it complies with RA 10173 (the Data Privacy Act of 2012)"
- "What we publish": "Province flood exposure aggregates" -> "Province totals for who and what is exposed (people and built-up land)"; "WorldPop" / "Microsoft GlobalML footprints" -> glossed; "peak flood share (max fraction ...)" -> "the worst flood share (the largest fraction ...)"; "Flood polygon GeoJSONs at the observed open-water extent level ... dwelling-level geometry" -> "The mapped flood area as map files at the level of open water seen by satellite ... home-level outlines"; "Hazard-gap classification per province: under_observed_prone / charted / monitored / low" -> "The prediction-vs-record bucket for each province" (enum values dropped from prose, kept in data); "Track B recurrence-prone sample-grid points ... building centroids ... dwelling identifiers" -> "Track B (the flood-prediction model) sample points ... not buildings ... No home identifiers"; "trained classifier, the committed embeddings cache, full reproducibility chain" -> "trained model, the cached satellite fingerprints of the land, and the full chain anyone needs to re-run it and get the identical result"
- "What we don't publish": "Per-household flood status geometry ... dwelling" -> "home-level flood-status shape ... house"; "Any PII property key ... CI gate scripts/check_no_pii.py" -> "Any personal-data field ... An automated check"; trailing "reverse-engineered" -> "worked back out"
- RA 10173 section heading: "Data Privacy Act (RA 10173) posture" -> "How it complies with RA 10173 (the Data Privacy Act)"; framing plain-languaged ("aggregated to province level (FAO GAUL level-2)" -> "summed up by province"); §3(g) statutory quote left BYTE-IDENTICAL; "hazard-gap classifications are institutional findings" -> "a prediction-vs-record bucket are findings about places"
- public-records framing: "WorldPop"/"Microsoft GlobalML Building Footprints"/"FAO GAUL level-2 province boundaries" -> glossed/"province boundaries"; "a v1.1 input" -> "a later input"
- lookup/telemetry: "is this area flood-prone?" -> "is this area predicted to flood?"; "bundled offline place-name index (a static gazetteer ...) ... in-browser point-in-polygon ... never transmitted" -> "place-name list shipped with the site ... checked ... on your device ... never sent"; RainViewer/GIBS/EODC tile entries unchanged (already plain)

## site/src/pages/lookup.astro

- meta description: "Offline, in-browser lookup ... Observed and modeled layers, each as-of-dated" -> "Look up dated flood evidence ... right in your browser ... Each layer is dated"
- eyebrow: "the recurrence-vs-record gap, as a tool" -> "the gap between what the model predicts and what past records show, as a tool"
- H1: "Is this place modeled-prone but thinly recorded?" -> "Is this place predicted to flood, but barely on record?"
- body: "states the recurrence-vs-record gap as one conservative sentence ... the modeled recurrence score, the historical observed record, the most recent observed satellite pass" -> "states the gap between what the model predicts and what past records show as one careful sentence ... what the flood-prediction model expects, what past records show, the most recent satellite pass"
- independence note: "reproducible, and is complementary to and never a replacement for" -> "anyone can re-run it and get the identical result. It works alongside ... and never replaces them"; "bundled offline place index" -> "place list shipped with the site"
- footer evidence: "Track B recurrence (AlphaEarth 2017 embedding, 300 m grid) ... Sentinel-1 SAR pass (... ~24 h product latency, observed not live), GPM IMERG rainfall accumulation context ... latest observed extent" -> "the flood-prediction model (Track B; a satellite fingerprint of the land from 2017, on a 300 m grid) ... Sentinel-1 radar (it sees through typhoon clouds) pass (... about 24 hours before the data is ready, seen by satellite not live), recent rainfall totals for context ... latest flood map"; standing disclaimer italic left byte-identical

## site/src/pages/methodology.astro (reference page — plain opening, glossed body)

NEW OPENING LINES:
- H1: "Two tracks, two jobs, two sets of numbers."
- "A flood is an event, not a fixed thing. One satellite photo cannot do the job: by the next clear photo the water is gone, and a regular camera satellite cannot see through the typhoon's own clouds anyway. So FloodWatch.PH uses two tracks with two different jobs."
- "Track A (the single-storm flood map) shows where floodwater reached during one specific typhoon. Track B (the flood-prediction model) learns which places flood again and again ... We never average the two." ("The README never averages them" -> "We never average the two")
- explicit signpost that body uses precise terms each glossed once

BODY (precise terms kept, each glossed first use):
- Sentinel-1 glossed "(it sees through typhoon clouds)"; processing steps -> "Radar processing steps. Standard cleanup (Refined-Lee speckle filtering, an industry-standard step that smooths the grainy noise ...; then a decibel conversion)"; backscatter glossed "(the amount of radar bounced back)"; "Otsu threshold (an automatic cutoff with no hand-tuned settings)" glossed; "acquisitions" -> "passes"; "permanent-water mask" -> "Rivers and lakes removed" with "public terrain and surface-water datasets (MERIT Hydro HAND ...; JRC Global Surface Water ...)"
- Track A check: IoU and F1 KEPT (methodology body) but glossed inline: "IoU (how much our map and the reference map overlap, as a fraction of their combined area)" and "F1 (a combined score balancing how much we catch against how much we over-call)"; "ungauged" -> "has no official measured record"; metric table rows unchanged ({M.trackA_iou}, {M.trackA_f1}, {M.trackB_f1} retained)
- Track B: "frozen embedding" -> "satellite fingerprint of the land"; AlphaEarth glossed "compact numeric summary of what each patch of land looks like from space"; "LogisticRegression" -> "a simple, well-understood classifier"; "Platt-sigmoid calibrated" -> "calibrated so the score reads like a real probability"; "bit-exact ... hash-verified" -> "anyone can re-run it and get the identical result"; "Event-disjoint holdout" -> "Tested by holding out whole storms" with leakage gloss
- civic layer heading "hazard gap (v1.0)" -> "the prediction-vs-record gap (v1.0)"; "Exposure ... aggregated to province (FAO GAUL level-2 ...)" -> "Who and what is exposed (people and built-up land) ... summed up by province*" with the ONE allowed footnote anchor; footnote added at page end: "* Province boundaries: FAO GAUL level-2, public."; core finding -> "predicted to flood, but barely on record"; enum values in <code> retained
- "Permanent-water masking (decision 2)" -> "Removing rivers and lakes (decision 2)"; HAND glossed "(height above the nearest river or drain)"
- "Honest limitations": "SAR at 10-20m" -> "At 10-20 m, the radar"; "pluvial and compound-urban" -> "rain-driven city flooding"; "observed extent" -> "flooding only after the water has been seen"
- "Reproducibility" -> "Anyone can re-run it"; "bit-exact" -> "anyone gets the identical result"
- data sources: Sentinel-1/AlphaEarth/WorldPop/Microsoft/FAO glossed; standing disclaimer italic (line 15) untouched

## site/src/pages/recurrence.astro (reference page — plain opening, glossed body, NO raw F1)

NEW OPENING LINES:
- eyebrow: "Track B · the flood-prediction model · v1"
- H1 kept: "Which places flood again and again."
- "Track A (the single-storm flood map) shows where the water went during one storm. Track B (the flood-prediction model) answers a different question: which places flood again and again, season after season?"
- "Like SolarMap, Track B is a trained classifier on a fixed satellite fingerprint of the land. Anyone can re-run it and get the identical result." + signpost that body glosses precise terms

BODY:
- "The embedding: Google AlphaEarth" -> "The satellite fingerprint of the land: Google AlphaEarth"; "frozen substrate" -> "the satellite data the model learns from"; AlphaEarth glossed; "64-dim unit-norm vectors" wording dropped to plain; "server-side on Earth Engine" -> "on Google's servers"
- "The classifier head" -> "The classifier"; "LogisticRegression ... Platt-sigmoid calibrated ... Deterministic" -> "a simple, well-understood classifier ... calibrated so the score reads like a real probability ... Anyone can re-run it and get the identical result"
- "Training labels" -> "Training examples"; Positives/Negatives -> "Flooded"/"Not flooded" examples; "permanent water removed"
- "Event-disjoint holdout" -> "Tested by holding out whole storms"; leakage explained plainly (removed raw "IoU and F1" mention here)
- "Track B metrics (event-disjoint holdout)" -> "How well it does": REMOVED raw `{M.trackB_f1}`/`{M.trackB_precision}`/`{M.trackB_recall}` rows; replaced with plain paragraph + table showing only "Tested by / Calibration / Model fingerprint ({M.clf_sha256}) / Cutoff in use ({M.trackB_threshold})", precision/recall now point to /methodology
- "What the output looks like": "FeatureCollection of Point features ... AOI ... deployed threshold ... building centroids" -> "points on a 300 m grid over the area ... cutoff in use ... not buildings"; "hazard-gap pipeline aggregates ... province level (FAO GAUL level-2 ...)" -> "gap pipeline sums Track B scores up by province"; enum values in <code> retained; "token-gated or SPA-only" -> "locked behind logins or apps"
- "What Track B does not claim": "2017 satellite embedding signature ... hydraulic model" -> "what its land looked like from space in 2017 ... not a water-flow model"; "Province-level aggregation ... individual-pixel claims" -> "Province-level summing ... single-point claims"; "average or combine their metrics" -> "their numbers"
- "Reproducibility" -> "Anyone can re-run it"; "deterministic ... reproduce" -> "give the identical result every time ... re-run"; standing disclaimer italic (line 15) untouched
