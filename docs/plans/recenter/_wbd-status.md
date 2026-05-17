# Agent-WBD status — wave B data + adapter + governance

Status: done. Pipeline runs to completion; governance check passes.

## Files created (owned scope only)

- `docs/research/SCHEMA-flood-control.md` — schema contract, committed first
  (commit 87caba6) so Agent-WA codes the UI in parallel.
- `floodwatch_ph/accountability/__init__.py`
- `floodwatch_ph/accountability/governance.py` — hardcoded `DISCLAIMER`,
  `PUBLIC_RECORD_BLOCK`, `BUDGET_TRANCHES` (5 bands), `tranche_for()`,
  `assert_governed()` (raises on missing/altered disclaimer or public-record
  block, walks by_province/by_type/by_tranche + projects map).
- `floodwatch_ph/adapters/__init__.py`
- `floodwatch_ph/adapters/base.py` — ghostwatch BaseAdapter pattern, sync.
- `floodwatch_ph/adapters/flood_control.py` — `FloodControlAdapter`: cache ->
  curl 3-retry+backoff -> hf_hub_download -> datasets; flood-control filter
  (category "Flood Control and Drainage" + title-keyword fallback); status
  normalization to completed/ongoing/not_started; geolocation_confidence.
- `pipeline/flood_control.py` — point-in-polygon vs hazard_gap 82 province
  polygons, intersection vs flood_carina_2024 dated S1 passes, emits the two
  governed JSON files.
- `pipeline/_dpwh_flood_control_cache.parquet` — committed raw snapshot (23 MB),
  the deterministic-CI artifact.
- `site/public/data/flood_control_accountability.json` — aggregate-only.
- `site/public/data/flood_control_by_id.json` — by-id map, lookup-only.
- `requirements.txt` — added `pandas==3.0.3`, `pyarrow==24.0.0`,
  `shapely==2.1.2`, `huggingface-hub==1.8.0` (all == pinned, match installed
  versions that produced the numbers).
- `docs/plans/recenter/_wbd-computed.txt` — captured real pipeline stdout.

## Real computed numbers (from the committed snapshot)

- Source: BetterGovPH `bettergovph/dpwh-transparency-data` (CC0), 248,220 raw
  rows, file `dpwh_transparency_data.parquet`.
- Flood-control subset: 44,983 projects (canonical category 33,866 plus the
  title-keyword fallback the brief requires: dike, drainage, flood control,
  river control, slope protection, pumping station, revetment, seawall, flood
  mitigation, river wall, bank protection).
- total_allocation_php = 1,972,257,679,834.
- 43,482 of 44,983 resolved to a province polygon (96.7%); the rest had no
  usable coords and no resolvable province text.
- by_province: 82 provinces. by_type: 11 classes. by_tranche: 5 bands.
- snapshot_sha256 = `5b411cf3f112fabd1913c70681791e5e2b78b43a8393f489f48bd882f154e123`
- 45 of 82 provinces meet the conservative `warrants_investigation` rule
  (allocation > 0 AND (recurrence_score >= 0.60 OR observed_flood_passes > 0)).
- Sentinel-1 Carina observed extent intersects flood-control project locations
  in Pampanga and Tarlac (2 dated passes each); both are modeled-prone.

These numbers differ from the feasibility doc's ~9,855 / ₱545B estimate
because that was a planning estimate. The figures above are computed from the
live BetterGovPH data with the title-keyword fallback, per compute-before-
narrating. Agent-WA and metrics.ts must interpolate these, not hardcode them.

## Governance verification (passed)

- `python3 -c "...assert d['_meta']['disclaimer']==g.DISCLAIMER..."` prints
  `governance OK 44983 1972257679834`.
- `assert_governed` passes on both files; tampering the disclaimer raises.
- `_meta.public_record_block` equals the constant on both files.
- `flood_control_accountability.json` has no project titles and no projects
  array (aggregate-only). `flood_control_by_id.json` is a dict keyed by id,
  no list.
- Tranche order matches `BUDGET_TRANCHES`.
- ruff check passes on all four Python files (line-length 100, py311).
- No AI-fingerprint words, no em-dashes, no efficacy/causation language about
  projects, no COA-337 figure, no 337-adjacent ghost/confirm strings.

## How CI runs offline from the cache

`FloodControlAdapter.fetch()` checks `pipeline/_dpwh_flood_control_cache.parquet`
first. The file is committed (23 MB), so CI and any offline run read it
directly and never touch the network. Verified: with the cache present the
adapter logs "Using committed snapshot cache" and returns immediately.
Re-running the pipeline reproduces the identical numbers and the same
snapshot_sha256, so the published artifact is deterministic. To refresh from
the live source, delete the cache file and re-run; the adapter will curl (3
retries + backoff), fall back to hf_hub_download then datasets, then rewrite
the cache.
