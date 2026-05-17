# GhostWatch Pattern Study: Reusable Implementations for Flood-Control Accountability

**Date:** 2026-05-17  
**Scope:** Extracting satellite-verification and conservative-language patterns from ghostwatch for FloodWatch v1.2+ flood-control accountability wave  
**Source repos:** `github.com/xmpuspus/ghostwatch` (primary), `/Users/xavier/Desktop/sar-ghostwatch` (SAR research branch, unpublished)

---

## I. GhostWatch Thesis and Dual-Repository Structure

### What GhostWatch Is

GhostWatch is an **automated satellite-verification pipeline** that cross-references 248,220 Philippine DPWH government infrastructure contracts against Sentinel-2 optical satellite imagery to surface projects reported as complete with no visible construction evidence. The core thesis: official completion claims are verifiable or falsifiable at 10-meter resolution from space without manual field audits.

**Key outputs:**
- 214,747 geolocated projects mapped and verified
- 5-class classification: `CONSTRUCTION_DETECTED`, `VEGETATION_CLEARED`, `PARTIAL_CONSTRUCTION`, `NO_CHANGE`, `INSUFFICIENT_DATA`
- Flag logic: status="completed" + classification="NO_CHANGE" + confidence ≥ 0.70 → "flagged for review"
- Dashboard + API + CLI + Python library

### The Two Local Directories vs Remote

| Directory | Purpose | Branch Status | Remote |
|-----------|---------|---------------|--------|
| `/Users/xavier/Desktop/ghostwatch/` | **Canonical** — live deployed code | main | github.com/xmpuspus/ghostwatch (git-tracked) |
| `/Users/xavier/Desktop/sar-ghostwatch/` | **Research** — Sentinel-1 SAR extension | Untracked (no git remote) | Standalone docs + paper outline |

**Key distinction:** The canonical ghostwatch uses **Sentinel-2 optical only**. The sar-ghostwatch directory (not deployed) contains the **research phase** for a companion paper (`paper-outline.md`) that adds Sentinel-1 SAR (dual-polarization VV/VH backscatter) + omnibus change-point testing + InSAR coherence to resolve cloud-masked areas. This dual-sensor approach is highly relevant for FloodWatch's monsoon-zone flood-control verification.

---

## II. Data Sourcing: Government Procurement + Geolocation Strategy

### Government Data Ingestion: The Adapter Pattern

**File:** `/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/philippines.py` (lines 71–256)

GhostWatch uses an **adapter-based ingestion strategy** that normalizes heterogeneous government data schemas into a common `BaseAdapter` interface:

1. **Source:** DPWH dataset from HuggingFace: `bettergovph/dpwh-transparency-data` (248,220 records, Parquet)
2. **Download:** Resilient curl-based fetch (lines 76–124) with 3-attempt retry + exponential backoff, fallback to HuggingFace datasets library
3. **Column mapping:** Dynamic detection of column variants (camelCase, snake_case, multiple names per field) — e.g., `contractId | project_id | projectid` all map to the target `project_id` field (lines 24–51)
4. **Status normalization:** 20+ variants ("completed", "finished", "100%") → 5 canonical values (lines 54–60)
5. **Type classification:** Keyword-based project type from title if missing (lines 62–68, 248–255): road, bridge, flood_control, building, water
6. **Geolocation extraction:** Separate logic for dict-based location fields (province/region nested in location dict) vs flat lat/lon columns (lines 232–246, 193–202)

**Why this matters for FloodWatch:** The adapter pattern is **fully reusable**. For a flood-control accountability wave, you'd create a `FloodControlAdapter` that:
- Ingests DBM-Bayanihan flood-project records (currently API-gated; the adapter handles auth)
- Maps contractor records to DPWH/budget source
- Normalizes progress indicators ("design", "under construction", "completed", "abandoned")
- Fills missing coordinates via gazetteer (next section)

**Handling PH Civic-Data Failure Modes:**
- **API 401 / token-gated access:** The adapter already handles timeout + fallback (lines 84–124). For token-gated services, add JWT handling in the fetch method before curl
- **Missing coordinates:** Defaults to None and skips the project from satellite analysis (line 195–202), but the record still loads into the dashboard for manual verification
- **Stale / inconsistent schema:** Column detection via `detect_columns()` inherited from BaseAdapter (not shown but called line 152) handles this automatically

### Geolocation: Gazetteer + Confidence Scoring

**Critical finding:** GhostWatch does **NOT implement a gazetteer for location text → coordinates**. All DPWH records come pre-geolocated from the HuggingFace dataset (lat/lon columns). The 248,220 → 214,747 discrepancy (86.5% with coordinates) is due to missing or null values, not failed geocoding.

**For FloodWatch flood-control projects without coordinates**, the reusable pattern would require:

1. **Primary:** PSA PSGC (Philippine Standard Geographic Code) — barangay-to-coordinates mapping
   - Not publicly available as a simple CSV; DOST-ASTI has a QGIS layer
   - Fallback: Nominatim (OpenStreetMap) via geopy library
   - Pattern: `from geopy.geocoders import Nominatim; geocoder.geocode("Brgy X, Municipality Y")`

2. **Confidence decay:** Mark geocoded locations with a `geolocation_confidence` field (0.0–1.0):
   - Exact coordinate in source data → 1.0
   - Barangay centroid from PSGC → 0.8
   - Municipality centroid from fuzzy match → 0.6
   - Pass this into the satellite verification as a downweight on confidence scores

**Not reusable (GhostWatch-specific):** The DPWH dataset's location field structure (province/region as nested dict) is an artifact of that specific HuggingFace dataset; your next source will have a different structure. Abstracting the `_extract_location()` method to accept a config dict (JSON path rules) would make it portable.

---

## III. Satellite Verification: The Optical Method (Reusable Core)

### Spectral Indices: Sentinel-2 Band Math

**Files:**
- `/Users/xavier/Desktop/ghostwatch/ghostwatch/core/indices.py` (lines 8–51)
- `/Users/xavier/Desktop/ghostwatch/ghostwatch/core/classifier.py` (lines 23–81)

GhostWatch computes **three spectral indices** from Sentinel-2 10-meter bands:

| Index | Formula | Detects |
|-------|---------|---------|
| **NDBI** (Normalized Difference Built-up) | `(SWIR − NIR) / (SWIR + NIR)` | Concrete, asphalt, roofing. Increases when built-up area expands. |
| **NDVI** (Vegetation) | `(NIR − Red) / (NIR + Red)` | Vegetation density. Decreases when land is cleared or paved. |
| **BSI** (Bare Soil) | `((SWIR + Red) − (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))` | Exposed bare earth during site clearing/excavation. |

**Bands used (Sentinel-2):** B2 (Blue), B4 (Red), B8 (NIR), B11 (SWIR)

The indices are computed as **90-day cloud-masked median composites** (via Google Earth Engine) for both before and after periods. Change is computed as `after_index − before_index`.

**Reusable for FloodWatch flood-control:** 
- NDBI detects dike/levee construction (built-up change)
- NDVI detects land clearing before construction
- BSI detects earthmoving / excavation
- The **exact formulas and band combinations** are directly reusable — Sentinel-2 is the same satellite

**Not reusable:** The 90-day median composite window is specific to DPWH optical data quality. For flood-control projects in the monsoon belt (June–October), a **wet-season 90-day window produces `INSUFFICIENT_DATA` in ~15–20% of AOIs** (per the sar-ghostwatch paper, lines 49–50). FloodWatch should test whether a **longer pre/after window (6–12 months)** or **dry-season windowing** is needed.

### Change Classification Logic

**File:** `/Users/xavier/Desktop/ghostwatch/ghostwatch/core/classifier.py` (lines 23–81)

The classification logic is a **nested threshold tree** with confidence scoring:

```
IF (NDBI_delta > 0.10 AND NDVI_delta < -0.15):
    CLASS = CONSTRUCTION_DETECTED
    confidence = avg(scaled_NDBI, scaled_NDVI); +0.15 if BSI also high
ELSE IF (NDVI_delta < -0.15 AND NDBI_delta ≤ 0.10):
    CLASS = VEGETATION_CLEARED
    confidence = scaled_NDVI × 0.70
ELSE IF (NDBI_delta > 0.10 AND NOT NDVI_delta < -0.15):
    CLASS = PARTIAL_CONSTRUCTION
    confidence = scaled_NDBI × 0.50
ELSE IF (abs(NDBI_delta) > 0.05 OR abs(NDVI_delta) > 0.075):
    CLASS = PARTIAL_CONSTRUCTION (weak)
    confidence = max(scaled_NDBI, scaled_NDVI) × 0.30
ELSE:
    CLASS = NO_CHANGE
    confidence = 1.0 − max(abs(NDBI_delta), abs(NDVI_delta))
```

**Confidence scaling:** `min(1.0, abs(delta) / (threshold × 3))` — capped at 1.0, so NDBI_delta=0.30 (3x threshold) gives confidence ≈ 1.0; NDBI_delta=0.12 gives ~0.4.

**Reusable for FloodWatch:**
- The threshold structure is **directly reusable** for flood-control dikes/levees (which are built-up + vegetation cleared)
- However, **test the thresholds against 30–50 hand-verified flood-control AOIs** before going to production. Dikes have lower NDBI magnitude than roads (narrower, sometimes grass-covered), so the 0.10 NDBI threshold may be too strict.
- The confidence formula is sensible but **arbitrary**; you may need to retune based on false-positive / false-negative trade-offs.

**Configurable thresholds:** All three thresholds are in `/Users/xavier/Desktop/ghostwatch/ghostwatch/config.py` (GHOSTWATCH_NDBI_CHANGE_THRESHOLD, etc.) and can be overridden via `ghostwatch.yaml` or env vars. This is the pattern to adopt.

### Ghost Project Flag Logic

**File:** `/Users/xavier/Desktop/ghostwatch/ghostwatch/core/classifier.py` (lines 84–117)

The **flag decision** is binary and conservative:

```
IF status == "completed":
    IF classification == "no_change" AND confidence >= 0.70:
        flagged = TRUE, reason = "completed_no_satellite_change"
    ELSE IF classification == "vegetation_cleared" OR 
            (classification == "partial" AND confidence < 0.30):
        flagged = TRUE, reason = specific
    ELSE:
        flagged = FALSE
ELSE:
    flagged = FALSE, reason = "project_not_completed"
```

**Key detail:** The `flagged` status depends on **reported status from the government record**, not on the satellite evidence alone. A project with zero visible construction is only flagged if it claims to be completed. Ongoing projects with no visible change are not flagged.

**Reusable for FloodWatch:** This is the **core accountability pattern**. For flood-control projects:
- Flag if reported status = "completed" but satellite shows no change
- Do NOT flag if status = "ongoing" or "in design" even if no change visible
- This prevents false accusations of projects that are legitimately ahead of schedule or not yet started

---

## IV. Satellite Verification: The SAR Extension (sar-ghostwatch)

**Files:** `/Users/xavier/Desktop/sar-ghostwatch/paper-outline.md`, `critical-risks.md`, `viral-post-draft.md`

### Why SAR Matters for Monsoon Regions

GhostWatch's Sentinel-2 optical method fails catastrophically in monsoon environments:
- **200+ cloudy days/year in the Philippines** (monsoon June–October coincides with disaster-relief construction peak)
- **90-day cloud-masked median composites** still return `INSUFFICIENT_DATA` for ~15–20% of AOIs in the monsoon belt and Cordillera
- **Underground / sub-pixel structures** remain invisible at 10m resolution

**Solution:** Sentinel-1 SAR (Synthetic Aperture Radar)
- **Cloud-transparent:** C-band microwaves penetrate clouds; works day/night
- **Same 10-meter resolution** as Sentinel-2
- **Dual-polarization:** VV (vertical) + VH (vertical-horizontal cross-pol)
- **6-day revisit** over the Philippines (now that Sentinel-1C/1D constellation is live as of Nov 2025)
- **Free:** Copernicus Copernicus data-space

### SAR Features for Construction Detection

**Paper (lines 143–175):**

Per 500-meter buffer around each project coordinate:

| Feature | Computation | What it detects |
|---------|-------------|-----------------|
| **VV/VH backscatter change** | `VV_after_dB − VV_before_dB` | Intensity change in built-up areas. Metal/concrete scatter increases. |
| **Dual-pol ratio** | `(VH/VV)_after − (VH/VV)_before` | Structural orientation change; depolarization from irregular surfaces. |
| **Coefficient of variation (REACTIV)** | Rolling 12-month CV of backscatter | Temporal stability; decreases when structure added. |
| **Omnibus change-point test** (Conradsen et al. 2016) | Statistical test on dual-pol stack | Detects significant change regardless of magnitude; less threshold-sensitive than index delta. |
| **InSAR coherence change** | `γ_pre − γ_post` on 12-day burst pairs | Phase-based signal; indicates ground deformation or new scatterers. Generated on-demand via ASF HyP3. |

### SAR Limitations in Tropics (The Honest Assessment)

**Critical risks (from `critical-risks.md`):**

1. **Small structures below SNR:** DPWH flood-control items (pumping stations, small dikes) are 5–20m linear extent. At 10m SAR resolution, a single structure's backscatter delta can be below 2–3 dB (confused with soil-moisture noise). **Risk 1** flags this as potentially **method-fatal** if > 60% of portfolio is sub-10m structures.

2. **Monsoon soil-moisture confound:** Wet-soil VV can shift 2–3 dB with zero structural change. If wet-to-wet comparison is unwindowed, false positive rate spikes. **Risk 2** mitigation: mandatory wet-to-wet and dry-to-dry windowing; IMERG rainfall as a covariate in the classifier.

3. **InSAR coherence below SNR in vegetation:** 12-day coherence over vegetated tropical surfaces often medians below 0.2. At that level, coherence change has almost no detection power for a 10m structure (new concrete replacing bare grass). **Risk 4** mitigation: stack ≥ 6 coherence pairs; use coherence std over the AOI buffer rather than point value.

4. **GEE compute quota:** Sentinel-1 dual-pol 36-month 248k-AOI stack hits GEE Community tier ceilings fast. **Risk 5** mitigation: aggressive pre-reduction (per-AOI monthly tables, not pixel stacks); apply for Earth Engine Research Credits.

### What SAR Actually Recovers (Phase 2 Placeholder)

Per `paper-outline.md` (lines 225–234), the paper's primary metric is **recovery rate:**

> "Fraction of AOIs where optical returns `insufficient_data` but SAR returns a confident class (confidence ≥ 0.70)"

Expected recovery: **30–50%** in monsoon-prone regions. If actual recovery is < 15%, the SAR addition is marginal; the paper pivots to "SAR as cloud-fallback complement, not replacement."

**Not yet computed** (paper is in Phase 2); the exact recovery rate, precision/recall on hand-verified holdout, and fused-classifier gain over optical-alone are placeholders. This is **research-stage output**, not production-ready.

### Reusable Pattern: Pre-Production Gate

The `critical-risks.md` document itself is a **reusable risk-gating framework** for multi-phase remote-sensing work:

- **Phase 1 gates (Week 2):** Method signal-to-noise on a small sample (200 AOIs). Triggers early pivot if SNR is too low.
- **Phase 2 gates (Week 3):** Full-population scan; descriptive stats only. No precision/recall claimed yet.
- **Phase 3 gates (Week 6–8):** Hand-verified holdout; fusion classifier; publishable metrics.

**For FloodWatch flood-control wave:** Adopt this phased-gating structure. Phase 1 should verify whether flood-dike NDBI thresholds work on 30–50 real projects before committing to Phase 2 satellite batch.

---

## V. Conservative Language & Legal Posture Implementation

### The Accountability Problem

GhostWatch's core claim — "a project flagged for review is a statistical indicator that warrants further investigation" — is **legally adjacent to accusation**. In the Philippines, any named project associated with "ghost" or "unbuilt" language can trigger defamation suits (cyber libel under RA 10175 carries criminal penalties). Xavier's CLAUDE.md for ghostwatch explicitly flags this (Risk 7, `critical-risks.md` lines 135–150).

### Language Architecture

**File:** `/Users/xavier/Desktop/ghostwatch/api/routers/analytics.py` (lines 10–12)

The implementation uses a **three-layer disclaimer + aggregation + careful terminology strategy:**

#### Layer 1: Endpoint-Level Disclaimer

Every analytics endpoint returns a `disclaimer` field:

```json
{
  "data": {...},
  "disclaimer": "Statistical indicators derived from public data. Patterns may have legitimate explanations.",
  "meta": {...}
}
```

This disclaimer is **hardcoded in the API response** (not optional), not in the frontend. Clients cannot remove it. **File path:** `/Users/xavier/Desktop/ghostwatch/api/routers/analytics.py` (line 10–12, injected into every `/analytics/*` response).

**Reusable:** Use the same pattern for FloodWatch. Embed disclaimers at the API layer, not the UI layer, so they're impossible to strip.

#### Layer 2: Aggregation Only (No Entity Names)

The API **never exposes project-level names, contractors, or LGUs** in any "flagged" or "ghost" output. All public outputs are **aggregated by region, project type, budget tranche**:

```
GET /analytics/regional
Response: {
  "data": [
    {
      "region": "Region III",
      "total_projects": 12400,
      "flagged_for_review": 340,
      "flagged_rate": 2.7,
      ...
    }
  ],
  "disclaimer": "..."
}
```

Compare against:

```
GET /projects?verification=GHOST_PROJECT
Response: {
  "data": [
    {
      "id": "DPWH-12345",
      "title": "Panguil Bay Bridge",        // ← named project
      "contractor": "XYZ Corp",           // ← named contractor
      "flagged_for_review": true,         // ← accusatory status
      "satellite_evidence": "no_change"
    }
  ]
}
```

**GhostWatch never returns the second format in production.** The project detail endpoint (`/projects/{id}`) does return names, but only via **direct project lookup** (you must know the ID), not via "list all flagged projects" — a deliberate friction layer.

**In code:** `/Users/xavier/Desktop/ghostwatch/api/services/data_service.py` (lines 253–316) computes regional stats only; project-level detail is in `get_project()` (lines 88–118 of `projects.py`), which is name-rich but requires individual lookup.

**Reusable:** For FloodWatch flood-control accountability, expose:
- ✅ Aggregated regional flagging rates
- ✅ Budget-tranche breakdowns ("PHP 100M–500M projects: 5% flagged")
- ✅ Project-type flagging rates ("Dikes: 8% flagged; Pumping stations: 3%")
- ✗ Named project lists with "flagged" status
- ✗ Contractor-specific rollups (creates defamation vector)

#### Layer 3: Terminology (Never "Ghost", Always "Flagged")

**In code:** `/Users/xavier/Desktop/ghostwatch/api/services/satellite_service.py` (line 111–112):

```python
# conservative label — "ghost project" is an editorial conclusion, not an API assertion
"flagged_for_review": int(...)
```

The API never uses the word "ghost" in the JSON output. Dashboard UX may use "ghost" as a shorthand, but the **API contract** uses "flagged_for_review" + "no_satellite_evidence" + "insufficient_data" — factual descriptors.

README (line 63) uses "ghost projects" in the headline but immediately qualifies:

> "A project flagged for review is a statistical indicator that warrants further investigation — it is not a finding of fraud or irregularity."

**Reusable:** Use "flagged for review" or "warrants investigation" in all API/UI copy. Reserve "ghost" for editorial commentary (blog posts, LinkedIn) where you can provide full context. Never use it in automated systems.

### Implementation Checklist

To adopt GhostWatch's conservative posture in FloodWatch flood-control wave:

- [ ] Every endpoint with flagging data includes a `disclaimer` field in the response
- [ ] No named entity lists ("show me all flagged contractors")
- [ ] Flagging output aggregated to region/type/budget-tranche level
- [ ] Use "flagged for review" in API/UI; "warrants investigation" in documentation
- [ ] All sample AOIs shown (project detail, methodology slides, blog posts) are anonymized or use confirmed-built reference projects
- [ ] Pre-launch legal review if any aggregate exceeds PHP 100M per flag
- [ ] Grep the codebase before every release for entity names in flagging output

**File path:** `/Users/xavier/Desktop/ghostwatch/api/routers/analytics.py` is the model. Copy this pattern exactly.

---

## VI. Architecture: Graph Model, Integrity Gates, CI Discipline

### System Architecture (No Graph DB)

Contrary to the civic-tech-ph memory (which notes InfraWatch PH uses Neo4j on ports 7475/7688), **GhostWatch does NOT use a graph database**. The CLAUDE.md explicitly states:

> "No Neo4j — that stays in InfraWatch. GhostWatch = satellite verification only"

Data model is **flat Parquet** (columnar):
- Raw DPWH data downloaded to `data/raw/dpwh_projects.parquet`
- Normalized data in `data/processed/` (schema: project_id, title, contractor, contract_amount, lat, lon, status, …, verification_status, flagged_for_review, confidence)
- Satellite verification results as separate CSV/Parquet joined on project_id

**Reusable:** The simplicity is a feature. No graph traversal overhead, pure filtering/aggregation. For FloodWatch accountability, stay flat unless you need cross-project relationships (e.g., "all projects funded by the same contractor").

### Pipeline & Integrity Gates

GhostWatch's CI gates (from the repo's GitHub Actions + tests):

1. **Data integrity:** `tests/test_classifier.py` (lines 96–166) has truth-table tests for the classifier logic. All 14 test cases cover the flag decision tree (completed+no_change → flagged; ongoing+no_change → not flagged; etc.). These gates prevent regression on the core business logic.

2. **Index computation:** `tests/test_indices.py` has formula validation. NDBI, NDVI, BSI formulas are tested against known inputs (e.g., `compute_ndbi(swir=0.28, nir=0.21)` should yield ~0.143).

3. **Disclaimer presence:** `/Users/xavier/Desktop/ghostwatch/tests/test_api.py` (lines 279–306) has 6 test cases that assert every analytics endpoint returns a `disclaimer` field. This is a **legal gate**: any code change that removes the disclaimer fails CI.

**Reusable gates for FloodWatch:**
- [ ] Classifier logic truth table (test all flag conditions)
- [ ] Satellite formula validation (NDBI, NDVI, BSI on known band values)
- [ ] Disclaimer presence test (every flagging endpoint must have it)
- [ ] Anonymization test (grep for contractor/LGU names in flagging output; fail if found)
- [ ] Threshold consistency (verify YAML config thresholds are loaded, not hardcoded)

**Implementation:** Copy the test structure from `/Users/xavier/Desktop/ghostwatch/tests/` directly.

### Configuration Management

**File:** `/Users/xavier/Desktop/ghostwatch/ghostwatch/config.py`

All thresholds are **Pydantic Settings** loaded from environment variables, `.env` file, or `ghostwatch.yaml` override:

```
GHOSTWATCH_NDBI_CHANGE_THRESHOLD=0.10
GHOSTWATCH_NDVI_CHANGE_THRESHOLD=0.15
GHOSTWATCH_GHOST_CONFIDENCE_THRESHOLD=0.70
GHOSTWATCH_GEE_PROJECT="your-gee-project-id"
```

This pattern means **thresholds can be tuned without code changes**. A flood-control dike dataset with different spectral properties can override the optical thresholds just by changing the YAML file.

---

## VII. Frontend & Dashboard Patterns (Minimal)

GhostWatch's frontend is **Next.js 14**. The key UX patterns for accountability:

1. **Before/After Slider:** Side-by-side satellite imagery comparison (not shown in code, but mentioned in README). This visual evidence is the **strongest disclaimer** — users see the actual satellite data and judge for themselves.

2. **Map with Filter:** Interactive map of all 214,747 geolocated projects, filterable by status/verification/region. No "flagged" list sorting; users must consciously filter to see flagged projects.

3. **Methodology Page:** Full explanation of spectral indices, thresholds, confidence scoring, and limitations. This is **required reading** before any dashboard use.

4. **Dark Theme:** The README mentions "dark cinematic UI" — this is a deliberate design choice to avoid the impression of an official government dashboard. The dark, research-forward aesthetic signals "exploratory tool, not final verdict."

**Reusable for FloodWatch:**
- [ ] Before/after satellite slider (same Sentinel-2 bands or SAR VV/VH)
- [ ] Interactive map, no pre-sorted "flagged" list
- [ ] Methodology page prominently linked from hero
- [ ] Dark / neutral theme to avoid appearing official

---

## VIII. Specific Reusable Patterns for FloodWatch Flood-Control Accountability Wave

### Summary Table: What to Lift, What to Skip, What to Adapt

| Pattern | GhostWatch File | Status | For FloodWatch | Why / Notes |
|---------|-----------------|--------|---|---|
| **Adapter-based data ingestion** | `adapters/philippines.py` | ✅ Directly reusable | Copy for DBM-Bayanihan flood projects | Column variant detection, status normalization, geolocation extraction all transfer. Add JWT auth if source requires token. |
| **Spectral indices (NDBI, NDVI, BSI)** | `core/indices.py` | ✅ Directly reusable | Use same formulas for flood-dike detection | Sentinel-2 bands are universal. Test thresholds on 30–50 hand-verified dike AOIs before production. |
| **Classification logic** | `core/classifier.py` | ⚠️ Requires tuning | Adapt for dike-specific thresholds | 0.10 NDBI threshold may be too strict for narrow dikes. Lower to 0.07–0.08; test empirically. |
| **Ghost flag decision tree** | `core/classifier.py` | ✅ Directly reusable | status="completed" + no_change → flag | This is the core accountability gate. Use as-is. |
| **SAR backscatter + omnibus test** | `sar-ghostwatch/paper-outline.md` | ⚠️ Research-stage | Optional Phase 2 for monsoon-belt projects | Not production-ready yet. Use only if optical confidence < 0.60 in test phase. Document recovery rate empirically. |
| **Disclaimer endpoint responses** | `api/routers/analytics.py` | ✅ Directly reusable | Embed `"disclaimer": "..."` in every flagging response | Copy the exact disclaimer text or use a variant. Make it non-optional (required field in response schema). |
| **Aggregation-only output** | `api/services/data_service.py` | ✅ Directly reusable | Never expose project names in flagging results | Expose region/type/budget rollups only. Individual project lookup OK, but no "list all flagged projects" endpoint. |
| **Conservative terminology** | README, API | ✅ Directly reusable | "Flagged for review", never "ghost" in system outputs | Use "ghost" only in editorial context (blog posts, LinkedIn) with full caveats. |
| **Classifier truth-table tests** | `tests/test_classifier.py` | ✅ Directly reusable | Test all flag decision branches | Copy test structure. Add dike-specific edge cases (narrow structures, partially completed). |
| **Disclaimer presence CI gate** | `tests/test_api.py` lines 279–306 | ✅ Directly reusable | Fail build if disclaimer missing from endpoints | This is a legal gate. Non-negotiable. |
| **Configuration as Pydantic Settings** | `ghostwatch/config.py` | ✅ Directly reusable | Threshold tuning via .yaml or env vars | Enables rapid A/B testing without code deploy. |
| **Before/after satellite slider UI** | web/ (not in code dump) | ⚠️ Architecture reference | Next.js 14 with side-by-side imagery | Reuse the pattern, not the component. FloodWatch already has satellite integration. |

### Concrete Bullet List: Exact Implementation Steps

1. **Data ingestion (Week 1):**
   - Copy `/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/base.py` and `philippines.py` as a starting point
   - Create `/floodwatch/adapters/flood_control.py` subclassing `BaseAdapter`
   - Implement `fetch()` to handle DBM-Bayanihan source (or whatever flood-project registry you use)
   - Implement `parse()` with project-type keyword extraction for flood-control items (dike, pumping station, drainage channel, etc.)
   - Add geolocation confidence scoring (1.0 for source coords, 0.8 for gazetteer-geocoded)

2. **Satellite verification (Week 2):**
   - Copy `core/indices.py` and `core/collector.py` wholesale; no changes needed
   - Copy `core/classifier.py` to `core/classifier_flood.py`
   - Adjust thresholds: test NDBI 0.07–0.08 for narrow dikes (vs 0.10 for roads)
   - Copy the `is_ghost_project()` logic exactly; add a new enum class `FloodProjectStatus` for dike-specific states if needed

3. **API & conservative language (Week 3):**
   - Copy `/api/routers/analytics.py` and `/api/routers/satellite.py` as templates
   - Create `/api/routers/flood_analytics.py` with regional flood-project flagging stats
   - Embed `"disclaimer": "Statistical indicators derived from public data. Patterns may have legitimate explanations."` in every response
   - Create `/api/routers/flood_detail.py` for individual project lookup (name-rich, but requires direct ID lookup)
   - Never implement a `/api/flood/flagged` endpoint (list all flagged projects); friction is intentional

4. **CI integrity gates (Week 4):**
   - Copy `/tests/test_classifier.py` structure
   - Add truth-table tests for dike-specific thresholds (narrow structure, slow vegetation recovery, partial completion)
   - Copy `/tests/test_api.py` lines 279–306; add test that asserts `disclaimer` present in all flood_analytics endpoints
   - Add anonymization test: `grep -r "contractor\|LGU" api/routers/ | grep -v comments` should return 0 in flagging endpoints

5. **Configuration (Week 2):**
   - Copy `ghostwatch/config.py` structure
   - Add flood-specific settings: `FLOOD_NDBI_THRESHOLD=0.07`, `FLOOD_DIKE_CONFIDENCE_THRESHOLD=0.75`
   - Create `/floodwatch.yaml` with tunable thresholds

6. **Optional SAR Phase (Month 2, if monsoon coverage is critical):**
   - Reference `/Users/xavier/Desktop/sar-ghostwatch/paper-outline.md` Phase 1 gates (lines 194–200)
   - Run SAR backscatter on 200 test AOIs (50 built dikes, 50 flagged, 100 mixed)
   - Measure SAR-only precision vs optical-only on a hand-verified subset
   - Only proceed if SAR recovery rate > 25% on monsoon AOIs; otherwise, accept optical-only with longer windowing

---

## IX. The Single Most Important Pattern

**The most load-bearing reusable pattern is the conservative-language governance architecture (Layer 1–3 above).**

GhostWatch's legal safety comes not from fancy engineering — it comes from **structural friction built into the data flow**. The disclaimer is non-optional (API layer, not frontend). Flagging results never expose names (aggregation-only). The flag decision is defined clearly in code (truth table tested in CI). The terminology is controlled ("flagged", never "ghost").

**For FloodWatch:** A flood-control accountability dashboard that surfaces billions of pesos in potentially unbuilt infrastructure is orders of magnitude more politically sensitive than an optical construction-verification tool. You need Xavier's three-layer governance model (disclaimer + aggregation + terminology) baked in from the API schema onward, not bolted on to the UI later. **Copy the conservative language pattern directly, especially the CI gate that asserts disclaimer presence on every response.**

---

## X. Things That Are NOT Reusable (Don't Duplicate)

1. **Sentinel-2 + Google Earth Engine integration:** The GEE authentication, composite generation, and index computation are tightly coupled to Google's API. If FloodWatch ever needs a different satellite source or local compute, rewriting `collector.py` is the right move.

2. **DPWH-specific schema and column mappings:** The HuggingFace DPWH dataset has a unique structure (nested province/region in a location dict, specific column names). The next government dataset (DBM, LGU, private contractor) will have a different schema. The adapter pattern absorbs this; don't hard-code DPWH field names anywhere else.

3. **The sar-ghostwatch paper methodology:** The omnibus change-point test (Conradsen et al.) and HyP3 coherence pipeline are only applicable if FloodWatch decides to pursue multi-sensor verification. This is research-stage output (Phase 1–2 gates not yet met). Reference the paper's risk framework, but don't port the SAR code until recovery rate is empirically validated.

4. **The Panguil Bay bridge case study:** GhostWatch's headline example (PHP 6.7B bridge with visible construction) is iconic but DPWH-specific. FloodWatch needs its own canonical dike or pumping station example — find a verified-built flood-control project and use that instead.

---

## Appendix: File Path Quick Reference

| Purpose | Path | Key Lines |
|---------|------|-----------|
| Adapter base class | `/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/base.py` | Subclass this |
| DPWH adapter (copy pattern) | `/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/philippines.py` | 71–256 |
| Spectral indices (copy wholesale) | `/Users/xavier/Desktop/ghostwatch/ghostwatch/core/indices.py` | 8–51 |
| Classification logic (tune thresholds) | `/Users/xavier/Desktop/ghostwatch/ghostwatch/core/classifier.py` | 23–117 |
| Config (copy structure) | `/Users/xavier/Desktop/ghostwatch/ghostwatch/config.py` | - |
| Disclaimer implementation | `/Users/xavier/Desktop/ghostwatch/api/routers/analytics.py` | 10–12 |
| Aggregated stats (copy) | `/Users/xavier/Desktop/ghostwatch/api/services/data_service.py` | 253–316 |
| Classifier tests (copy + adapt) | `/Users/xavier/Desktop/ghostwatch/tests/test_classifier.py` | 96–166 |
| Disclaimer presence test (copy) | `/Users/xavier/Desktop/ghostwatch/tests/test_api.py` | 279–306 |
| SAR research (reference only) | `/Users/xavier/Desktop/sar-ghostwatch/paper-outline.md` | - |
| SAR risk gates (reference) | `/Users/xavier/Desktop/sar-ghostwatch/critical-risks.md` | 1–248 |

---

## Summary

GhostWatch is a battle-tested, production-deployed satellite-verification pipeline with three reusable cornerstones:

1. **The adapter pattern** for heterogeneous government data ingestion
2. **The spectral-index satellite verification algorithm** (NDBI/NDVI/BSI thresholds + confidence scoring)
3. **The conservative-language governance architecture** (disclaimer fields, aggregation-only output, controlled terminology, CI gates)

For FloodWatch's flood-control accountability wave, you should directly copy patterns 1–3, tune the optical thresholds empirically on 30–50 hand-verified dike AOIs, and defer SAR until optical confidence is validated in monsoon zones. The governance architecture is non-negotiable — it's the legal safety net that makes publishing infrastructure accountability data defensible.

The sar-ghostwatch branch offers a mature risk-gating framework and methodological depth for future multi-sensor work, but the SAR pipeline itself is research-stage and should not ship to production until Phase 1 gates confirm feasibility.
