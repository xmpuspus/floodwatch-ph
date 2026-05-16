# Related work and defensibility — FloodWatch.PH

Status: research sweep for the near-real-time enhancement wave. Produced by the
deep prior-art pass. Every system below is a real, operational product or
published dataset; FloodWatch credits all of them and is positioned as
**independent, open, reproducible, and complementary** — never first, only,
best, or a forecaster.

Sweep date: 2026-05-16. Citations are inline; live URLs at the bottom.

---

## 1. The systems FloodWatch sits next to

### Google Flood Hub / Google Research Flood Forecasting (DeepMind)

- **What it does.** AI riverine flood **forecasting**: predicts river discharge
  and inundation up to 7 days ahead from hydrologic + meteorological models,
  using "virtual gauges" where physical gauges are absent.
- **Data / method.** Proprietary LSTM-family hydrologic models, global gauge +
  reanalysis data. Not reproducible by a third party; the model is closed.
- **PH coverage.** The Philippines **is** in the ~150-country coverage list (the
  Help Center country list includes it; ~240,000–250,000 global forecast
  points). Coverage is at river-reach forecast points along modelled basins, not
  a national wall-to-wall layer.
- **Forecast vs observed.** Pure **forecast** (daily-resolution, updated daily),
  explicitly "for informational purposes only."
- **Scope it explicitly excludes.** Google's own FAQ states it covers
  *"only riverine floods, as opposed to flash/coastal floods,"* and that flash
  floods, coastal floods, urban flood maps, and pluvial (rainfall-induced)
  floods are **not** covered.
- **How FloodWatch differs / complements.** The Philippine flood that closes
  SLEX/NLEX and inundates Metro Manila during a typhoon is overwhelmingly
  **pluvial / compound urban** flooding driven by extreme rainfall and the
  enhanced southwest monsoon — precisely the class Flood Hub says it does not
  model. FloodWatch publishes **observed** SAR extent of exactly that water
  after it has happened, plus a recurrence-vs-historical-record gap. It is the
  observational, open, reproducible complement to a closed riverine forecaster:
  Flood Hub answers "will this river crest"; FloodWatch answers "where did the
  water actually go on this Sentinel-1 pass, and which areas recur." Use Flood
  Hub for the forecast; FloodWatch never forecasts.

### UP NOAH / Project NOAH (UP Resilience Institute)

- **What it does.** The authoritative Philippine hazard-map and near-real-time
  warning platform: flood, landslide, storm-surge hazard maps, plus (since 2024)
  an **Impact-Based Flood Forecasting System** that predicts whether a
  neighbourhood will be affected ~24 h ahead. Maintained by UP NIGS / UP RI;
  hazard maps now also surfaced on the new PAGASA site.
- **Data / method.** Government LiDAR-derived hydraulic flood-hazard modelling,
  validated in real events (e.g. Palawan 2025). Authoritative planning
  instrument.
- **PH coverage.** National, the official reference for PH flood hazard.
- **Forecast vs observed.** Both: static hazard maps + a 24 h impact forecast.
- **Open/closed.** Hazard leaves are served through token-gated ArcGIS / a SPA;
  no stable bulk data URLs (the well-documented PH civic-data access failure
  mode). Modelling code/inputs are not third-party reproducible.
- **How FloodWatch differs / complements.** FloodWatch is **not** a hazard map
  and does not replace NOAH. NOAH is the modelled authority; FloodWatch is an
  independent **observation** of where water actually was on dated satellite
  passes plus a reproducible recurrence model, and it explicitly defers the
  NOAH/PAGASA/MGB overlay to a documented v1.1 because those layers are not
  fetchable as open data. FloodWatch sends users to NOAH/PAGASA for hazard and
  forecasting.

### PAGASA (DOST) — flood forecasting and warning

- **What it does.** The mandated national hydromet agency: flood bulletins,
  river/dam monitoring, the PANaHON observing network, official flood-hazard
  maps (now hosting NOAH layers), warnings.
- **Forecast vs observed.** Operational forecasting + gauge observation.
- **Open/closed.** Public bulletins; underlying gauge feeds and hazard rasters
  not openly bulk-distributed.
- **How FloodWatch differs / complements.** FloodWatch is never a warning system
  and routes all "live conditions / what do I do now" questions to PAGASA, MMDA
  Flood Control, and the LGU DRRMO. It adds an open reproducible observed-extent
  and recurrence-gap layer that PAGASA does not publish as open data.

### MMDA Flood Control / NAMRIA

- **MMDA Flood Control** operates the Metro Manila street-level flood-sensor and
  pumping-station network and the public flood advisories used for routing
  during active events — the live operational layer FloodWatch points to and
  never competes with.
- **NAMRIA** is the national mapping authority (topography, base geodata).
  FloodWatch uses open global equivalents (FAO GAUL, OSM) rather than
  redistributing NAMRIA products.

### Copernicus EMS — Global Flood Monitoring (GFM) and Rapid Mapping

- **What it does.** GFM auto-processes **every** Sentinel-1 VV land scene into a
  near-real-time flood mask, typically within ~5 h of acquisition, using three
  independent algorithms (LIST, DLR, TU Wien). CEMS Rapid Mapping produces
  on-activation crisis maps. Free and open; the closest sibling to FloodWatch
  Track A.
- **PH coverage.** Global, including the Philippines (PH DOST has collaborated
  with the GFM/JRC programme).
- **Forecast vs observed.** Observed (SAR-derived extent), like Track A.
- **Open/closed.** Open data, but the production pipeline is an institutional
  service, not a single reproducible repo a researcher runs end-to-end in ~30 s.
- **How FloodWatch differs / complements.** FloodWatch does **not** claim to beat
  or replace GFM. GFM is the operational global authority for S1 flood masks;
  FloodWatch is a small, fully **reproducible, single-repo, permanent-water-
  masked** PH-focused artifact whose civic value is the *recurrence-vs-observed-
  record gap* and a transparent, caveated method — and it cites GFM as the
  operational reference. A natural FloodWatch contribution is cross-checking
  against GFM where both exist.

### Floodbase (formerly Cloud to Street) and the Global Flood Database (GFD)

- **GFD** (Tellman et al., *Nature* 2021; Cloud to Street × Dartmouth Flood
  Observatory) is the 913-event, 2000–2018, 250 m MODIS historical flood
  archive. CC-BY-4.0. **FloodWatch uses GFD directly** as Track B labels and the
  Track A validation reference — it is upstream, fully credited, not a
  competitor.
- **Floodbase** is the commercial successor (parametric-insurance flood
  monitoring). Closed/commercial. FloodWatch is the open, civic, non-commercial
  counterpart and does not overlap its market.

### UNOSAT / UNITAR and Dartmouth Flood Observatory (DFO)

- **UNOSAT** delivers on-activation satellite crisis maps (incl. PH typhoons);
  **DFO** maintains the long-run global flood event catalogue feeding GFD.
- **How FloodWatch differs.** Both are activation/catalogue services; FloodWatch
  is a reproducible method + recurrence model, credits DFO via the GFD lineage,
  and lists UNOSAT/CEMS as richer v1.1 validation sources.

### NASA SERVIR-SEA / SERVIR-Mekong, Nababaha.com, GMA/ABS-CBN flood trackers

- **SERVIR** builds regional EO decision tools (HYDRAFloods etc.) for SE Asia;
  methodologically adjacent, capacity-building, not a PH open recurrence-gap
  product. FloodWatch cites the UN-SPIDER / SERVIR S1 recommended practice as
  method lineage.
- **Nababaha.com / media trackers** are crowd/advisory aggregators for live
  conditions — useful to the public during an event, not reproducible datasets;
  FloodWatch points users to official sources, not to these, for safety.

### Academic PH SAR / embedding flood work

- Sentinel-1 + Otsu (Edge/Bmax-Otsu, KI) on Google Earth Engine is an
  established, widely published flood-mapping recipe (Thailand 2019, Turkey,
  arid-region and multi-temporal benchmarks; UN-SPIDER recommended practice).
  FloodWatch's Track A is a deliberate, **non-novel** application of this
  standard method — claiming novelty here would be an overclaim and is avoided.
- PH-specific flood-susceptibility ML on S1 (2018–2023 historical S1, ML
  susceptibility) exists. No published work was found combining AlphaEarth /
  Google Satellite Embedding with PH flood **recurrence**; FloodWatch should
  describe this as an unexplored *combination of public components*, not a
  scientific first. JRC Global Surface Water already provides a "recurrence"
  layer for surface water — FloodWatch's recurrence is flood-event recurrence
  vs the GFD record, a different quantity, and the doc should not let a reader
  conflate them.

---

## 2. Comparison table

| System | Job | Forecast / Observed | PH coverage | Open & reproducible | Relation to FloodWatch |
|---|---|---|---|---|---|
| Google Flood Hub | Riverine flood forecast (≤7 d) | Forecast | Yes, riverine reach points | Closed model | Complementary; FW never forecasts; FW covers pluvial/urban observed extent Flood Hub excludes |
| UP NOAH / Project NOAH | Official hazard maps + 24 h impact forecast | Both | National, authoritative | Hazard data token-gated/SPA | Authority FW defers to; FW is independent observation, not a hazard map |
| PAGASA | Mandated forecasting + warnings | Forecast + gauge | National | Bulletins public, data not bulk-open | FW routes live/safety questions here |
| MMDA Flood Control | Live street sensors + advisories | Live observed | Metro Manila | Operational, not a dataset | FW points here for routing; never competes |
| Copernicus EMS GFM | Automated global S1 flood mask (~5 h) | Observed | Global incl. PH | Open data, institutional pipeline | Closest sibling; FW is reproducible single-repo PH artifact, cites GFM |
| Copernicus EMS Rapid Mapping / UNOSAT | On-activation crisis maps | Observed | On activation | Open products | Richer FW v1.1 validation source |
| Global Flood Database (Cloud to Street/DFO) | Historical flood archive 2000–2018 | Observed (historical) | Global incl. PH | CC-BY-4.0 | **Upstream input** to FW (labels + validation), fully credited |
| Floodbase | Commercial parametric-insurance monitoring | Observed | Global | Closed/commercial | Non-competing; FW is the open civic counterpart |
| NASA SERVIR-SEA | Regional EO decision tools | Both | SE Asia | Mostly open tools | Method lineage; FW cites recommended practice |

---

## 3. How FloodWatch positions itself (zero superlatives)

FloodWatch.PH is an independent, open-source, reproducible civic-tech artifact.
It measures **observed** flood extent from public Sentinel-1 SAR on dated
acquisition passes, adds rainfall context from GPM IMERG accumulation, and
publishes a recurrence model and the gap between modelled flood-proneness and
the historical observed record. It builds on and credits the Global Flood
Database, Copernicus Sentinel-1 and EMS GFM, Google AlphaEarth, MERIT Hydro, JRC
Global Surface Water, WorldPop, OSM, and the UN-SPIDER S1 recommended practice.

It is **complementary to, and never a replacement for**, PAGASA, Project NOAH,
MMDA Flood Control, and Google Flood Hub. It is **not** a forecaster, **not** a
warning system, and **not** an official hazard map. Its distinct contribution is
narrow and stated plainly: a fully reproducible, permanent-water-masked,
single-repo PH pipeline that surfaces the observed-extent-and-recurrence-vs-
record gap — most useful exactly where the forecasting and hazard authorities
either do not model the flood type (pluvial/urban/compound) or do not release
their layers as open data. For live conditions, forecasts, and routing during an
active flood, FloodWatch directs every user to PAGASA, MMDA Flood Control, and
the LGU DRRMO.

---

## Sources

- Google Flood Hub coverage: https://support.google.com/flood-hub/answer/16508958
- Google Flood Hub scope (riverine only, excludes flash/coastal/urban/pluvial): https://support.google.com/flood-hub/answer/15638004
- Google Research Flood Forecasting: https://sites.research.google/gr/floodforecasting/
- Expanding flood forecasting coverage (Google blog): https://blog.google/technology/ai/expanding-flood-forecasting-coverage-helping-partners/
- UP NOAH: https://noah.up.edu.ph/ and https://noahcenter.up.edu.ph/
- UP NOAH hazard-map validation (Palawan): https://resilience.up.edu.ph/up-noah-flood-hazard-maps-validated-during-the-palawan-flooding/
- UP impact-based flood forecasting: https://www.gmanetwork.com/news/scitech/science/942731/up-scientists-develop-impact-based-flood-forecasting-system/story/
- PAGASA flood hazard maps: https://www.pagasa.dost.gov.ph/products-and-services/flood-hazard-maps
- Copernicus EMS GloFAS/GFM: https://global-flood.emergency.copernicus.eu/
- GFM service description (~5 h, three algorithms): https://global-flood.emergency.copernicus.eu/news/107-global-flood-monitoring-product-launch/
- Global Flood Database (Tellman et al., Nature 2021): https://global-flood-database.cloudtostreet.ai/
- GFD on Earth Engine: https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1
- Dartmouth Flood Observatory: https://floodobservatory.colorado.edu/
- UNOSAT: https://unosat.org/
- S1 + Otsu intercomparison (method lineage): https://www.mdpi.com/2072-4292/15/5/1200
- AlphaEarth Satellite Embedding V1: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
