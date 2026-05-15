# Changelog

All notable changes to FloodWatch.PH are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-15 - inaugural public release

v1.0.0 ships one calibrated Track A demo event, the Track A IoU/F1 validation
against a GFD reference polygon, and the Track B recurrence model trained and
calibrated on the full GFD Philippines event history with an event-disjoint holdout.

### Added

- **Track A -- Sentinel-1 SAR flood-extent change detection.** Per-timestep flood
  polygon GeoJSON for Super Typhoon Carina / Gaemi + enhanced SW monsoon, Jul-Aug 2024,
  Metro Manila + Bulacan + Pampanga (bbox `[120.5, 14.4, 121.4, 15.3]`). Six real
  S1 acquisition dates: 2024-06-16, 06-28 (dry baseline), 07-10 (pre), 07-22, 07-30
  (peak / recession), 08-03 (post). Carina 2024 has no promptly-public official
  flood-extent polygon; the absence of a reference is documented explicitly in
  `_meta.gauged: false`.
- **Track A validation against GFD event 4300.** IoU and F1 of the Otsu change-detection
  method vs the GFD `flooded` polygon for Tropical Storm Koppu / Lando, 2015-10-22,
  central Luzon, using the 2015-10-26 Sentinel-1 post-onset acquisition. The method
  is parameter-free; no train/test leakage applies.
- **Permanent-water mask** (HAND from MERIT Hydro + JRC GSW occurrence >= 50% + OSM
  `natural=water` / `waterway`). CI gate `scripts/check_permanent_water.py` asserts
  every published flood GeoJSON carries `_meta.permanent_water_masked: true` and
  < 5% of flood area intersects JRC permanent water.
- **Track B -- `recurrence_clf_v1`.** LogisticRegression head on frozen Google
  AlphaEarth Satellite Embedding V1 (64-dim, 2017, CC-BY-4.0, produced by Google and
  Google DeepMind), trained on GFD Philippines events 2002-2017, Platt-sigmoid
  calibrated on an event-disjoint holdout. Committed cache:
  `model/embeddings/floodwatch_embeddings_v1.npz` (~10 MB). `make train` reproduces
  the model bit-exact in approximately 30 seconds with no GPU.
- **Event-disjoint holdout.** Whole typhoon events held out (named in
  `model/holdout_events.json`). CI gate `scripts/check_event_disjoint.py` enforces
  that no holdout event appears in any training fold; the split file hash is pinned
  in the Makefile.
- **`make hash-verify`.** Asserts `recurrence_clf_v1.joblib` sha256 `b7c702532f92c43f`.
  Deterministic from pinned deps in `requirements.txt`.
- **Barangay exposure join** (`pipeline/exposure.py`). WorldPop population and
  Microsoft GlobalML building counts aggregated to barangay level. Counts rounded to
  the nearest 10. CI gate `scripts/check_no_pii.py` asserts no per-dwelling geometry
  and no PII property keys in any published output.
- **Hazard gap layer** (`pipeline/hazard_gap.py`). Barangay-level comparison of
  observed recurrence score (Track B) vs presence on the official UP NOAH / PAGASA /
  MGB hazard map. `gap: "uncharted"` flags barangays with observed recurrent flooding
  absent from the official hazard layer -- the headline civic finding.
- **Astro + MapLibre site** (`site/`). Time-slider over the six Carina 2024 S1
  acquisition dates. Click a barangay for exposed population, building count, and
  official hazard-map status. Pages: index, map, methodology, recurrence, privacy,
  faq, safety.
- **CI gate suite** (`scripts/`): `check_permanent_water.py`, `check_event_disjoint.py`,
  `check_no_pii.py`, site/src/data/events.json byte-identity vs event/events.json,
  `make hash-verify`, Astro typecheck + build, pytest.
- **Open-source release** under MIT (code) + CC-BY-4.0 (published data).
- **Community files:** `CITATION.cff`, `MODEL_CARD.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `docs/privacy-impact-assessment.md`,
  `site/public/data/SCHEMA.md`, `.zenodo.json`, GitHub issue templates.
- **`examples/run_on_new_event.md`:** recipe for registering a new typhoon event in
  `event/events.json` and running `make event`.

### Notes

- v1.1 scope (additional events Kristine / Trami Oct 2024, Odette 2021) is tracked
  in the issue backlog and will extend the multi-event arc after v1.0 ships calibrated
  and honest.
