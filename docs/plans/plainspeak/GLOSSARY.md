# Plain-language glossary — single source of truth (v1.4.3)

Audience: Filipino citizens, journalists, LGU staff. Not engineers, not GIS people.
Rule: if a normal person reading the news would not instantly understand a word,
it does not belong in user-visible copy. Replace EXACTLY as below, every page,
identically. Adapt grammar to the sentence but keep the wording consistent.

## Core product vocabulary (most important — must read identically everywhere)

| Current jargon | Plain replacement |
|---|---|
| modeled-prone / modeled flood-prone / modeled flood-proneness | predicted to flood |
| recurrence-prone / flags as flood-prone (model sense) | predicted to flood repeatedly |
| the recurrence-vs-record gap | the gap between what the model predicts and what past records show |
| under-observed / under-observed-prone (visible text) | barely on record |
| "modeled-prone but under-observed" (the core finding) | predicted to flood, but barely on record |
| hazard gap / hazard-gap layer (visible label) | prediction-vs-record gap |
| the recurrence model / Track B recurrence model | the flood-prediction model (Track B) |
| Track A / Track B (keep label, always gloss on first use per page) | Track A (the single-storm flood map) / Track B (the flood-prediction model) |

## Remote-sensing / data jargon

| Current | Plain |
|---|---|
| acquisition date / SAR acquisition | satellite pass date / the date the satellite passed over |
| inundation | flooding |
| into recession / flood recession | as the water drained |
| the observed substrate / the frozen substrate | the satellite data the model learns from |
| ungauged (event) | with no official measured record |
| permanent-water mask / permanent-water-masked (visible prose) | rivers and lakes removed |
| exposure / exposure figures / flood exposure aggregates | who and what is exposed (people and built-up land) |
| FAO GAUL level-2 (every inline use) | province (drop the code inline; one footnote on /methodology only: "Province boundaries: FAO GAUL level-2, public.") |
| polygon / flood polygons / GeoJSON / FeatureCollection (visible prose) | the mapped flood area / the flood map |
| embedding / 64-dim / frozen embeddings | a satellite fingerprint of the land |
| Platt-sigmoid calibrated / Platt-calibrated | calibrated so the score reads like a real probability |
| logistic regression head / classifier head / sklearn... | a simple, well-understood classifier |
| Otsu threshold / Otsu thresholding | an automatic cutoff with no hand-tuned settings |
| speckle filtering / Refined-Lee / dB conversion / backscatter / VV / VH / IW mode | (methodology body only; on entry/faq/recurrence-intro say) radar processing steps |
| bit-exact / hash-verified / deterministic / make hash-verify (entry/faq/me) | anyone can re-run it and get the identical result |
| pluvial / compound-urban | rain-driven city flooding |
| civic-tech research artifact | an open research project |
| publication boundary | what we publish and what we don't |
| legal posture under RA 10173 | how it complies with RA 10173 (the Data Privacy Act) |
| the README never averages them | we never average the two |
| event-disjoint holdout (entry/faq/me; keep in methodology body w/ plain lead) | tested by holding out whole storms, never random points |

## Acronyms — expand on first use per page, then the acronym is fine

- DRRMO -> "your city or municipal disaster office (DRRMO)"
- Sentinel-1 -> first use per page: "Sentinel-1 radar (it sees through typhoon clouds)" then "Sentinel-1"
- WorldPop -> "population data (WorldPop)"; Microsoft GlobalML -> "building footprints (Microsoft)"
- MERIT Hydro HAND / JRC Global Surface Water -> methodology only, as "(public terrain and surface-water datasets)"
- Keep with NO gloss (audience knows): PAGASA, DPWH, COA, MMDA, LGU, barangay, NDRRMC, Project NOAH, typhoon, GitHub

## DO NOT TOUCH (hard stops)

- JSON/data enum VALUES and keys: `under_observed_prone`, `charted`, `monitored`, `low`,
  `_meta.permanent_water_masked`, `recurrence_score`, `observed_flood_passes`,
  `warrants_investigation`, `geolocation_confidence`, filenames. These are data, not copy.
- Code identifiers/IDs: hazard-gap-fill, recurrence-dots, __fwCorridor, corridorState,
  cw-clock-*, lookupCorridor, CORRIDOR_BUFFER_M, recurrence_clf_v1, panel-*, fw-acct-*.
- Legal/verbatim strings (qa_live-asserted — keep BYTE-IDENTICAL):
  - The accountability disclaimer (governance.DISCLAIMER) and public-record block.
  - "warrants independent investigation"
  - Destination thesis: "Where flood-control money was spent, and where the water still came."
  - Block-3 redirect: "For live conditions, warnings, and routing during an active flood, use PAGASA ( bagong.pagasa.dost.gov.ph ), MMDA Flood Control, and your LGU DRRMO." (already plain; keep)
  - The standing footer line: "Observed flood extent derived from public satellite data. Patterns may have legitimate explanations; figures warrant independent verification." (keep)
  - "Expressway watch" headline (just shipped, keep)
  - honest-empty caption fragments in site/src/lib/freshnessClock.ts — if you must touch
    them, the orchestrator owns the lockstep qa_live update. Agents: DO NOT change freshnessClock.ts.
- /methodology BODY may keep precise terms (Otsu, backscatter, MERIT/JRC, IoU/F1 numbers)
  but its OPENING paragraph must be plain. Bare "IoU 0.054 · F1 0.065" must be REMOVED from
  /map and /faq and replaced with: "Validated against an independent 2015 flood map; the
  overlap is low and openly reported (see methodology)." The numbers live on /methodology only.

## Voice

Xavier's voice: direct, technical-when-needed, no fluff, no AI tells, no em-dashes in
user strings, no "delve/leverage/seamless/robust/comprehensive/underscore/realm". Short
concrete sentences. Every changed string must still be true (no overclaim, conservative
civic posture intact).
</content>
