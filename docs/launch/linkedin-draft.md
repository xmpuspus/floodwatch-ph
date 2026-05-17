# LinkedIn launch draft - FloodWatch.PH

Status: DRAFT. Do not post. For review only.
Voice: plain, technical, no hype, conservative civic framing. No emoji, no em-dashes.

---

I restructured the FloodWatch.PH Now view into a "Corridor watch": a log of what the satellites and radar have observed over the Philippine expressways. It is not a live feed and not a forecast. It is observed, dated evidence, organized by how fresh each observation is.

The Philippines floods every typhoon season, and people are trying to work out whether a corridor like SLEX or NLEX has water on it. The honest answer a satellite project can give is not a prediction, it is the record: where water was last actually observed, where it tends to recur, and how much rain has fallen since. Corridor watch shows that and says plainly what it is not.

The view is tiered, because the honest fact is structural. Ground-radar rain refreshes in minutes. The observed flood extent from radar satellite is hours to days old by the time it lands. The optical flood signal is cloud-limited and off by default, because typhoon cloud usually blanks it. Rather than hide that asymmetry behind one timestamp, the layout shows it: each layer carries its own ticking age, its acquisition time, its source, and its latency class. A failed fetch says it is unavailable; it never shows a blank map and never says "just now". The labels describe the kind of observation, not which one is the answer.

It stays a two-track system, reported with separate metrics, never averaged into one flattering number.

Track A, observed extent. The map auto-detects the most recent usable Sentinel-1 radar pass over the Greater Metro Manila and Central Luzon corridor and runs the same training-free Otsu change detection, with permanent rivers and lakes removed. Radar is used because it sees through typhoon cloud, which is the only reason a flood is observable while the storm is still overhead. The layer is labeled the most recent satellite pass, ~6-day revisit with ~24 h product latency, not a live feed. When a pass is not usable it says so, rather than drawing a clean map that reads as all clear. The kept 2024 Carina time series is clearly marked a historical demonstration.

Three new layers are fetched in the browser at view time, from public government and meteorological sources, with no new server and no cron: RainViewer ground-radar rain relayed from PAGASA, Copernicus EMS Global Flood Monitoring faster-observed Sentinel-1 flood extent, and NASA LANCE VIIRS near-real-time optical flood (off by default). They fetch the same fixed nationwide tiles for every visitor; the location lookup query still never leaves the browser. Monitored expressways and major roads (SLEX, NLEX, SCTEX, Skyway, CAVITEX, TPLEX and others) are intersected with the latest observed water, per segment. GPM IMERG rainfall accumulation over the modeled flood-prone areas is shown as dated context for the gap between radar passes, explicitly not a score and not a flood forecast.

There is also a location and route check. It is fully client side: a small bundled Metro Manila gazetteer matched in the browser, no third-party geocoder, the typed query never leaves the device and is never logged. It returns layered, as-of-dated evidence for a place or a corridor (modeled recurrence, historical flood record 2002 to 2017, latest observed radar status, rainfall context, nearby flagged expressway segments). It never says an area will or will not flood, never gives a routing or safety instruction, and points to PAGASA, MMDA Flood Control and the LGU DRRMO for live conditions.

Track B, the recurrence model, is unchanged: a frozen Google AlphaEarth embedding plus a small calibrated logistic-regression head, trained with whole typhoon events held out, not random pixels. Precision 0.949, recall 0.962, F1 0.955 on the event-disjoint holdout, bit-exact reproducible from a committed cache, no GPU, about thirty seconds, deterministic sha256 b7c702532f92c43f.

On where this sits next to existing work: Google Flood Hub covers Philippine rivers but is riverine forecast only, and by its own documentation excludes the flash, urban and compound flooding that actually closes Metro Manila expressways. Project NOAH, PAGASA and the Copernicus Emergency Management Service Global Flood Monitoring are the authoritative and institutional references. FloodWatch is not a competitor or a replacement for any of them. It is an independent, open, reproducible measurement of observed extent and the gap between the historical record and what the model expects, complementary to those systems and deferring to them for warnings.

Everything is public: MIT code, CC-BY-4.0 data, GitHub, Zenodo DOI, model card, privacy impact assessment, related-work review, and CI gates that enforce the permanent-water and event-disjoint rules. A daily refresh regenerates the observed cron layers, gates broken or fabricated data out, and verifies the live deploy. GloFAS and riverine forecasting stay deliberately out of scope, recorded as a possible future external link and never a forecast pixel on the corridor map. It is a civic-tech research artifact, not a warning system and not an accusation. Patterns may have legitimate explanations and figures warrant independent verification. FloodWatch is complementary to and never a replacement for PAGASA, MMDA Flood Control, your LGU DRRMO, Project NOAH and Google Flood Hub. For live flood conditions and routing during an active flood, use those.

Code and method: https://github.com/xmpuspus/floodwatch-ph
Live map: https://floodwatch-ph-five.vercel.app

Built on Sentinel-1 (Copernicus), NASA GPM IMERG, Google AlphaEarth, the Global Flood Database (Cloud to Street), MERIT Hydro, JRC Global Surface Water, OpenStreetMap and FAO GAUL. Related work: Google Flood Hub, Project NOAH, PAGASA, Copernicus EMS Global Flood Monitoring, the Global Flood Database, UN-SPIDER's Sentinel-1 flood recommended practice, and my earlier SolarMap.PH.
