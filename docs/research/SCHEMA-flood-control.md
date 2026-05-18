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
    "temporal_rule": "completed_then_flooded = DPWH records status 'completed' AND a dated Sentinel-1 pass AFTER the recorded completion_date still observed water at the recorded location, during Super Typhoon Carina (Jul-Aug 2024). This is the only dated observed extent; it is not a finding of project failure.",   // v1.5
    "confidence_rule": "share_low_confidence = allocation resolved only by province-text fallback (no project coordinate) over total allocation; higher means the province figure is coarser.",  // v1.5
    "coa_rule": "coa_flagged_findings_count = COA/Ombudsman public findings on flood-control projects in this province, per individually cited public sources (see pipeline/_coa_flagged.json). FloodWatch does not independently verify and makes no accusation; a per-project tag is applied only on a confident description match.",  // v1.5
    "coa_source": "Public COA/Ombudsman releases and reputable PH news (Wikipedia-cited COA filings, GMA News). See tmp/v1.5-coa-qa/run-notes.md for the per-row source map.",  // v1.5
    "satellite_rule": "satellite_checked_count / satellite_no_change_rate = coarse Sentinel-1 VH built-change corroboration at the recorded coordinate. Absence of a change signal is NOT evidence of a ghost: the recorded coordinate itself may be wrong (the MYPS problem). Indicative only, not confirmation, not a finding of fraud or project failure.",  // v1.5
    "satellite_method": "despeckled mean VH (dB) over a ~120 m disc at the recorded point: post-completion-window mean minus pre-start-window mean; Sentinel-1 IW GRD, VH polarisation, both orbit passes",  // v1.5
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
      "n_completed_then_flooded": 0,       // v1.5 int, projects DPWH-recorded completed before a dated S1 pass that still observed water there
      "allocation_completed_then_flooded_php": 0, // v1.5 int, allocation sum for those projects
      "post_completion_flagged_rate": 0.0, // v1.5 float 0..1, n_completed_then_flooded over province project count
      "allocation_low_confidence_php": 0,  // v1.5 int, allocation resolved only by province-text fallback (no coordinate)
      "share_low_confidence": 0.0,         // v1.5 float 0..1, allocation_low_confidence_php over province allocation_php
      "coa_flagged_findings_count": 0,     // v1.5 int, cited public COA/Ombudsman findings mapped to this province
      "coa_findings": [],                  // v1.5 str[], distinct coa_finding labels present (e.g. flagged_review, pre_existing, site_mismatch)
      "coa_source_orgs": [],               // v1.5 str[], distinct citing orgs (e.g. COA, GMA)
      "satellite_checked_count": 0,        // v1.5 int, projects with a Sentinel-1 VH built-change corroboration computed
      "satellite_no_change_rate": 0.0,     // v1.5 float 0..1, share of checked projects with no built-change signal (indicative only)
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
      "completion_date": null,              // v1.5 str date or null, DPWH-recorded completion date
      "post_completion_observed_passes": 0, // v1.5 int, dated S1 passes after completion_date that still observed water here
      "coa_flagged": false,                 // v1.5 bool, true only on a confident description match to a cited COA/Ombudsman finding
      "coa_finding": null,                  // v1.5 str or null, the matched finding label (e.g. flagged_review)
      "coa_source": null,                   // v1.5 str or null, the citing org for the matched finding
      "satellite_checked": false,           // v1.5 bool, true if a Sentinel-1 VH built-change check ran at the coordinate
      "built_change_signal": null,          // v1.5 str or null, one of: strong | weak | none (indicative; null when not checked)
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

## v1.5 accountability deepening

`n_projects` and `total_allocation_php` are unchanged from v1.4.3 (36,711
projects; PHP 1,740,510,212,408). v1.5 adds four read paths over the same
subset; it adds no projects and no allocation.

- Temporal "spent then still flooded" (`n_completed_then_flooded`,
  `allocation_completed_then_flooded_php`, `post_completion_flagged_rate`,
  by-id `completion_date` / `post_completion_observed_passes`). A project is
  counted only when DPWH records it completed and a dated Sentinel-1 pass
  after that completion date still observed water at the recorded location.
  The only dated observed extent is Carina 2024, so this is bounded to that
  event. It is not a finding of project failure.
- Confidence honesty (`allocation_low_confidence_php`, `share_low_confidence`).
  The share of a province's allocation resolved only by province-text fallback
  because the project carried no usable coordinate. A higher share means the
  province figure is coarser, stated rather than hidden.
- COA cross-reference (`coa_flagged_findings_count`, `coa_findings`,
  `coa_source_orgs`; by-id `coa_flagged` / `coa_finding` / `coa_source`).
  Compiled from public COA/Ombudsman releases and reputable PH news, every row
  individually cited in `pipeline/_coa_flagged.json` and gated by
  `scripts/check_coa_cited.py`. `contract_id` is null in the compiled set, so
  the province count is the signal; a per-project tag is set only on a
  confident project-description match. FloodWatch does not independently
  verify and makes no accusation.
- Satellite corroboration (`satellite_checked_count`,
  `satellite_no_change_rate`; by-id `satellite_checked` /
  `built_change_signal`). Coarse Sentinel-1 VH built-change corroboration at
  the recorded coordinate from `pipeline/satellite_verify.py`, cached in the
  committed `pipeline/_satellite_verify_cache.json`. Coverage is a resumable
  sample that grows with the weekly refresh. Absence of a change signal is
  not evidence of a missing project: the recorded coordinate itself may be
  wrong (the MYPS problem). Indicative only.

`_meta` gains `temporal_rule`, `confidence_rule`, `coa_rule`, `coa_source`,
`satellite_rule`, `satellite_method`, each the verbatim rule string the UI
renders as the caveat for its surface. A weekly
`.github/workflows/refresh-accountability.yml` re-pulls the BetterGovPH
snapshot, runs the same governance gates, and deploys via Vercel Git on merge
to main. Language stays "flagged for review" / "warrants independent
investigation"; never "ghost", "failed", "fraud", or "caused".
