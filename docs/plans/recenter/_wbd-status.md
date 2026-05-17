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
  normalization to completed/ongoing/not_started/terminated;
  geolocation_confidence.
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
- Flood-control subset: 36,711 projects. Population is the exact DPWH
  category "Flood Control and Drainage" (33,866) plus rescued rows whose
  category is uninformative (blank or a funding-shell program code such as
  GAA 20XX, Unprogrammed, CSSP, MFO, OO-, LP, LFP, SSP) AND whose description
  is clearly flood-control by keyword (2,845). A row carrying an explicit
  non-flood infrastructure category (Roads, Bridges, Buildings and
  Facilities, Water Provision and Storage, Buildings) is never reclassified,
  even when its description mentions drainage or slope-protection components.
- total_allocation_php = 1,740,510,212,408 (about ₱1.74T).
- 35,485 of 36,711 resolved to a province polygon; the rest had no usable
  coords and no resolvable province text.
- by_province: 82 provinces. by_type: 11 classes. by_tranche: 5 bands.
- snapshot_sha256 = `5b411cf3f112fabd1913c70681791e5e2b78b43a8393f489f48bd882f154e123`
- 45 of 82 provinces meet the conservative `warrants_investigation` rule
  (allocation > 0 AND (recurrence_score >= 0.60 OR observed_flood_passes > 0)).
- Sentinel-1 Carina observed extent intersects flood-control project locations
  in Pampanga and Tarlac (modeled-prone provinces).

Filter-defect correction: an earlier revision used a broad title-keyword
fallback that pulled in 10,509 explicitly-typed non-flood projects (7,674
"Roads", 99 "Bridges", others) and inflated the total to ₱1.97T. Counting a
DPWH-categorized Roads project as flood-control spending is an over-claim the
conservative posture forbids. The corrected filter only rescues
uninformative-category rows and never overrides an explicit infrastructure
category. Regression check confirms zero road/bridge/building-categorized
rows in the subset. These numbers differ from the feasibility doc's ~9,855 /
₱545B planning estimate; they are computed from the live BetterGovPH data,
per compute-before-narrating. Agent-WA and metrics.ts must interpolate these,
not hardcode them.

Status-normalization defect correction: `normalize_status` returns the first
canonical class whose any variant is a substring of the lowered raw value.
The raw DPWH value "Not Yet Started" lowercases to "not yet started", which
contains "started" (an `ongoing` variant), so it was matching `ongoing`
before `not_started` was ever checked. `_STATUS_MAP` is now ordered
completed -> not_started -> terminated -> ongoing, with `not_started`
variants covering "not yet started", "not started", "for procurement",
"procurement", "for implementation", "pending". A `terminated` canonical was
added so the DPWH-terminated rows are labelled accurately instead of falling
to `unknown`. No `not_started` variant is a substring of "on-going", so real
"On-Going" still maps to `ongoing`; "Completed" is checked first.
n_projects and total_allocation_php are unchanged by this fix (only the
status label moves for the affected rows).

Corrected by-id status distribution (total 36,711):
- completed: 28,736
- ongoing: 6,879
- not_started: 950 (was published as `ongoing` before the fix)
- terminated: 146 (was `unknown` before the fix)

Tests: `tests/test_flood_control_adapter.py` status assertions rewritten to
encode the requirement ("Not Yet Started" -> not_started, "For Procurement"
-> not_started, "Terminated" -> terminated, real "On-Going" -> ongoing). The
prior test that pinned the buggy `ongoing` behavior was replaced.
`pytest tests/ -q` => 92 passed.

## Governance verification (passed)

- `python3 -c "...assert d['_meta']['disclaimer']==g.DISCLAIMER..."` prints
  `governance OK 36711 1740510212408`.
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
