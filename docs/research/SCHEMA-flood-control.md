# Schema: flood-control accountability data files

Two files are written by `pipeline/flood_control.py` into `site/public/data/`.
This document is the contract Agent-WA codes the UI against. It is committed
before the real JSON lands so UI work runs in parallel.

Source: BetterGovPH `bettergovph/dpwh-transparency-data` (CC0 1.0 public domain),
flood-control subset only. Population: DPWH category "Flood Control and
Drainage" plus unclassified-category projects whose description is
flood-control; explicitly road/bridge/building-categorized projects are
excluded even when they include drainage components. Project locations are
DPWH/BetterGovPH MYPS planning
coordinates; an estimated 10 to 15 percent carry coordinate uncertainty per COA.
This surface reports where money was allocated and where Sentinel-1 still
observed flooding. It is not a finding of fraud, project failure, or causation.

Language rule for any consumer: use "flagged for review" / "warrants
independent investigation". Never "ghost", "failed", or "caused". Never present
a sorted list of named projects.

---

## File 1: `flood_control_accountability.json` (aggregate-only, public surface)

The rendered file. Region/province by project-type by budget-tranche
aggregates plus the cross-reference summary. No array of named projects
anywhere the UI can list. This is what the accountability page fetches.

```jsonc
{
  "_meta": {
    "source": "BetterGovPH bettergovph/dpwh-transparency-data (CC0)",
    "snapshot_sha256": "<hex sha256 of the cached raw parquet snapshot>",
    "n_projects": 0,                       // int, flood-control subset count
    "total_allocation_php": 0,             // int, sum of allocation across subset
    "generated_utc": "2026-05-17T00:00:00Z",
    "scope": "BetterGovPH DPWH transparency, flood-control subset",
    "population": "DPWH category 'Flood Control and Drainage' plus unclassified-category projects whose description is flood-control; explicitly road/bridge/building-categorized projects excluded even when they include drainage components",
    "geolocation_caveat": "MYPS planning coords; ~10-15% uncertain (COA)",
    "warrants_investigation_rule": "allocation_php > 0 AND (recurrence_score >= 0.60 OR observed_flood_passes > 0)",
    "prone_threshold": 0.60,
    "disclaimer": "<governance.DISCLAIMER, exact>",
    "public_record_block": "<governance.PUBLIC_RECORD_BLOCK, exact>"
  },

  "by_province": [
    {
      "province": "Bulacan",               // hazard_gap feature 'city' field
      "region": "Region III (Central Luzon)", // hazard_gap feature 'province' field
      "n_projects": 0,                     // int, projects whose location resolves to this province
      "allocation_php": 0,                 // int, sum of allocation for those projects
      "recurrence_score": 0.0,             // float, from hazard_gap polygon
      "observed_events": 0,                // int, from hazard_gap polygon
      "gap": "low",                        // str, hazard_gap gap class verbatim
      "observed_flood_passes": 0,          // int, count of dated S1 passes any project here fell within observed water
      "flagged_rate": 0.0,                 // float 0..1, share of province projects modeled-prone AND observed flooded
      "warrants_investigation": false,     // bool, per _meta.warrants_investigation_rule
      "disclaimer": "<DISCLAIMER, exact>"
    }
  ],

  "by_type": [
    {
      "project_type": "flood control",     // normalized title-keyword class
      "n_projects": 0,
      "allocation_php": 0,
      "flagged_rate": 0.0,
      "disclaimer": "<DISCLAIMER, exact>"
    }
  ],

  "by_tranche": [
    {
      "tranche": "₱10-50M",                // one of governance.BUDGET_TRANCHES labels
      "n_projects": 0,
      "allocation_php": 0,
      "flagged_rate": 0.0,
      "disclaimer": "<DISCLAIMER, exact>"
    }
  ]
}
```

Notes for the UI:

- `by_province` is sorted by `province` ascending (stable, deterministic). It is
  a province roll-up, not a project list. Safe to render as a table or choropleth.
- `flagged_rate` is a fraction in `[0, 1]`. Format as a percentage in the UI.
- `warrants_investigation` is the only flag. Render it as "warrants independent
  investigation", never as an accusation.
- `gap` carries the hazard_gap class verbatim: one of `charted`, `low`,
  `under_observed_prone` (and `monitored` if present in the polygon source).
- A province appears only if at least one flood-control project resolves to it.
- Tranche labels and order come from `governance.BUDGET_TRANCHES`; render in
  the array order given.
- `_meta.disclaimer` must equal `governance.DISCLAIMER` byte-for-byte. CI fails
  the build if it is missing or altered. Do not template or trim it in the UI.

## File 2: `flood_control_by_id.json` (by-id map, lookup-only)

Every flood-control project keyed by id. No flagged-only filter, no sorted
list, no array. The UI never lists this. It is read only when a user has
already resolved to a province on `/lookup`, then the page may show counts or
look up a specific id the user already holds. Friction is intentional.

```jsonc
{
  "_meta": {
    "source": "BetterGovPH bettergovph/dpwh-transparency-data (CC0)",
    "snapshot_sha256": "<same hex as file 1>",
    "n_projects": 0,
    "generated_utc": "2026-05-17T00:00:00Z",
    "population": "DPWH category 'Flood Control and Drainage' plus unclassified-category projects whose description is flood-control; explicitly road/bridge/building-categorized projects excluded even when they include drainage components",
    "geolocation_caveat": "MYPS planning coords; ~10-15% uncertain (COA)",
    "disclaimer": "<DISCLAIMER, exact>",
    "public_record_block": "<PUBLIC_RECORD_BLOCK, exact>"
  },
  "projects": {
    "<project_id>": {
      "title": "",                         // str, project description verbatim from source
      "allocation_php": 0,                  // int or null if not parseable
      "status": "completed",                // one of: completed | ongoing | not_started | terminated | unknown
      "geolocation_confidence": 1.0,        // 1.0 source coords; 0.6 province-centroid fallback
      "province": "Bulacan",                // resolved hazard_gap 'city', or null if unresolved
      "region": "Region III (Central Luzon)", // resolved hazard_gap 'province', or null
      "recurrence_score": 0.0,              // float from the resolved province polygon, or null
      "observed_flood_passes": 0,           // int, dated S1 passes this project location fell within observed water
      "disclaimer": "<DISCLAIMER, exact>"
    }
  }
}
```

Notes for the UI:

- `projects` is an object keyed by the source `project_id` string. There is no
  ordered list. The UI must not build a "top flagged" list from this.
- `status` is normalized to `completed`, `ongoing`, `not_started`,
  `terminated`, or `unknown`. The raw DPWH value "For Procurement" maps to
  `not_started`; "Terminated" maps to `terminated`.
- `geolocation_confidence` is `1.0` when the project carried usable source
  coordinates, `0.6` when the location was filled from the province-centroid
  fallback, derived from the hazard_gap province polygon the project text
  resolved to. A project with neither has `province: null` and confidence `0.6`
  only if a province was resolvable by text, else it is unresolved.
- Every project record carries `disclaimer` equal to `governance.DISCLAIMER`.

## Governance invariants (both files)

- Top-level `_meta.disclaimer` and every record-level `disclaimer` equal
  `floodwatch_ph.accountability.governance.DISCLAIMER` byte-for-byte.
- `_meta.public_record_block` equals `governance.PUBLIC_RECORD_BLOCK`.
- The pipeline calls `governance.assert_governed(obj)` on each file object
  before writing. A missing or altered disclaimer raises and fails the build.
- `_meta.snapshot_sha256` is the sha256 of the cached raw parquet snapshot
  (`pipeline/_dpwh_flood_control_cache.parquet`), so the published numbers are
  reproducible from a committed artifact and CI runs offline from the cache.
