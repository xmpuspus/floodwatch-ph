# Privacy Impact Assessment: FloodWatch.PH

**Project:** FloodWatch.PH (https://github.com/xmpuspus/floodwatch-ph)
**Author / Self-designated DPO:** Xavier Puspus (`xpuspus@gmail.com`)
**Assessment date:** 2026-05-15 (v1.0.0)
**Applicable law:** Republic Act 10173 (Data Privacy Act of 2012), implementing rules, NPC circulars in force as of 2026-05-15.
**Status:** Self-conducted PIA. Formal NPC voluntary advisory opinion is in scope for the post-launch quarter.

---

## 1. Purpose of processing

FloodWatch.PH applies a two-track satellite pipeline to publicly licensed data over the Philippines to produce two outputs:

(a) **Track A** -- per-timestep flood-extent GeoJSON from Sentinel-1 SAR Otsu change detection, showing where flooding was observed during real typhoon events.

(b) **Track B** -- a per-pixel flood-recurrence-prone classification from a logistic-regression head trained on Google AlphaEarth Satellite Embedding V1 and the Global Flood Database Philippines event history.

These outputs are joined with WorldPop population estimates and Microsoft GlobalML building footprint counts at the province level (FAO GAUL level-2) to produce exposure figures, and compared with the historical observed record (Global Flood Database) to produce the civic gap layer. The official UP NOAH / PAGASA / MGB hazard-map cross-reference is a documented v1.1 refinement.

The intended use is civic-tech research and public-interest reporting on the gap between satellite-observed recurrent flood extent and official hazard-map coverage, supporting LGU disaster planning and policy discussion in the Philippines.

---

## 2. Categories of information processed

| Category | Source | Identifiability | Disposition |
|---|---|---|---|
| SAR backscatter raster | Copernicus Sentinel-1 GRD (public) | None: radar return from ground surface | Not republished. Used as model input for Track A change detection only. |
| AlphaEarth embedding vectors | Google Earth Engine, CC-BY-4.0 | None: 64-dim floating-point vectors | Committed cache (~10 MB) used for Track B training. Not republished as standalone data. |
| GFD flood-event footprints | Global Flood Database, CC-BY-4.0 | None: binary raster / polygon, no per-person data | Used for Track B labels and Track A validation. |
| MERIT Hydro / JRC GSW terrain raster | Public Earth Engine assets | None | Used for permanent-water mask. Not republished. |
| OSM water features | OpenStreetMap (ODbL) | Indirect: public features on a public map | Used for permanent-water mask. |
| WorldPop population | WorldPop, CC-BY-4.0 | Modeled aggregate; no individual identifiers | Published as rounded province-level (FAO GAUL level-2) totals only (nearest 10). |
| Microsoft GlobalML building footprints | Microsoft, ODbL-equivalent | Indirect: building outline on a public map | Published as province-level (FAO GAUL level-2) count only; no per-building attributes. |
| Province boundaries | FAO GAUL level-2 (public) / OSM (ODbL) | Administrative; public | Published as click-target polygons with aggregate properties only. |
| Official hazard map extents | UP NOAH / PAGASA / MGB (government public) | None | A v1.1 refinement; not used in v1.0. |
| Flood-extent polygons (Track A output) | Computed from Sentinel-1 | Indirect: spatial extent of flooding over a date range | Published per-event, per-date, as Polygon geometry with no property that identifies a dwelling. |
| Recurrence score (Track B output) | Computed from AlphaEarth | None on its own: a probability number on a 300 m sample grid | Published as a point grid. Points are sample-grid centers, not buildings. |
| Province exposure aggregate | Computed join | Province aggregate (FAO GAUL level-2: population, built-up area, flood share) | Published; all figures are aggregate, not per-household. |

No direct identifiers are collected: no names, no email addresses, no phone numbers, no national ID numbers, no electric-meter serials, no tax declaration numbers, no dwelling addresses.

---

## 3. RA 10173 §3 analysis

### §3(g) "personal information"

> "any information ... from which the identity of an individual is apparent or can be reasonably and directly ascertained ... or when put together with other information would directly and certainly identify an individual."

- A flood-extent polygon over a date range does not name a person.
- A recurrence-score point on a 300 m grid does not name a person.
- A province-level (FAO GAUL level-2) population count or building count does not name a person.
- The "put together with other information" clause is the legal exposure point: combining a province-level flooded count with a household registry could in principle narrow flood status, but a province (FAO GAUL level-2, ~82 Philippine provinces) is far too coarse to identify a household. This is a lower exposure than SolarMap.PH's per-building solar coordinates because FloodWatch publishes only counts and polygon extents, never per-dwelling geometry.
- **Mitigation:** All exposure figures are aggregated to province level (FAO GAUL level-2) with rounding. No per-building flood-status geometry is published. No per-dwelling property key appears in any output. CI gate `scripts/check_no_pii.py` enforces this on every release.

### §3(c) "consent"

Public satellite data (Sentinel-1, AlphaEarth) and public administrative boundaries (PSA, OSM) do not require individual consent under the public-records doctrine inherent to RA 10173's coverage. FloodWatch does not capture, store, or republish raw imagery. Published outputs are derived statistical indicators. The publication boundary (province aggregation at FAO GAUL level-2, takedown channel, attribution chain) is the responsibility-shifting mechanism in lieu of per-subject consent.

### §11 "general data privacy principles"

- **Transparency:** This PIA, `site/src/pages/privacy.astro`, and `SECURITY.md` document scope, purpose, and recipients.
- **Legitimate purpose:** Civic-tech research on a public-interest policy question (hazard-map coverage gaps, disaster risk).
- **Proportionality:** Only the aggregate province-level (FAO GAUL level-2) figures necessary for the research question are published. No per-dwelling geometry, no household attributes.

---

## 4. Risks and mitigations

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Per-dwelling flood geometry leaks into output | Low with CI gate active | High | `scripts/check_no_pii.py` CI gate asserts no per-dwelling geometry or PII keys in any published GeoJSON; failure halts the build and the release. |
| Re-identification by combining province aggregate with a household registry | Low (counts are province-level aggregate, not addresses) | Medium | Province counts (FAO GAUL level-2) are rounded; no property key links a row to a specific dwelling; conservative language ("province-level aggregate"). |
| Misuse as a targeting list for insurance denial or resettlement pressure | Low (no per-household resolution; data is already public) | Medium | Conservative civic language throughout ("observed extent", "warrants verification"). Disclaimer on every analytics surface. Takedown channel published. |
| Detection or model error affecting a specific community's planning | Medium (SAR detection errors, modeled population) | Medium | Track A IoU/F1 and Track B precision/recall published in MODEL_CARD.md. Every output carries the public-records disclaimer. "Report a data quality issue" CTA in the site FAQ. |
| Copernicus / OSM / WorldPop license non-compliance | Low (attribution-only) | Medium | Attribution section in README, MapView corner credit, MODEL_CARD.md data-sources table. |
| Vulnerability in joblib deserialization | Low | High | SECURITY.md flags `joblib.load`. `scripts/verify_clf.py` hash-verifies before load. `make hash-verify` in CI. |
| Inability to remove a published feature after complaint | Low (quarterly republish cadence) | Medium | Takedown channel via GitHub issue (label `takedown`); 5 working-day acknowledgement, 14 working-day removal target. Git history preserves audit trail. CC-BY-4.0 requires attribution of derivatives. |

---

## 5. Data lifecycle

| Stage | Location | Retention | Notes |
|---|---|---|---|
| S1 GRD scene cache | Local disk, `event/cache/` | Indefinite for reproducibility; not committed to git (.gitignore) | Not republished. |
| AlphaEarth embedding cache | `model/embeddings/floodwatch_embeddings_v1.npz` | Committed to repo (~10 MB) | Encoded feature vectors, not raw imagery. |
| GFD label cache | `model/labels/` | Committed to repo | Binary event membership labels per sample point. |
| Trained classifier | `model/recurrence_clf_v1.joblib` | Committed; hash-verifiable | Public artifact under MIT. |
| Flood-extent GeoJSON (Track A) | `site/public/data/flood_<event>.geojson` | Republished with each event or model update | CI-gated: permanent-water masked, no PII keys. |
| Recurrence grid (Track B) | `site/public/data/recurrence_prone.geojson` | Republished with each model version | No dwelling identifiers. |
| Hazard gap layer | `site/public/data/hazard_gap.geojson` | Republished with each update | Province aggregate (FAO GAUL level-2); disclaimer in `_meta.disclaimer`. |
| Province exposure aggregate | `site/public/data/barangay_exposure.json` (legacy filename retained for compatibility; contains province units, FAO GAUL level-2) | Republished with each update | Rounded counts; no household resolution. |
| Takedown requests | GitHub issues (label `takedown`) | Public audit trail in issue history | Personal information in emailed complaints redacted before any public response. |

---

## 6. Recipients

- Public web (CC-BY-4.0): all published GeoJSON and JSON outputs.
- Researchers, press, and public-interest organizations: same as public web; no privileged channel.
- LGUs, NDRRMC, PAGASA, DOST, NPC: same as public web; no privileged data access.
- No user data is sent to third-party analytics, advertising, or telemetry services.
- The site has no server-side handler. No query, address, or interaction is logged by FloodWatch.PH infrastructure.

---

## 7. DPO and accountability

- **DPO (self-designated):** Xavier Puspus, `xpuspus@gmail.com`.
- **Takedown channel:** Open a GitHub issue with label `takedown`. Acknowledgement within 5 working days; removal from the next published dataset within 14 working days.
- **Formal NPC registration:** scoped for post-launch quarter, deferrable contingent on traffic and feedback.
- **Review cadence:** PIA re-reviewed at each quarterly republish or whenever a new event or model version is published.
- **Last reviewed:** 2026-05-15 (v1.0.0).

---

## 8. Conclusion

FloodWatch.PH publishes statistical indicators derived from public satellite data and public administrative datasets. The publication boundary (province aggregation at FAO GAUL level-2, rounding, no per-dwelling geometry, CI-enforced PII gate, conservative civic language, and a published takedown channel) is, in the author's good-faith judgment, sufficient to satisfy the proportionality and transparency principles of RA 10173 for an inaugural launch. The environmental data processed here carries a lower per-person exposure than SolarMap.PH's per-building rooftop geometry. The PIA will be re-reviewed at each subsequent release, and a formal NPC advisory opinion will be sought in the post-launch quarter as scale or scope warrants.
