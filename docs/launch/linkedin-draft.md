# LinkedIn launch draft - FloodWatch.PH

Status: DRAFT. Do not post. For review only.
Voice: plain, technical, no hype, conservative civic framing. No emoji, no em-dashes.

---

I built FloodWatch.PH: an open, reproducible measurement of where floods actually go in the Philippines, from public satellite data.

Philippine communities flood again and again. The official hazard maps (UP NOAH, PAGASA, MGB) and the post-event damage assessments do not always agree with each other or with what satellites observed. FloodWatch.PH is an independent check on that, and the whole chain is public and reproducible.

It is deliberately a two-track system, because flooding is an event and rooftop solar is a fixture, so the SolarMap.PH single-snapshot approach does not transfer directly. The two tracks are reported with separate metrics, never averaged into one flattering number.

Track A, the demo: Sentinel-1 C-band radar flood-extent change detection. Radar is used because it sees through typhoon cloud, which is the only reason a flood is observable at all while the typhoon is still overhead. Optical satellites are blind exactly when it matters. The map sweeps 4 real Sentinel-1 acquisition dates across Super Typhoon Carina and the 2024 southwest monsoon over Metro Manila, Bulacan and Pampanga; detected flood peaks at about 184 square kilometres. Permanent rivers and lakes are removed from every frame, so the layer is flood, not hydrography. The method is classical and training-free; its agreement with the older coarse MODIS flood reference is reported plainly, including where it is weak and why (a single radar pass days after onset versus a multi-day 250 m optical product).

Track B, the model: a frozen Google AlphaEarth Foundations satellite embedding plus a small calibrated logistic-regression head, trained to classify flood-recurrence-prone land. The honest decision here is the split: whole typhoon events are held out, never random pixels, because adjacent pixels are near-duplicates and a random split inflates every score. On that event-disjoint holdout the classifier reports precision 0.949, recall 0.962, F1 0.955. The build is bit-exact reproducible from a committed embeddings cache, no GPU, about thirty seconds, deterministic sha256 b7c702532f92c43f.

The civic point is the gap: 337 sampled locations the model flags as flood-prone that have no record at all in the Global Flood Database for 2002 to 2017. Aggregated to province, almost everywhere in the country is already in the historical record, which is itself an honest finding; the value is in the locations the record misses. The cross-reference against the official government hazard maps (UP NOAH, PAGASA, MGB) is a stated next step, deferred for a documented reason: those layers are token-gated or single-page-app only.

Everything is public: MIT code, CC-BY-4.0 data, GitHub, Zenodo DOI, model card, privacy impact assessment, CI integrity gates that enforce the permanent-water rule and the event-disjoint rule. It is a civic-tech research artifact, not a warning system and not an accusation. Patterns may have legitimate explanations and figures warrant independent verification.

Code and method: https://github.com/xmpuspus/floodwatch-ph
Live map: https://floodwatch.ph

Built on Sentinel-1 (Copernicus), Google AlphaEarth, the Global Flood Database (Cloud to Street), MERIT Hydro, JRC Global Surface Water, WorldPop and OpenStreetMap. Related work: the Global Flood Database, UN-SPIDER's Sentinel-1 flood recommended practice, and my earlier SolarMap.PH.
