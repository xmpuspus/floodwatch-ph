# FloodWatch.PH published data schema

All files are CC-BY-4.0. Cite `FloodWatch.PH (2026), https://github.com/xmpuspus/floodwatch-ph`.
Every analytics surface carries: *"Observed flood extent derived from public
satellite data. Patterns may have legitimate explanations; figures warrant
independent verification."*

## `flood_<event>.geojson` (Track A — event flood extent)

`FeatureCollection`. One file per event (`flood_carina_2024.geojson`,
`flood_koppu_2015.geojson`).

- `_meta.event` — event key
- `_meta.label` — human label (e.g. "Super Typhoon Carina (Gaemi)...")
- `_meta.role` — `"demo"` or `"validation"`
- `_meta.gauged` — bool (true if a GFD ground-truth polygon exists)
- `_meta.permanent_water_masked` — **always `true`** (integrity decision 2; CI-gated)
- `_meta.aoi_name`, `_meta.bbox`
- `_meta.dates[]` — `{date, flood_area_km2, otsu_threshold_db, n_polygons}`
- `_meta.validation` (gauged events only) — `{gfd_event_id, validation_date, iou, precision, recall, f1}`
- `features[]` — `Feature` Polygon, `properties = {date: "YYYY-MM-DD", event}`.
  The site filters features by the slider's selected `date`.

## `flood_<event>_meta.json`

The `_meta` block above, standalone, for the methodology/figures.

## `recurrence_prone.geojson` (Track B — recurrence-prone classifier output)

`FeatureCollection` of Point features (sampled grid), permanent water removed.

- `_meta` — `{model: "recurrence_clf_v1", embedding: "AlphaEarth 2017 64-dim",
  threshold, holdout_iou_f1: {...}, disclaimer}`
- `features[].properties` — `{score: 0..1 calibrated, prone: bool (score>=threshold)}`
  No dwelling identifiers. Points are a 10–30 m sample grid, not buildings.

## `hazard_gap.geojson` (the civic layer)

`FeatureCollection`, Polygon per barangay.

- `properties` — `{barangay, city, province, recurrence_score (0..1, mean of
  Track B over the barangay), on_official_hazard_map: bool,
  observed_event_count: int (GFD events intersecting), gap: "uncharted" |
  "charted" | "low"}`. `gap == "uncharted"` ⇔ recurrent observed flooding **and**
  absent from the official hazard layer — the headline civic finding.
- `_meta.disclaimer` — required public-records disclaimer string.

## `barangay_exposure.json` (click-target aggregates)

Object keyed by barangay id:

- `{ name, city, province, population (WorldPop, integer, rounded to nearest 10),
  building_count (Microsoft GlobalML footprints), peak_flood_pct (max share of
  barangay area flooded across the demo event's dates),
  on_official_hazard_map: bool }`

**Privacy (decision 5):** every figure is a barangay-level aggregate. No
household geometry, no per-dwelling flood status, no PII property keys. Counts
are rounded. CI gate `scripts/check_no_pii.py` enforces this.
