# `flood_latest.geojson` schema (near-real-time Track A)

Contract for `site/public/data/flood_latest.geojson`. Agent B (site) and
Agent D (tests/QA) build against this. It is intentionally a strict superset
of the `flood_<event>.geojson` schema in `site/public/data/SCHEMA.md`, so the
existing map code, `tests/test_schema.py`, and `scripts/check_permanent_water.py`
keep working unchanged.

## What this file is

The most recent **usable observed** Sentinel-1 SAR pass over the Greater Metro
Manila + Central Luzon corridor, run through the same validated detection
method as `event/flood_extent.py`. Sentinel-1 revisit over the Philippines is
~6–12 days.

**It is OBSERVED, NOT a forecast, NOT live.** `_meta.as_of` is the satellite
acquisition date; the data is lagged by days. Render it as
"latest satellite pass — <as_of>", never "live" or "current".

Produced by `event/flood_latest.py` (`make event-latest` once Agent C wires
the Makefile target). Also writes `site/public/data/flood_latest_meta.json`
(the `_meta` block standalone).

## Top level

```json
{ "type": "FeatureCollection", "_meta": { ... }, "features": [ ... ] }
```

- `type` — always the string `"FeatureCollection"`.
- `_meta` — object, see below.
- `features` — always a JSON array. **Empty `[]` whenever
  `_meta.scan_status != "ok"`** (no-pass / degenerate / low-confidence). Never
  contains a fabricated polygon.

## `features[]`

Present only when `_meta.scan_status == "ok"`. Each element:

```json
{
  "type": "Feature",
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "properties": { "date": "YYYY-MM-DD", "event": "latest" }
}
```

- `geometry.type` — always `"Polygon"` (single polygons; permanent-water,
  slope, HAND-plausible and min-area masked, smoothed, Douglas–Peucker
  simplified, identical to the event path).
- `properties.date` — equals `_meta.as_of` (the S1 acquisition date). Lets the
  existing date-slider filter treat this like any other flood layer.
- `properties.event` — always the string `"latest"`.
- No other property keys. No PII, no per-dwelling data.

## `_meta` fields

### Keys required by the existing flood schema / CI (always present)

| key | type | value |
|---|---|---|
| `event` | string | always `"latest"` |
| `label` | string | `"Latest Sentinel-1 pass — Greater Metro Manila + Central Luzon"` |
| `role` | string | always `"realtime"` |
| `gauged` | bool | always `false` (no GFD ground truth for a live pass) |
| `permanent_water_masked` | bool | always `true` — CI-gated, locked decision 2 |
| `aoi_name` | string | human AOI description |
| `bbox` | `[w,s,e,n]` | `[120.40, 14.00, 121.55, 15.40]` lon/lat |
| `dates` | array | `[]` unless `scan_status == "ok"`, then exactly one entry: `{date, flood_area_km2, otsu_threshold_db, n_polygons}` |

### Near-real-time fields (always present)

| key | type | value |
|---|---|---|
| `scan_status` | string enum | one of `"ok"`, `"no_usable_pass"`, `"degenerate_threshold"`, `"low_confidence"` (see below) |
| `observed_not_forecast` | bool | always `true` |
| `generated_at` | ISO-8601 UTC string | when the script ran, e.g. `"2026-05-16T04:49:03Z"` |
| `as_of` | ISO date string or `null` | S1 acquisition date `"YYYY-MM-DD"`; `null` when `scan_status == "no_usable_pass"` |
| `lookback_days` | int | how many days back the scan searched (default 14) |
| `baseline_days` | int | dry-baseline window length in days (default 60) |
| `s1_scene_ids` | string array | Copernicus S1 product IDs used (`[]` if no pass) |
| `feature_count` | int | number of polygons in `features` (`0` unless `scan_status == "ok"`) |
| `method` | string | one-line method description (mirrors `event/flood_extent.py`) |
| `disclaimer` | string | required public-data / not-a-forecast disclaimer |

### Fields present only when a pass was found (`scan_status != "no_usable_pass"`)

| key | type | notes |
|---|---|---|
| `otsu_threshold_db` | float | Otsu valley in dB, clamped to `[-24, -14]` |
| `orbit_pass` | string | `"ASCENDING"` or `"DESCENDING"` (single consistent track) |
| `relative_orbit` | int | Sentinel-1 relative orbit number of the chosen track |
| `aoi_coverage` | float | fraction of AOI the chosen pass footprint covers (`0..1`) |
| `note` | string | present on non-`ok` statuses; human reason the extent was withheld |
| `rejected_flood_area_km2` | float | present on `low_confidence`: the implausible area that was withheld |

## `scan_status` values (authoritative)

| value | meaning | `features` | `as_of` | site should render |
|---|---|---|---|---|
| `ok` | usable pass, valid Otsu valley, plausible extent — real flood polygons published | non-empty | the pass date | the flood layer + "satellite pass <as_of>" |
| `no_usable_pass` | no S1 acquisition with ≥55% AOI coverage in the lookback window | `[]` | `null` | "no recent usable pass in the last N days" (no map lie) |
| `degenerate_threshold` | a pass exists but the Otsu valley pinned to a clamp rail (no real water/land separation) | `[]` | the pass date | "last pass <as_of> had no reliable water signal" |
| `low_confidence` | detected area exceeds the plausibility cap (≈ speckle/agriculture, not flood) | `[]` | the pass date | "last pass <as_of> inconclusive" |

**Rule for consumers:** only draw flood geometry when
`scan_status == "ok" && features.length > 0`. For every other status show the
honest text using `as_of` (the last good/most recent pass date) — never a
blank map presented as "no flooding".

## Stability guarantees

- `type`, the 8 required schema keys, `scan_status`, `as_of`, `generated_at`,
  `feature_count`, `s1_scene_ids` are **always present** regardless of status.
- `permanent_water_masked` is **always `true`**.
- New `_meta` keys may be added later; consumers must not assume the set is
  closed. The keys in this doc will not be removed or change type.
