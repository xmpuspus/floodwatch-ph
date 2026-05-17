# Agent-WBD brief — wave B data + adapter + governance module

You own: `floodwatch_ph/**`, `pipeline/flood_control.py`, new `site/public/data/flood_control_*`
files, `docs/research/SCHEMA-flood-control.md`, `requirements.txt` additions (pinned `==`).
Do NOT touch `site/src/**`, `scripts/**`, `tests/**`, `.github/**`, `Makefile` (Agent-WBI owns those).

Read first: `docs/plans/recenter/00-master.md`, `docs/research/ghostwatch-study.md`
(§II, V, VIII, Appendix), `docs/research/flood-control-data-feasibility.md`. Study the
real ghostwatch code:
- `/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/base.py` (subclass this pattern)
- `/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/philippines.py` (lines 71-256: fetch retry, column-variant detection, status normalization, type classification, geolocation extraction)
- `/Users/xavier/Desktop/ghostwatch/ghostwatch/config.py` (Pydantic Settings threshold pattern)
- `/Users/xavier/Desktop/ghostwatch/api/routers/analytics.py` lines 10-12 (disclaimer constant)
- `/Users/xavier/Desktop/ghostwatch/api/services/data_service.py` 253-316 (aggregation-only)

## Build

1. `floodwatch_ph/accountability/governance.py`
   - `DISCLAIMER` constant (hardcoded, un-strippable). Exact text:
     `"Statistical indicators derived from public data. Patterns may have legitimate explanations. Flood-control project locations are per DPWH/BetterGovPH records (MYPS planning coordinates; an estimated 10 to 15 percent carry coordinate uncertainty per COA). This surface reports where money was allocated and where Sentinel-1 still observed flooding. It is not a finding of fraud, project failure, or causation. Specific allegations require independent investigation and corroboration."`
   - `PUBLIC_RECORD_BLOCK` constant (the civic-tech-ph all-data-is-public-record block).
   - `assert_governed(obj)` helper: raises if `_meta.disclaimer` missing/altered.
   - `BUDGET_TRANCHES` (e.g. <₱10M, ₱10-50M, ₱50-100M, ₱100-500M, >₱500M).

2. `floodwatch_ph/adapters/base.py` + `floodwatch_ph/adapters/flood_control.py`
   - Copy ghostwatch BaseAdapter pattern. `FloodControlAdapter`:
     - `fetch()`: resilient download of `bettergovph/dpwh-transparency-data` (curl with
       3-attempt retry + exponential backoff; fallback to `datasets`/`huggingface_hub`).
       Cache raw snapshot to `pipeline/_dpwh_flood_control_cache.parquet` (committed; the
       deterministic-CI artifact, mirrors the embeddings-cache pattern). Pipeline must run
       offline from the cache when present.
     - `parse()`: column-variant detection (contractId|project_id|...); filter category to
       flood-control (`category == "Flood Control and Drainage"` or title-keyword
       fallback: dike, drainage, flood control, river control, slope protection, pumping
       station, revetment); status normalization to {completed, ongoing, not_started};
       carry `latitude`/`longitude` + a `geolocation_confidence` (1.0 source coords; 0.6
       province-centroid fallback via `hazard_gap.geojson` province polygons).

3. `pipeline/flood_control.py` — cross-reference + emit
   - Load parsed flood-control projects. Point-in-polygon each project against
     `site/public/data/hazard_gap.geojson` (82 province polygons; `city`=province,
     `recurrence_score`, `observed_events`, `gap`). For projects with coords, also test
     intersection with observed extent `flood_carina_2024.geojson` polygons (the dated S1
     passes) — record which dated passes (`_meta.dates[].date`) the project location falls
     within observed water.
   - **Aggregate-only public file** `site/public/data/flood_control_accountability.json`:
     ```
     { "_meta": { "source": "BetterGovPH bettergovph/dpwh-transparency-data (CC0)",
                   "snapshot_sha256": "...", "n_projects": <int>, "total_allocation_php": <int>,
                   "generated_utc": "...", "geolocation_caveat": "MYPS planning coords; ~10-15% uncertain (COA)",
                   "disclaimer": DISCLAIMER, "public_record_block": PUBLIC_RECORD_BLOCK },
       "by_province": [ { "province": "...", "region": "...", "n_projects": <int>,
                   "allocation_php": <int>, "recurrence_score": <float>, "gap": "low|...",
                   "observed_flood_passes": <int>, "flagged_rate": <float>,
                   "warrants_investigation": <bool>, "disclaimer": DISCLAIMER } ],
       "by_type": [ { "project_type": "...", "n_projects": <int>, "allocation_php": <int>, "flagged_rate": <float>, "disclaimer": DISCLAIMER } ],
       "by_tranche": [ { "tranche": "...", "n_projects": <int>, "allocation_php": <int>, "flagged_rate": <float>, "disclaimer": DISCLAIMER } ] }
     ```
     `warrants_investigation` = (allocation_php > 0) AND (recurrence_score >= prone
     threshold OR observed_flood_passes > 0). `flagged_rate` = share of province
     projects whose location is modeled-prone AND observed flooded. NO project names here.
   - **By-ID map** `site/public/data/flood_control_by_id.json`: `{ "_meta": {disclaimer...},
     "projects": { "<project_id>": { "title", "allocation_php", "status",
     "geolocation_confidence", "province", "recurrence_score", "observed_flood_passes" } } }`
     — ALL projects keyed by id (no flagged-only filter, no sorted list). This powers
     `/lookup` only when a user already resolves to a province; the UI never lists it.
   - Every record dict carries `disclaimer`. Call `assert_governed` before writing.
   - **Compute before narrating:** print the real computed totals to stdout; Agent-WA and
     metrics.ts interpolate those — never hardcode prose numbers.

4. `docs/research/SCHEMA-flood-control.md` — document both files' schema EARLY (commit
   first thing) so Agent-WA can code the UI against it before real JSON lands.

5. `requirements.txt`: add pinned deps (`huggingface-hub==<latest>`, `pyarrow==<latest>`,
   `shapely==<latest>` if not present). Verify each `==`.

## Constraints
- No efficacy/causality. No "ghost"/"failed"/"caused". No COA-337 figure anywhere.
- Numbers must be computed by running the pipeline; capture real stdout into
  `docs/plans/recenter/_wbd-computed.txt`. No placeholder prose values.
- Plain English, zero AI-fingerprint words (no-ai-jargon.md), in code comments + the schema doc.
- Write status + the real computed numbers to `docs/plans/recenter/_wbd-status.md` when done.
</content>
