# Model card: FloodWatch.PH

FloodWatch.PH is a two-track system. The tracks have different jobs and their
metrics are reported separately. This card documents both. The README never
averages them.

---

## Track A - Event track: Sentinel-1 SAR flood-extent change detection

| Field | Value |
|---|---|
| Method name | SAR Otsu change detection |
| Sensor | Sentinel-1 C-band GRD, VV + VH, IW mode (`COPERNICUS/S1_GRD`) |
| License (data) | Copernicus open / free |
| Training required | None. The method is parameter-free. Otsu has no fitted parameters. |
| Permanent-water mask | HAND (MERIT Hydro `MERIT/Hydro/v1_0_1`) + JRC GSW (`JRC/GSW1_4/GlobalSurfaceWater`, occurrence >= 50%) + OSM `natural=water` / `waterway` |
| Validation event | GFD event 4300, Tropical Storm Koppu / Lando, 2015-10-22, central Luzon |
| Validation date | 2015-10-26 (Sentinel-1 post-onset acquisition) |
| Validation metric | IoU and F1 vs GFD `flooded` polygon |
| Demo event | Super Typhoon Carina / Gaemi + SW monsoon, Jul-Aug 2024, Metro Manila + Bulacan + Pampanga |
| Demo dates | 2024-06-16, 06-28 (dry baseline), 07-10 (pre), 07-22, 07-30 (peak / recession), 08-03 (post) |

### Pipeline steps (per acquisition date)

1. Pull S1 GRD scenes bracketing the event. Build a pre-event baseline composite (median of dry weeks before) and per-date during/after images.
2. Speckle-filter (refined-Lee / focal median). Convert to dB.
3. Otsu threshold on the VH (and VV cross-check) change image (`during - baseline`). Candidate open water.
4. Subtract the permanent-water mask. Report flood, not rivers and lakes.
5. Emit a per-timestep flood polygon GeoJSON.

The Otsu threshold is computed fresh per image pair. There are no fitted parameters and no train/test split for Track A. The event-disjoint holdout decision (see §3 of the spec) governs Track B only.

### Track A performance

| Metric | Value |
|---|---|
| Track A IoU vs GFD event 4300 (Koppu 2015) | `0.061` |
| Track A F1 vs GFD event 4300 (Koppu 2015) | `0.071` |
| Track A precision vs GFD event 4300 (Koppu 2015) | `0.085` |
| Track A recall vs GFD event 4300 (Koppu 2015) | `0.061` |
| Otsu threshold (dB, Koppu validation date) | `-21.7` |

The Carina 2024 demo event has no promptly-public official flood-extent polygon; it is the ungauged demo, not the validation event. The validated method is applied to Carina without a ground-truth comparison.

---

## Track B - Recurrence model: `recurrence_clf_v1`

| Field | Value |
|---|---|
| Model name | `recurrence_clf_v1` |
| Released | 2026-05-15 (v1.0.0) |
| License | MIT (code); CC-BY-4.0 (embeddings from AlphaEarth) |
| Reproducibility | Bit-exact; `make hash-verify` asserts sha256 `b7c702532f92c43f` |
| Encoder | Google AlphaEarth Foundations "Satellite Embedding V1" (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`), 10 m, 64-dim, unit-norm, annual, year **2017**. "Produced by Google and Google DeepMind." License: CC-BY-4.0. |
| Classifier head | `sklearn.linear_model.LogisticRegression` on the 64-dim embedding |
| Calibrator | Platt sigmoid on the event-disjoint holdout |
| Task | Per-pixel flood-recurrence-prone classification |
| Embedding year | 2017 (earliest AlphaEarth annual; contemporaneous with GFD record end) |
| Positive class | Points inside GFD historical flood-event footprints (2002-2017, Philippines), permanent water removed |
| Negative class | Land points not flooded in any GFD Philippines event |
| Committed cache | `model/embeddings/floodwatch_embeddings_v1.npz` (~10 MB) |
| Decision threshold | `0.5` |

### Training data

- GFD Philippines events: `40` typhoon events used for training, covering 2002-2017.
- Holdout events: `17` whole typhoon events held out (event-disjoint, never random pixels). Named in `model/holdout_events.json`.
- Positive samples: `6700` (GFD flood footprint interior, permanent water removed).
- Negative samples: `4500` (non-flooded land points across all GFD Philippines events).

The embedding year is fixed at 2017. The annual cadence is too coarse for a single event (Track A's job) but is appropriate for "does this place's land-embedding signature predict it floods repeatedly."

### Track B performance (event-disjoint holdout)

| Metric | Value |
|---|---|
| F1 at deployed threshold | `0.955` |
| Precision at deployed threshold | `0.949` |
| Recall at deployed threshold | `0.962` |
| AUC-ROC | `0.974` |
| Brier score | `0.046` |
| Holdout positive count | `2200` |
| Holdout negative count | `1346` |

These numbers are measured on the event-disjoint holdout only. The holdout events are named in `model/holdout_events.json` and never appear in any training fold. A CI gate (`scripts/check_event_disjoint.py`) enforces this.

### How to load

```python
import joblib, numpy as np
from scripts.verify_clf import verify_sha256

# Verify before loading (joblib.load is a pickle surface).
verify_sha256("model/recurrence_clf_v1.joblib")

bundle = joblib.load("model/recurrence_clf_v1.joblib")
clf   = bundle["clf"]          # LogisticRegression
platt = bundle["platt"]        # {"A": ..., "B": ...}

def calibrated_probability(features_64d: np.ndarray) -> np.ndarray:
    raw = clf.decision_function(features_64d)
    A, B = platt["A"], platt["B"]
    return 1.0 / (1.0 + np.exp(-(A * raw + B)))
```

### Reproducibility

```bash
pip install -r requirements.txt
make train          # builds recurrence_clf_v1.joblib from cached npz (no network)
make hash-verify    # asserts sha256 b7c702532f92c43f
make calibrate      # Platt sigmoid on the event-disjoint holdout
```

`make train` is deterministic and runs in approximately 30 seconds on a standard laptop with no GPU. Pinned deps (`scikit-learn`, `joblib`, `numpy`) in `requirements.txt` make the joblib bytes reproducible across machines.

---

## Data sources and licenses

All inputs are publicly licensed. No paywall, no non-commercial clause.

| Input | Source / GEE asset | License | Use |
|---|---|---|---|
| SAR backscatter | `COPERNICUS/S1_GRD` (Sentinel-1) | Copernicus open | Track A event flood extent |
| Annual embeddings | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (AlphaEarth) | CC-BY-4.0 | Track B recurrence head |
| Flood labels (historical) | Global Flood Database `GLOBAL_FLOOD_DB/MODIS_EVENTS/V1` (Cloud to Street, Nature 2021) | CC-BY-4.0 | Track B positives; Track A validation |
| Flood labels (event) | Copernicus EMS Rapid Mapping; UNOSAT | Copernicus open / UNOSAT open | Track A validation polygons |
| Permanent water / terrain | `MERIT/Hydro/v1_0_1` (HAND); JRC GSW `JRC/GSW1_4/GlobalSurfaceWater` | Open | Permanent-water mask |
| Population exposure | WorldPop / Meta HRSL | CC-BY-4.0 | Barangay exposed-population denominator |
| Building exposure | Microsoft GlobalML Building Footprints | ODbL-equivalent | Barangay building-count denominator |
| Barangay boundaries | PSA / OSM admin polygons | PSA public / ODbL | Click-target geography |
| Official hazard (comparison) | UP NOAH / Project NOAH / PAGASA / MGB published extents | Government public | The civic gap layer |

"Produced by Google and Google DeepMind" applies to the AlphaEarth embeddings. Attribution required under CC-BY-4.0.

---

## Intended use / out-of-scope

**Intended:** Aggregate civic-tech research on the gap between satellite-observed recurrent flood extent and official hazard maps. Supporting public-interest reporting and LGU disaster planning.

**Not intended for:**
- Any enforcement, permit, insurance, or compensation decision affecting an individual dwelling or household.
- Replacing an official flood-hazard assessment or an engineering survey.
- Real-time emergency response routing (Track A latency is days to weeks, not minutes).
- Extrapolation outside the Philippines without revalidation.

---

## Known biases and limitations

- The GFD record ends 2017. Track B is trained on 2002-2017 events. Events since 2017 are not in training or holdout.
- The AlphaEarth embedding year is fixed at 2017. Land-cover changes since 2017 (urban expansion, reclamation, reforestation) are not reflected.
- The Otsu threshold is scene-specific. Shadowed areas, very calm river surfaces, and rice paddy water can confound the change detection.
- Permanent-water masking uses JRC GSW occurrence >= 50%. Areas with seasonal water near the threshold may be over- or under-masked depending on monsoon phase.
- Track B outputs are a 10-30 m sample grid, not a per-building assessment. Do not interpret a positive point as a statement about a specific dwelling.
- Exposure figures (WorldPop population, Microsoft footprint building counts) are modeled estimates, not census counts. They are rounded to the nearest 10 at barangay level.
- The official hazard-map comparison uses UP NOAH / PAGASA / MGB published extents as available; coverage and vintage vary by LGU.

---

## Ethics and privacy

Exposure figures are aggregated to barangay-level counts only. No household identification. No per-dwelling flood-status geometry. No PII property keys. CI gate `scripts/check_no_pii.py` enforces this on every release.

Conservative civic language throughout the site and outputs. Every analytics surface carries the disclaimer: "Observed flood extent derived from public satellite data. Patterns may have legitimate explanations; figures warrant independent verification."

The project is not affiliated with NDRRMC, PAGASA, UP NOAH, DOST, or any Philippine government agency.

---

## Citation

```bibtex
@software{puspus_floodwatch_ph_2026,
  author = {Puspus, Xavier},
  title  = {FloodWatch.PH: open-source observed flood extent and recurrence mapping from satellite data},
  year   = 2026,
  url    = {https://github.com/xmpuspus/floodwatch-ph},
}
```
