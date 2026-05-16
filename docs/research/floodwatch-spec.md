# FloodWatch.PH - end-to-end build spec

Status: locked. This is the source of truth for the v1.0.0 build. It mirrors the
SolarMap.PH playbook section-for-section, adapted to the honest fact that flooding
is *temporal* where rooftop solar is *static*. Do not relitigate the locked
decisions in §3 - they are the headline-honesty contract.

Seed: `~/Desktop/solar-map-ph/docs/research/next-ideas.md` (FloodWatch entry, idea #1,
score 27/30) and the locked memory `project_floodwatch-ph-spec.md`.

---

## 1. One-paragraph thesis

Philippine communities flood repeatedly. The official hazard maps (UP NOAH /
Project NOAH, PAGASA, MGB) and the NDRRMC post-event damage assessments do not
agree with each other or with what satellites actually observed flooding. FloodWatch.PH
is an open, reproducible, independent measurement of *observed* flood extent during
real typhoons, and a recurrence-prone classifier that flags barangays that flood
again and again but are **not** on the official hazard layer. Inputs are 100%
publicly licensed. The civic output is the gap: where the water goes vs where the
maps say it goes.

## 2. The two-track architecture (honest, do not collapse)

Flood is an event, not a fixture. A single high-resolution snapshot - the SolarMap
move - cannot work, because the flood is gone by the next clear pass and optical
satellites are cloud-blocked by the very typhoon that causes the flood. So the
product is two tracks with two different jobs. This split is the honest answer and
the README reports their metrics **separately** (never averaged into one number).

### Track A - Event track (the GIF / the demo)

- **Sensor:** Sentinel-1 C-band SAR (`COPERNICUS/S1_GRD`), VV + VH, IW mode,
  Copernicus open / free. SAR penetrates typhoon cloud cover - it is the *only*
  sensor that sees the ground during a Philippine flood. Sentinel-2 optical is
  useless here on purpose; saying so is part of the methodology honesty.
- **Method:** classical, reproducible, no training. Per-timestep:
  1. Pull S1 GRD scenes bracketing the event; build a pre-event baseline
     composite (median of the dry weeks before) and per-date during/after images.
  2. Speckle-filter (refined-Lee / focal median), convert to dB.
  3. Otsu threshold on the VH (and VV cross-check) change image
     (`during − baseline`) to get candidate open water.
  4. Subtract the **permanent-water mask** (§3 decision 2): HAND ≤ threshold
     from MERIT Hydro `MERIT/Hydro/v1_0_1` + HydroSHEDS/JRC Global Surface Water
     occurrence ≥ 50% + OSM `natural=water`/`waterway`. Report **flood**, not
     rivers and lakes.
  5. Emit a per-timestep flood polygon GeoJSON.
- **Demo event:** MapLibre time-slider over **6 real Sentinel-1 acquisition
  dates** bracketing Super Typhoon Carina / Gaemi + the enhanced SW monsoon:
  2024-06-16 and 06-28 (dry baseline), 07-10 (pre), 07-22 and 07-30 (peak /
  recession - Carina landfall ~Jul 24), 08-03 (post), over Metro Manila +
  Bulacan + Pampanga (bbox `[120.5, 14.4, 121.4, 15.3]`). Each slider frame is
  a real acquisition date, not interpolation. Click a barangay → exposed
  population (WorldPop), building count (Microsoft GlobalML footprints), and
  whether the barangay is on the official hazard map. Carina 2024 has **no
  promptly-public official flood-extent polygon** - that absence is the civic
  vacuum the demo fills.
- **Validation event:** the Global Flood Database ends 2017, so the method is
  IoU/F1-validated against the GFD `flooded` polygon for **GFD event 4300,
  Tropical Storm Koppu / Lando, 2015-10-22, central Luzon** (54 dead, severity
  2), using the 2015-10-26 Sentinel-1 post-onset acquisition. Track A is
  parameter-free (Otsu has no fitted parameters), so it carries no train/test
  leakage; the event-disjoint holdout (§3 dec. 1) governs Track B. The
  validated method is then applied to the ungauged Carina 2024 demo event.

### Track B - Trained-model track (the SolarMap analog)

- **Substrate:** frozen Google AlphaEarth Foundations "Satellite Embedding V1"
  (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`), natively 10 m but **sampled at 300 m**
  in this pipeline (see model/fetch_embeddings.py), 64-dim, unit-norm, annual
  2017-2025, CC-BY-4.0 ("produced by Google and Google DeepMind"). This replaces
  SolarMap's CLIP-ViT-L tile-embedding step with a download - and removes the
  Esri tile-fetch + IP-throttle pain entirely (anti-throttle lesson, §3 dec. 3).
- **Head:** `sklearn.linear_model.LogisticRegression` on the 64-dim embedding,
  Platt-sigmoid calibrated on an event-disjoint holdout. Bit-exact, ~30 s,
  no GPU, deterministic, hash-verified - the exact SolarMap reproducibility chain.
- **Task:** per-pixel **flood-recurrence-prone** classification. Positives =
  points inside GFD historical flood-event footprints (2002-2017, 57 PH events),
  permanent water removed. Negatives = land points never flooded across all GFD
  events. The embedding year is fixed at **2017** (earliest AlphaEarth annual,
  contemporaneous with the GFD record end). The annual cadence is too coarse for
  a single event (Track A's job) but is ideal for "does this place's land-
  embedding signature predict it floods repeatedly".
- **Committed cache:** `model/embeddings/floodwatch_embeddings_v1.npz` (~1 MB),
  the AlphaEarth vectors sampled at every labelled point. `make train` runs
  offline from this cache, identical to SolarMap's `dataset_v4.npz`.

## 3. Locked decisions (do not relitigate)

1. **Event-disjoint holdout.** Hold out *entire typhoon events*, never random
   pixels. Random-pixel splits leak (adjacent pixels are near-duplicates) and
   inflate IoU/F1. This is the single most important honesty decision and is
   enforced by a CI gate. Holdout events are named in `model/holdout_events.json`
   and never appear in any training fold.
2. **Permanent-water masking is the integrity rule.** The product reports FLOOD,
   not rivers/lakes/sea. This is the analog of SolarMap's residential-suppression
   gate. A CI gate asserts every published flood GeoJSON has had the permanent-
   water mask applied (checked via a provenance flag + a spatial assertion that
   < X% of flood area intersects JRC permanent water).
3. **Embeddings / SAR only - never bulk raw-imagery fetch.** Bake the anti-
   throttle lesson in from day one. No Esri tile loop. Earth Engine server-side
   reduction → small client downloads only.
4. **`site/` is the Vercel root and never imports outside `site/`.** Any shared
   config a page needs is mirrored into `site/src/data/` and a verify gate
   asserts byte-identity with the canonical copy. Deploy is manual
   `cd site && vercel deploy --prod` until Git integration is verified.
5. **Privacy:** environmental data, lower RA 10173 exposure than rooftop solar,
   but exposure figures are aggregated to **barangay-level counts only** - no
   household identification, no per-building flood-status geometry tied to a
   dwelling. The PIA documents this. Conservative civic language throughout
   ("observed flood extent", "warrants verification", never "the government
   lied").
6. **Bit-exact deterministic build** from the committed ~1 MB embeddings cache;
   `make hash-verify` asserts a canonical sha256; the event-disjoint split is
   itself hash-pinned so a leaked split fails CI.

## 4. Data sources and licenses (100% public chain)

| Input | Source / GEE asset | License | Use |
|---|---|---|---|
| SAR backscatter | `COPERNICUS/S1_GRD` (Sentinel-1) | Copernicus open | Track A event flood extent |
| Annual embeddings | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` | CC-BY-4.0 | Track B recurrence head |
| Flood labels (historical) | Global Flood Database `GLOBAL_FLOOD_DB/MODIS_EVENTS/V1` (Cloud to Street, Nature 2021) | CC-BY-4.0 | Track B positives + Track A validation |
| Flood labels (event) | Copernicus EMS Rapid Mapping; UNOSAT | Copernicus / UNOSAT open | Track A validation polygons |
| Permanent water / terrain | `MERIT/Hydro/v1_0_1` (HAND), JRC Global Surface Water `JRC/GSW1_4/GlobalSurfaceWater` | open | Permanent-water mask (dec. 2) |
| Population exposure | WorldPop / Meta HRSL | CC-BY-4.0 | Barangay exposed-population denominator |
| Building exposure | Microsoft GlobalMLBuildingFootprints | ODbL-equivalent | Barangay building-count denominator |
| Barangay boundaries | PSA / OSM admin polygons | PSA public / ODbL | Click-target geography |
| Official hazard (comparison) | UP NOAH / Project NOAH / PAGASA / MGB published extents | gov public | The civic gap layer |

No paywall, no non-commercial clause anywhere. Maxar/xBD/WDPA explicitly excluded
(see next-ideas "What to avoid").

## 5. Civic thesis (the net-metering-gap analog)

SolarMap's hook was "informal solar not in the net-metering registry". FloodWatch's
hook is the structurally identical gap. **v1.0 honest scope:** the gap between
**modeled flood-proneness (Track B)** and the **historical observed flood record
(GFD)** - places the recurrence model flags as prone that have little or no
historical observed-flood coverage ("under-observed prone"). This is fully
self-contained on the 100%-public chain and needs no government layer.

The cross-reference against the **official UP NOAH / Project NOAH / PAGASA / MGB
hazard maps** is the **v1.1 extension**, deferred for a documented reason, not an
omission: those government layers are token-gated ArcGIS (`499 Token Required` on
the actual hazard leaves) or SPA-only (Project NOAH exposes no stable URLs) - the
well-documented PH civic-data failure mode. v1.0 ships the public-chain gap and
the README roadmap states this substitution honestly.

Exposure is aggregated to **city / municipality** (FAO GAUL level-2) for v1.0;
PH barangay polygons are not a clean public/EE asset, so barangay-resolution
aggregation is a documented v1.1 refinement. Language stays conservative and
every analytics surface carries the public-records disclaimer.

## 6. Repository layout (mirrors SolarMap section-for-section)

```
floodwatch-ph/
|-- event/                      # Track A: Sentinel-1 SAR event change-detection
|   |-- fetch_s1_event.py       # EE: pull S1 GRD timesteps for an event window
|   |-- flood_extent.py         # speckle filter + Otsu + permanent-water subtract
|   |-- permanent_water.py      # HAND + JRC GSW + OSM water -> mask
|   |-- events.json             # event registry (name, bbox, window, holdout flag)
|   `-- README.md
|-- model/                      # Track B: AlphaEarth embeddings + recurrence head
|   |-- embeddings/
|   |   `-- floodwatch_embeddings_v1.npz   # committed ~10MB cache (in git)
|   |-- fetch_embeddings.py     # EE: sample AlphaEarth at labelled points
|   |-- bootstrap_labels.py     # GFD/CEMS -> recurrence labels
|   |-- holdout_events.json     # event-disjoint split (hash-pinned)
|   |-- train.py                # LogisticRegression head (deterministic)
|   |-- calibrate.py            # Platt sigmoid on event-disjoint holdout
|   `-- recurrence_clf_v1.joblib           # committed, hash-verified
|-- pipeline/                   # exposure join + barangay aggregation
|   |-- exposure.py             # WorldPop/HRSL + MS footprints per barangay
|   |-- hazard_gap.py           # observed-recurrence vs official-hazard gap
|   `-- requirements.txt
|-- site/                       # Astro static site, MapLibre time-slider
|   |-- public/data/            # flood timesteps + recurrence + gap GeoJSON/JSON
|   |   |-- flood_carina_2024.geojson      # per-timestep extent FeatureCollection
|   |   |-- recurrence_prone.geojson
|   |   |-- hazard_gap.geojson
|   |   |-- barangay_exposure.json
|   |   `-- SCHEMA.md
|   |-- src/
|   |   |-- components/         # MapView (time slider), Header, Footer
|   |   |-- data/events.json    # mirrored from event/events.json (Vercel boundary)
|   |   `-- pages/              # index, map, methodology, recurrence, privacy, faq, safety
|   `-- vercel.json
|-- scripts/
|   |-- verify_clf.py           # hash-verify a joblib before joblib.load
|   |-- check_permanent_water.py# CI gate: flood GeoJSONs are permanent-water-masked
|   |-- check_event_disjoint.py # CI gate: no holdout event leaks into training
|   |-- check_no_pii.py         # CI gate: outputs are barangay-aggregate, no dwellings
|   |-- verify_release.py       # full pre-release gate runner
|   `-- plot_metrics.py         # IoU/PR/reliability figures
|-- tests/                      # pytest, no network
|-- docs/
|   |-- research/floodwatch-spec.md   # this file
|   |-- privacy-impact-assessment.md
|   |-- screenshots/                  # README hero GIF
|   `-- figures/
|-- examples/run_on_new_event.md
|-- MODEL_CARD.md  CITATION.cff  CHANGELOG.md  CONTRIBUTING.md
|-- CODE_OF_CONDUCT.md  SECURITY.md  LICENSE  Makefile  Dockerfile
|-- requirements.txt  pyproject.toml  .zenodo.json  README.md
`-- .github/workflows/ci.yml
```

## 7. Makefile contract (mirrors SolarMap)

```
make embeddings   # EE: sample AlphaEarth at labelled points -> npz cache (network)
make labels       # GFD/CEMS -> recurrence labels + event-disjoint split
make train        # LogisticRegression head from cached npz (deterministic, no net)
make hash-verify  # assert recurrence_clf_v1.joblib sha256 == canonical
make calibrate    # Platt sigmoid on event-disjoint holdout
make event        # Track A: S1 SAR flood extent for an event (network)
make exposure     # barangay exposure + hazard-gap join
make demo         # print calibrated bundle + holdout IoU/F1 summary
make verify       # full release gate runner (permanent-water, event-disjoint, PII, mirror, hash)
make test         # pytest
```

`make train` + `make hash-verify` reproduce the model bit-exact from the committed
cache with no network - the SolarMap guarantee preserved.

## 8. Honest metrics, reported separately

- **Event track:** IoU and F1 of FloodWatch Carina extent vs the GFD/CEMS polygon
  for that event, computed on **held-out events** only. Reported as
  "Track A - observed-extent agreement".
- **Recurrence model:** precision / recall / F1 at the deployed threshold on the
  event-disjoint holdout, with a reliability diagram. Reported as
  "Track B - recurrence-prone classifier".
- The README never averages these. A reader sees two numbers for two jobs.

## 9. CI gates (the integrity contract)

1. `check_permanent_water.py` - every published flood GeoJSON carries
   `_meta.permanent_water_masked == true` and < 5% of flood area intersects JRC
   ≥50%-occurrence permanent water. (Decision 2.)
2. `check_event_disjoint.py` - `holdout_events.json` events never appear in any
   training fold; the split file hash matches the value pinned in the Makefile.
   (Decision 1.)
3. `check_no_pii.py` - outputs are barangay-aggregate; no per-dwelling geometry,
   no PII property keys. (Decision 5.)
4. `site/src/data/events.json` is byte-identical to `event/events.json`.
   (Decision 4.)
5. `make hash-verify` - deterministic classifier hash. (Decision 6.)
6. Astro typecheck + build; pytest; pinned-requirements check.

## 10. Ship chain (same as SolarMap, end to end)

scaffold from template → EE Sentinel-1 + AlphaEarth pull → GFD/CEMS label
bootstrap → event-disjoint holdout → train + calibrate recurrence head +
hash-verify → SAR event change-detection for the demo → Astro+MapLibre site with
time slider → CI verify gates green → README + recorded hero GIF → CHANGELOG +
MODEL_CARD + PIA → v1.0.0 tag + GitHub release (Zenodo auto-archive) → register
floodwatch.ph + attach to Vercel → manual prod deploy → Playwright-verify the
live site → draft (do NOT post) the LinkedIn launch in the plain-technical voice.

## 11. Known external gates (honest, surfaced not hidden)

- **`floodwatch.ph` domain:** dot.ph registration is a paid web checkout with no
  CLI/API. This single step needs the owner's action + payment. Everything Vercel-
  side is prepared so the domain attaches in one step once registered.
- **Zenodo auto-archive:** requires the GitHub↔Zenodo webhook toggled on for the
  new repo in the owner's Zenodo account before the release tag. `.zenodo.json` +
  `CITATION.cff` are committed so the archive metadata is correct when enabled.
- **EE quota:** all pulls use server-side reduction and small client downloads to
  stay well under free-tier limits; if a pull throttles, it is resumable and ships
  partial with explicit `_meta.scan_status`, the SolarMap partial-ship pattern.

## 12. Scope discipline

v1.0.0 ships **one calibrated event** (Carina/Gaemi Jul 2024, Metro Manila +
Bulacan + Pampanga) as the Track A reference, and the Track B recurrence model
trained on the full GFD Philippines event history with event-disjoint holdout.
Additional events (Kristine/Trami Oct 2024, Odette 2021) are the v1.1 multi-event
extension, mirroring SolarMap's v1.0 NCR → v1.1 multi-region arc. Do not scope-
creep v1.0 into multi-event; ship the reference event calibrated and honest.
