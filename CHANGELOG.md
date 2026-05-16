# Changelog

All notable changes to FloodWatch.PH are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-16 - near-real-time observed layers, area/route lookup

v1.1.0 adds a near-real-time "Now" view next to the kept v1.0 Carina-2024
historical demo. Everything new is observed and dated, never a forecast. The
public data chain stays 100% open (Sentinel-1, GPM IMERG, OpenStreetMap); no
paid dependencies; the permanent-water and event-disjoint CI gates are
unchanged and the recurrence classifier sha256 is still b7c702532f92c43f.

### Added

- **Track A latest pass.** `event/fetch_s1_latest.py` + `event/flood_latest.py`
  auto-detect the most recent usable Sentinel-1 acquisition over the Greater
  Metro Manila + Central Luzon corridor and run the identical Otsu +
  permanent-water + HAND detection, writing `flood_latest.geojson` with
  `_meta.scan_status` (ok / no_usable_pass / degenerate_threshold /
  low_confidence) and `_meta.as_of`. The first generated layer is the
  2026-05-15 pass: scan_status ok, 27 flood polygons, ~31 km2. No-pass,
  degenerate-Otsu and implausible-count guards emit an honest empty state
  rather than a fabricated polygon or a blank-map that reads as "clear".
- **Rainfall context.** `realtime/` derives 24 h and 72 h GPM IMERG V07
  accumulation over the Track B modeled-prone mask into
  `current_risk.geojson`, labeled rainfall accumulation as of a UTC stamp.
  It is context for the Sentinel-1 revisit gap, explicitly not a score and
  not a flood forecast. Bands are PAGASA advisory thresholds used as labels
  only, with the source cited in `_meta`.
- **Expressway / road flood-exposure.** `pipeline/road_exposure.py`
  intersects the latest observed extent with the OpenStreetMap motorway /
  trunk / named-expressway network (SLEX, NLEX, SCTEX, Skyway, CAVITEX,
  TPLEX, NAIAX, CALAX, C5, EDSA, Commonwealth) into
  `road_flood_exposure.geojson` with per-segment exposure
  (flooded / near / clear / unknown) and a per-expressway summary. The
  2026-05-15 pass honestly shows zero monitored segments intersecting the
  observed extent (the detected water was rural Pampanga / Bulacan farmland).
- **Area / route flood-prone lookup** (`/lookup`). A fully client-side check:
  a bundled 99-entry Greater Metro Manila gazetteer (public OSM / PSA points)
  matched in the browser, no third-party geocoder, the typed query never
  leaves the browser and is never logged (RA-10173-safe; preserves the
  published no-geocoders CSP posture). It returns five layered, as-of-dated
  evidence rows (Track B recurrence, GFD 2002-2017 history, latest Sentinel-1
  status, GPM rainfall context, nearby flagged expressway segments). It never
  outputs a verdict, a score, or a "will / will not flood" claim, and points
  to PAGASA, MMDA Flood Control and LGU DRRMO for live conditions.
- **Now view + freshness banners.** `/map` now has a default Now view and a
  clearly-labeled 2024 Carina historical tab. A site-wide banner states what
  is shown and its as-of date, read dynamically from each file's `_meta`, and
  says plainly when a satellite pass was not usable.
- **Scheduled refresh + ops.** `.github/workflows/refresh.yml` regenerates all
  three layers on a daily cron with a least-privilege, secret-scoped,
  SHA-pinned workflow. `scripts/gate_realtime.py` blocks broken or fabricated
  data from deploying while allowing honest-empty states through.
  `scripts/deploy_realias.py` makes the public-alias repoint explicit and
  verified, with rollback and a GitHub-issue pager on failure. Runbook in
  `docs/ops/runbook.md`.
- **Related-work and defensibility** (`docs/research/related-work.md`). Prior
  art surveyed against Google Flood Hub (Philippine coverage is riverine
  forecast only, not pluvial or urban), Project NOAH, PAGASA, Copernicus EMS
  GFM, the Global Flood Database and others. FloodWatch is positioned as an
  independent, open, reproducible observed-extent and recurrence-vs-record
  measurement, complementary to and never a replacement for those systems.

### Changed

- `/map` payload is lazy-loaded: the default Now view transfers about 289 KB
  gzip versus about 897 KB before; the recurrence and national hazard layers
  load only when their toggle or the Carina tab is opened.
- `earthengine-api` pinned to 1.7.26 across root and pipeline requirements;
  `pyproj==3.6.1` added for the metric-CRS road intersection.

### Fixed

- Copy audit corrections: the embedding scale is stated as its true 300 m
  (not 10 m) everywhere, the embeddings cache size as about 1 MB (not
  ~10 MB), v1.0 aggregation as province (not barangay), and several stale
  CHANGELOG and spec figures reconciled to the generated data.
- The locked `__fwMap` / `__fwReady` deploy-verification handles are exposed
  from the default Now view, and the Carina demo map now renders reliably
  when its tab is opened (it is created in a hidden panel, which previously
  left MapLibre's load event unfired).

## [1.0.0] - 2026-05-15 - inaugural public release

v1.0.0 ships one calibrated Track A demo event, the Track A IoU/F1 validation
against a GFD reference polygon, and the Track B recurrence model trained and
calibrated on the full GFD Philippines event history with an event-disjoint holdout.

### Added

- **Track A -- Sentinel-1 SAR flood-extent change detection.** Per-timestep flood
  polygon GeoJSON for Super Typhoon Carina / Gaemi + enhanced SW monsoon, Jul-Aug 2024,
  Metro Manila + Bulacan + Pampanga (bbox `[120.5, 14.4, 121.4, 15.3]`). Four real
  S1 event acquisition dates (2024-07-10, 07-22, 07-30, 08-03), with a dry
  pre-event baseline composite from 2024-06-16 and 06-28. Carina 2024 has no promptly-public official
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
  `model/embeddings/floodwatch_embeddings_v1.npz` (~1 MB). `make train` reproduces
  the model bit-exact in approximately 30 seconds with no GPU.
- **Event-disjoint holdout.** Whole typhoon events held out (named in
  `model/holdout_events.json`). CI gate `scripts/check_event_disjoint.py` enforces
  that no holdout event appears in any training fold; the split file hash is pinned
  in the Makefile.
- **`make hash-verify`.** Asserts `recurrence_clf_v1.joblib` sha256 `b7c702532f92c43f`.
  Deterministic from pinned deps in `requirements.txt`.
- **Province exposure join** (`pipeline/exposure.py`). WorldPop population and
  Microsoft GlobalML built-up area aggregated to province level (FAO GAUL level-2,
  ~82 Philippine provinces). City and barangay resolution is a documented v1.1
  refinement. Counts rounded to the nearest 10. CI gate `scripts/check_no_pii.py`
  asserts no per-dwelling geometry and no PII property keys in any published output.
- **Hazard gap layer** (`pipeline/hazard_gap.py`). Province-level comparison of
  modeled flood-proneness (Track B) vs the historical observed record (Global Flood
  Database). `gap: "under_observed_prone"` flags provinces modeled flood-prone but
  with few or no events in the historical observed record, the headline civic
  finding. The official UP NOAH / PAGASA / MGB hazard-map cross-reference is a
  documented v1.1 refinement (those layers are token-gated or SPA-only).
- **Astro + MapLibre site** (`site/`). Time-slider over the four Carina 2024 S1
  event acquisition dates. Click a province for exposed population, built-up area,
  observed historical events, and peak flood share. Pages: index, map, methodology,
  recurrence, privacy, faq, safety.
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
