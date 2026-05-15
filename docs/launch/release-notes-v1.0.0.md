# FloodWatch.PH v1.0.0

Open, reproducible flood-extent measurement and flood-recurrence classification
for the Philippines from public satellite data. An honest two-track system; the
two tracks are reported with separate metrics, never averaged.

## Track A - event flood extent (Sentinel-1 SAR, classical, training-free)

- Sentinel-1 C-band SAR (radar sees through typhoon cloud; optical is blind
  exactly when the flood happens). Otsu on the event VH image, gated on
  "got darker than the dry baseline", with permanent water, slope and a
  HAND-style flood-plausible-terrain mask.
- Demo: Super Typhoon Carina / 2024 SW monsoon over Metro Manila, Bulacan,
  Pampanga; 4 real Sentinel-1 acquisition dates; detected flood 80.0 -> 137.8
  -> 184.1 (peak, Jul 30) -> 115.7 km2; permanent water removed from every
  frame.
- Validation: vs the Global Flood Database `flooded` polygon for GFD event
  4300 (Tropical Storm Koppu / Lando, 2015) at GFD's native 250 m: IoU 0.054,
  F1 0.065. Reported plainly. A single 10 m SAR pass days after onset vs a
  multi-day 250 m optical product see different water; this is the documented
  limitation of the comparison, not a hidden one. Track A's value is the
  reproducible permanent-water-masked observed-extent time series.

## Track B - recurrence-prone classifier (frozen AlphaEarth + calibrated head)

- Frozen Google AlphaEarth Foundations Satellite Embedding (2017, 64-dim) +
  scikit-learn logistic regression + Platt calibration.
- Event-disjoint holdout: 40 whole GFD training events, 17 whole holdout
  events; a point flooded in both is dropped, so no point leaks across the
  boundary.
- Holdout (2200 pos / 1346 neg): precision 0.949, recall 0.962, F1 0.955,
  AUC 0.974, Brier 0.046.
- Bit-exact reproducible from the committed embeddings cache, no GPU, ~30 s,
  deterministic sha256 b7c702532f92c43f (CI-asserted).

## Civic layer

337 sampled locations the model flags flood-prone (calibrated score >= 0.60)
that have no Global Flood Database record for 2002 to 2017. Province-level
modeled-vs-observed gap map (82 provinces). Exposure: ~8.1M people in provinces
with detected Carina flooding. The official UP NOAH / PAGASA / MGB hazard-map
cross-reference is a documented v1.1 extension (those layers are token-gated /
single-page-app only).

## Integrity

CI gates enforce the permanent-water rule, the event-disjoint rule, the
no-PII / province-aggregate rule, the site/data config-mirror rule, and the
deterministic classifier hash. MIT code, CC-BY-4.0 data, model card, privacy
impact assessment.

100% public inputs: Sentinel-1 (Copernicus), Google AlphaEarth, Global Flood
Database (Cloud to Street), MERIT Hydro, JRC Global Surface Water, WorldPop,
GHSL, OpenStreetMap, FAO GAUL.
