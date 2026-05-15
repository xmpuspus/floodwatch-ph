# Running FloodWatch.PH on a new typhoon event

This recipe shows how to register a new typhoon event in `event/events.json` and
run `make event` to produce a flood-extent GeoJSON for that event. It assumes you
have an authenticated Earth Engine environment (`earthengine authenticate`) and
the pinned Python deps installed.

The natural extension after Carina 2024 is events like Kristine / Trami (Oct 2024)
or Odette (Dec 2021), which are the v1.1 candidates. The recipe below walks through
registering a new event and running the full Track A pipeline for it.

## What you need

- An authenticated Google Earth Engine account with access to `COPERNICUS/S1_GRD`.
  Free registration at https://earthengine.google.com.
- Python 3.11+, pip, the pinned deps from `requirements.txt`.
- A bounding box covering the region of interest. PSA PSGC boundaries or
  geojson.io are good sources for PH AOIs.
- The event start and end date range (must bracket the typhoon landfall). PAGASA
  TCWS archives and the NDRRMC situation reports are good sources for dates.

## 1. Add the event to `event/events.json`

`event/events.json` is the registry. Each entry follows this shape:

```json
{
  "key": "kristine_2024",
  "label": "Tropical Storm Kristine (Trami), October 2024",
  "bbox": [121.5, 13.5, 126.0, 18.5],
  "window_start": "2024-09-25",
  "window_end": "2024-11-05",
  "baseline_start": "2024-07-01",
  "baseline_end": "2024-09-20",
  "gauged": false,
  "holdout": false,
  "role": "demo"
}
```

Field notes:

- `key` -- lowercase, snake_case, used as a filename stem (e.g. `flood_kristine_2024.geojson`).
- `bbox` -- `[west, south, east, north]` in WGS84 decimal degrees. Keep it tight around the AOI; large bboxes slow the S1 pull significantly.
- `window_start` / `window_end` -- the date range from which S1 acquisitions are fetched. Include several dry weeks before the event as well as the peak and recession.
- `baseline_start` / `baseline_end` -- the dry-season window used to build the pre-event composite. Avoid dates within 30 days of the event window.
- `gauged` -- set to `true` only if a published ground-truth flood polygon exists (e.g. a GFD event footprint). If `true`, set `gfd_event_id` to the GFD integer ID.
- `holdout` -- set to `true` if this event is reserved for model evaluation only and must not appear in Track B training. Named holdout events are listed in `model/holdout_events.json`; the CI gate enforces this.
- `role` -- `"demo"` for events used on the site time-slider; `"validation"` for events used only in the IoU/F1 benchmark.

The site mirrors `event/events.json` to `site/src/data/events.json`. The CI gate
asserts byte-identity between the two copies. After editing `event/events.json`, run:

```bash
cp event/events.json site/src/data/events.json
```

## 2. Run Track A for the new event

```bash
make event EVENT=kristine_2024
```

This runs two scripts in sequence:

1. `event/fetch_s1_event.py --event kristine_2024` -- queries Earth Engine for
   Sentinel-1 GRD IW scenes intersecting the event bbox and window. Downloads the
   pre-event baseline composite and per-date VH/VV rasters as Cloud Optimized
   GeoTIFFs into `event/cache/kristine_2024/`. The pull uses server-side Earth
   Engine reduction and stays within free-tier quotas for a standard Philippine bbox.
   If the pull throttles partway through, re-run; partial dates are skipped.

2. `event/flood_extent.py --event kristine_2024` -- for each acquisition date:
   a. Speckle-filter (refined-Lee / focal median) and convert to dB.
   b. Compute the change image (`during - baseline`) on VH. Compute the Otsu
      threshold on the change image histogram. Apply to get candidate open water.
   c. Cross-check with VV.
   d. Subtract the permanent-water mask (HAND + JRC GSW + OSM).
   e. Emit a Polygon GeoJSON feature for that date.
   
   All per-date features are collected into a single `FeatureCollection` written to
   `site/public/data/flood_kristine_2024.geojson`.

The output `_meta` block will include:

```json
{
  "_meta": {
    "event": "kristine_2024",
    "label": "Tropical Storm Kristine (Trami), October 2024",
    "role": "demo",
    "gauged": false,
    "permanent_water_masked": true,
    "dates": [
      {"date": "2024-10-01", "flood_area_km2": ..., "otsu_threshold_db": ..., "n_polygons": ...}
    ]
  }
}
```

If `gauged` is `true`, the `_meta.validation` block will also be populated with
`{gfd_event_id, validation_date, iou, precision, recall, f1}` after the IoU
computation runs.

## 3. Verify the output

```bash
python scripts/check_permanent_water.py site/public/data/flood_kristine_2024.geojson
```

This asserts:
- `_meta.permanent_water_masked` is `true`.
- Less than 5% of the flood area intersects JRC >= 50%-occurrence permanent water.

Exit code is non-zero if either check fails. Fix by re-running `flood_extent.py`
with the permanent-water mask enabled (the default; check that `--no-mask` was not
passed).

Then run the full gate suite:

```bash
make verify
```

This runs all CI gates: permanent-water check, event-disjoint check, PII check,
events.json mirror check, hash-verify, Astro typecheck and build, and pytest.
All gates must exit zero before publishing.

## 4. Copy the events.json mirror and commit

```bash
cp event/events.json site/src/data/events.json
git add event/events.json site/src/data/events.json site/public/data/flood_kristine_2024.geojson
git commit -m "add kristine_2024 event (gauged: false)"
```

The CI gate will re-assert byte-identity on push.

## 5. If the event has a ground-truth polygon (gauged: true)

Set `"gauged": true` and `"gfd_event_id": <integer>` in the registry entry. After
`make event`, run:

```bash
python scripts/plot_metrics.py --event kristine_2024
```

This computes IoU, precision, recall, and F1 against the GFD footprint and writes
figures to `docs/figures/`. Update `MODEL_CARD.md` Track A performance table with
the actual values from `site/public/data/flood_kristine_2024_meta.json`.

## What the site time-slider needs

The MapLibre time-slider reads features from the GeoJSON filtered by the `date`
property. Each feature must have `properties.date` in `"YYYY-MM-DD"` format and
`properties.event` matching the registry key. The slider will show one frame per
unique date in the file. No site code change is needed for a new event as long as
the GeoJSON schema matches -- the slider reads the dates dynamically from the
`_meta.dates[]` array.

## Notes on Earth Engine quotas

All S1 pulls use server-side Earth Engine `ImageCollection.median()` and
`reduceRegion()` to export only small client-side downloads. A typical Philippine
typhoon bbox (500 km x 400 km) over 6 dates uses well under the free-tier daily
export quota. If a pull is throttled, the script emits `_meta.scan_status: "partial"`
on the affected date and is resumable.

## Citation

If you publish research using a FloodWatch.PH event run, cite the model
(`CITATION.cff`) and note the event key, acquisition dates, and Otsu threshold
values from `_meta.dates[]` in your methods section.
