# Near-real-time sources — capability matrix and honest architecture

Status: deep-research deliverable for the v1.2 "expressway corridor conditions"
wave. Produced by four parallel probe-backed research partitions on 2026-05-17.
Probe clock reference for every measured "now": `2026-05-17T03:13–03:16Z`.

Method: web + GitHub + papers + **live API probing** (curl on macOS, CORS
headers and freshness measured, not guessed). Every latency figure is either
MEASURED (probe output pasted in the partition scratch files under
`docs/research/_realtime-scratch/`) or CITED to a primary-source URL — stated
per cell. This doc is the single source of truth for which feeds v1.2 may use
and how. It does not change any code or copy.

Hard constraints carried verbatim from the locked posture: free + public only,
no paid deps, no fragile scrape, reproducible in CI, observation-not-forecast
unless attributed, every layer as-of-dated, never claim "live" if it is not,
client-side privacy invariant (the user's area-lookup query never leaves the
browser, RA-10173) must stay mathematically intact.

---

## 1. Headline measured findings

1. **Google Earth Engine is NOT a realtime source.** Measured: `NASA/GPM_L3/IMERG_V07` catalog availability ended `2026-05-15T03:30Z` — **47.7 h** behind the probe clock. `JAXA/GPM_L3/GSMaP/v8/operational` ended `2026-05-15T14:00Z` — **~37 h** behind. EE serves Late/Final-class products. It stays the engine for the computed S1 and GPM-accumulation layers; it cannot be the heartbeat.

2. **The freshest honest free+public rain source is RainViewer radar (PAGASA/PANAHON-sourced), measured 4.2 min behind, CORS-open, no key.** It is ground-radar observation over the exact corridors (9 PH stations; live echo over Metro Manila confirmed in the tile probe). Caveat: ToS says "personal or educational use only" + "no availability guarantee" — defensible for a civic/educational non-commercial project but a real dependency-fragility note.

3. **A genuinely-faster-than-S1 observed flood layer exists and is shippable: Copernicus EMS GFM via the public EODC STAC** — Sentinel-1 ensemble flood mask, 20 m, PUM-guaranteed ≤8 h after acquisition, no token, CORS reflects the site origin. Live probe returned 3 real ensemble flood items over Luzon dated 2026-05-15/16.

4. **Corrected honest S1 number (a stale-copy fix v1.2 must carry):** S1B failed Dec 2021; S1C user data opened 26 Mar 2025, operational ~early May 2025. The constellation is now **S1A + S1C, ~6-day combined revisit restored ~May 2025**, with **~24 h GRD product publication latency** (CDSE standard SLA). The existing site copy's "~6–12 day revisit" is stale single-satellite-era framing and must be updated to "~6-day revisit, ~24 h product latency".

5. **The decisive architecture answer is a split, per layer:** EE-derived layers (S1 extent, GPM accumulation/risk) stay on the existing daily GitHub Actions cron (EE has no anonymous browser tile API — server signing is mandatory; S1 revisit makes daily already optimal). The two genuinely-fresh layers (RainViewer rain-now, NASA GIBS NRT optical flood) move **client-side, fetched at page-view** — the only honest path to minutes/hours freshness on a free static site, at a cost of three new public CSP origins, each privacy-defensible.

6. **No honest ground-truth (in-situ confirmation) feed exists** for Metro Manila in 2026 that is free + public + CORS-clean + RA-10173-compatible. All four candidates (MMDA, TV5 traffic, Waze CCP, X/#floodPH) are document-as-future with hard reasons.

---

## 2. Source x capability matrix

Latency cells marked **[M]** were measured by a live probe; **[C]** are cited to
the primary source in section 6. Full pasted probe output is in the partition
scratch files (`docs/research/_realtime-scratch/partition-{A,B,C,D}-*.md`).

### 2a. Rain heartbeat candidates

| Product / feed | True latency | Cadence | Spatial res | PH / SLEX-NLEX coverage | Access + CORS (probed) | Licence + cost | CI-reproducible? | Obs vs forecast | Honest UI label (literal) |
|---|---|---|---|---|---|---|---|---|---|
| **RainViewer** `api.rainviewer.com/public/weather-maps.json` + tilecache XYZ | **4.2 min [M]** (frame 03:10:00Z vs now 03:14:11Z) | 10 min | radar-native ~1 km mosaic | Yes — PAGASA/PANAHON 9 stations; live Metro Manila echo confirmed (1431 px in probe tile) | REST JSON + XYZ tiles. CORS `access-control-allow-origin: *` probed on JSON **and** PNG tile. Direct browser fetch, no key | Free **"personal or educational use only"** (ToS); "no availability guarantee"; attribution required | Yes — pure client fetch, zero secrets, zero CI dep | **Observation** (ground radar reflectivity → rate). Use `radar.past` only; `nowcast` is extrapolation/forecast and was empty at probe | `Rain radar: PAGASA national radar via RainViewer — last frame {frameUTC} (~{age} min ago). Ground-radar observation, not a forecast. Source: RainViewer / PAGASA.` |
| **GPM IMERG via EE** `NASA/GPM_L3/IMERG_V07` | **~48 h [M]** (catalog ends 2026-05-15T03:30Z) | 30 min | 0.1° (~11 km) | Yes, global incl. Luzon | Earth Engine (SA key already in repo). No browser CORS — server/EE only | Free, public (NASA) | Yes, but **not realtime** — Late/Final class | Observation (gauge-adjusted multi-sat) | `Rainfall: GPM IMERG accumulation (NASA, via Earth Engine). Satellite estimate, not a gauge. Latest available {UTC}, typically ~1–2 days behind — not live.` |
| **GPM IMERG Early** `GPM_3IMERGHHE.07` (GES DISC) | **4 h [C]** (NASA GPM) | 30 min | 0.1° | Yes, global | GES DISC HTTPS/OPeNDAP — **Earthdata Login required** (probe hit NASA security banner + URS redirect). No browser CORS | Free but **token-gated** | **Fragile** — Earthdata machine token/.netrc secret in CI | Observation (forward-morphed, no gauge) | `Rainfall: GPM IMERG Early estimate (NASA), ~4 h behind. Satellite estimate, not a gauge, not a forecast. Valid {UTC}.` |
| **JAXA GSMaP_NRT** via EE `JAXA/GPM_L3/GSMaP/v8/operational` | **~37 h [M]** (catalog ends 2026-05-15T14:00Z) | hourly | 0.1° | Yes, global | Earth Engine. No browser CORS | Free, public (JAXA) | Yes but **not realtime** via EE | Observation (NRT provisional) | `Rainfall: JAXA GSMaP hourly estimate (via Earth Engine). Satellite estimate. Latest {UTC}, ~1.5 days behind — not live.` |
| **JAXA GSMaP_NRT / _NOW** direct (sharaku / G-Portal) | ~4 h / ~0 h [C] | hourly | 0.1° | Yes | FTP / G-Portal — **registration + password / CSRF session**. No anonymous tile/REST | Free but **registration-gated** | **Fragile** — credentialed FTP, no clean CI path | `_NRT` observation; **`_NOW` is partly FORECAST** (short-range blend) | `_NOW`: `Rainfall: JAXA GSMaP_NOW — current-hour estimate, partly short-range forecast/extrapolation, not a pure observation. {UTC}.` |
| **Himawari-9 AHI** (NOAA `s3://noaa-himawari9`) | **10.5 min [M]** (0300Z scan → S3 03:10:32Z) | 10 min full disk (2.5 min sectors) | 0.5–2 km vis/IR | Yes — full disk covers all PH | Anonymous S3 (no auth, probe confirmed). No CORS; raw `.DAT.bz2`/`.nc` → server processing only | Free, public (NOAA Open Data) | Yes (anon S3) but **heavy satpy processing** | **NOT rainfall** — cloud-top brightness; rain only inferred | `Storm clouds: Himawari-9 infrared cloud-top temperature (NOAA/JMA), ~10–15 min behind. Cloud intensity, NOT measured rainfall. {UTC}.` |
| **OpenWeatherMap** radar/precip tiles (free tier) | n/a (disqualified) | varies | coarse | global | XYZ tiles **require API key** (exposed client-side or CI secret); 60/min free cap | Free tier but key-gated | Possible but key-exposure risk | Mixed (precip layer often model-blended) | (not recommended — key exposure + honesty) |

### 2b. Observed-flood-faster-than-S1 candidates

| Product / feed | True latency | Cadence | Spatial res | PH / SLEX-NLEX coverage | Access + CORS (probed) | Licence + cost | CI-reproducible? | Obs vs forecast | Honest UI label (literal) |
|---|---|---|---|---|---|---|---|---|---|
| **Copernicus EMS GFM** — collection `GFM` on EODC STAC `stac.eodc.eu/api/v1` | **≤8 h [C]** ("product timeliness ≤ 8 h … within 5 h from acquisition"; total internal lead-time 60 min — GFM PUM p.10) | per S1 pass (event-driven) | **20 m** (`OC020M`) | Confirmed — live STAC query bbox 120,14,122,15 → 3 ensemble items, bboxes lon 120.2–122.9 / lat 11.8–17.2 (Manila Bay → central Luzon, NLEX/SLEX band) | STAC REST, no token. CORS reflects `access-control-allow-origin: https://floodwatch.ph` (probed). Render via titiler XYZ `tilejson` (CORS `*`) or pull `dlr_flood_extent` COG server-side | **CC BY 4.0** per GFM PUM ("open and free licenses"). STAC `license` field literally returns `proprietary` — an EODC catalog metadata default, **not** the governing Copernicus EMS policy (pre-ship verification flagged, §7) | **Yes** — one documented STAC `GET` (newest scene over Luzon bbox), no scrape, no token | **Observation** (SAR ensemble flood extent) | `Faster observed SAR flood: Copernicus EMS GFM ensemble, Sentinel-1 pass {DATETIME} (delivered <=8 h after acquisition). 20 m, all-weather radar. Observed, not a forecast; gaps where no recent S1 pass.` |
| **NASA LANCE VIIRS/MODIS NRT flood** — `VIIRS_Combined_Flood_1-Day` (+2/3-Day, MODIS) on NASA GIBS WMTS | **3 h LANCE [C]; ~5 h max to GIBS imagery [C]** (MCDWD/VCDWD User Guide Rev E §6.4) | daily composites (1/2/3-Day) | ~250 m (VIIRS 375 m native, resampled to 250 m grid) | Confirmed — live GIBS tile z6/x52/y19 over Luzon → HTTP 200, 26 KB PNG, `layer-time-actual: 2026-05-15` | WMTS/XYZ PNG, browser-fetchable. CORS `*` on capabilities **and** tiles (probed). No token | Free, public (NASA, US-gov public domain) | **Yes** — read `WMTSCapabilities.xml` (one curl, no auth) to pin latest date | **Observation** (optical water detection) | `Supplementary observed flat-water signal: NASA LANCE VIIRS NRT flood, {DATE} 1-day composite. Optical (~250 m), cloud-limited — typhoon cloud often blanks it. Not the primary layer, not live, not a forecast.` |
| **FloodWatch existing raw S1** (Track A, CDSE/ASF, via EE) | **~24 h [C]** GRD publication (CDSE standard SLA) | per S1 pass; **~6-day** combined revisit (S1A+S1C, restored ~May 2025) | ~10 m (GRD IW) | Global; Luzon covered | CDSE OData/STAC + ASF; EE-processed in repo | Copernicus free + open | Yes (already in pipeline) | **Observation** | `Latest usable Sentinel-1 SAR pass: {DATE}. S1A+S1C, ~6-day revisit, ~24 h product latency. Dated ground truth — not live, not a forecast.` |

### 2c. Authoritative river/forecast — attributed external pointer ONLY (never restated as a FloodWatch claim)

| Product / feed | Latency / horizon | Cadence | Coverage | Access + CORS (probed) | Licence | CI-reproducible? | Obs/forecast | Verdict |
|---|---|---|---|---|---|---|---|---|
| **Copernicus GloFAS open WMS** `ows.globalfloods.eu/glofas-ows/ows` | 30-day ensemble horizon [C] | daily run, 00:00 UTC ECMWF IFS | global incl. PH; 0.1° river grid; GetMap over PH bbox returns valid PNG | OGC WMS 1.3.0, **no auth**, CORS `*` (GetCapabilities + GetMap probed). GetFeatureInfo / WFS portal-gated | Copernicus EMS open; CDS data CC BY 4.0 | **WMS overlay: yes** (static unauthenticated endpoint, CI asserts 200). Reporting-point GeoJSON: no | Forecast (riverine) | **Surfaceable now** as a toggleable attributed overlay + deep link, with verbatim riverine-only exclusion |
| **GloFAS via CDS API** `cdsapi` → `cems-glofas-forecast` | same 30-day / daily | daily | global incl. PH | **Free CDS account token in `$HOME/.cdsapirc` required** + per-dataset ToU + heavy NetCDF | CC BY 4.0 | Marginal — token gate + async NetCDF, fragile for live | Forecast | **Document-as-future** (token gate + payload weight) |
| **Google Flood Forecasting API** `api.flood.google` | real-time riverine forecast | model-driven | >240k locations / ~150 countries, **PH listed**; basins not confirmed programmatically | **Partner/waitlist-gated pilot** → API key → enable in GCP project. No public root (probed empty) | CC BY 4.0, no charge | **No** — waitlist + per-project key, pilot-unstable | Forecast (**riverine only — Google's docs explicitly exclude flash/coastal and urban-area flood maps**) | **Document-as-future** (access gate + pilot). If ever keyed: attributed riverine pointer only, with the exclusion verbatim |
| **PAGASA / Project NOAH / PANaHON** gauges | n/a — no open feed | n/a | MM / Marikina / Pampanga gauges exist operationally | **SPA / session-cookie only.** NOAH serves index.html for every path (`api/v1/stations`, `stations.json` → 200 text/html). PANaHON routes → 404. No plaintext API base in bundle | gov site, no open-data licence | **No** — SPA catch-all + cookie portals, no stable bulk URL | Gauge (obs) but inaccessible | **Document-as-future** (the known PH SPA/token failure mode; no scraper) |

### 2d. Ground-truth (in-situ confirmation) — all document-as-future

| Product / feed | Access (probed) | Why blocked | Verdict |
|---|---|---|---|
| **MMDA Flood Control sensors (FCSMO)** | `mmda.gov.ph` → **HTTP 403 Cloudflare**. Data only in MetroBase + free-text tweets | No machine-readable endpoint; Cloudflare-walled CMS + tweets; not parseable/attributable reproducibly | **Document-as-future** |
| **MMDA traffic (TV5 / Interaksyon MetroBase)** `mmdatraffic.interaksyon.com` | **Dead**: `https` → TLS handshake fail (http=000); `http` → 301 loop; `api.` no resolve. Community wrappers abandoned 2017, no flood data | Upstream unreachable in 2026; abandoned; third-party unlicensed scrape; not flood data | **Document-as-future** |
| **Waze for Cities / CCP** | B2G partner program; GeoRSS/JSON delivered to a partnered **government agency** only, partner-token-gated, never CORS-exposed | Eligibility (agency-only); partner-token-gated; redistribution forbidden; RA-10173 (re-publishing crowd location reports) | **Document-as-future** |
| **X / #floodPH / @MMDA / @dost_pagasa** | X API v2 no free content tier (paid ≥US$100/mo); no anonymous CORS endpoint | Violates no-paid-deps; RA-10173 (third-party personal data); ToS redistribution limits; not CI-parseable without an LLM dep | **Document-as-future** |

---

## 3. The decisive architecture question — answered per layer

The question: is the honest "most realtime" a **client-side fetch of the
freshest public product at view time** (zero cron lag — requires CORS-clean +
privacy-reconcilable) versus a **server cron** (lag, heavier EE processing)?

Verified infra facts (probed/cited):
- **Vercel Cron (Hobby): hard-capped at once-per-day, ±59 min precision; sub-daily fails at deploy** (Vercel docs, last_updated 2026-03-04). Strictly no better than the existing GH Actions daily cron and would force an unneeded serverless function. **Rejected.** A Vercel edge fetch-proxy is also rejected — unnecessary (the two live sources are already CORS-`*`) and it would add a server that sees client IPs.
- **GitHub Actions cron: realistic reliable floor is ~daily**; the "5-minute minimum" is configurable, not delivered — scheduled runs slip 5–40 min and are skipped under load (worst at the top of every hour). A cron layer can honestly claim "refreshed approximately daily", never a tight sub-hourly SLA.
- **Earth Engine has no anonymous browser tile API** — every tile URL must be signed by the service-account key, which can only live server-side.
- **CORS probed:** NASA GIBS capabilities + tiles → `*`; RainViewer JSON + tiles → `*`; GFM EODC STAC → reflects site origin; GloFAS WMS → `*`. EE → none (server only).

Per-layer verdict:

| Layer | Delivery | Why | Cadence | CSP impact | Privacy reconciliation |
|---|---|---|---|---|---|
| Sentinel-1 flood extent (Track A, EE) | **Server / GH Actions cron (unchanged)** | EE signing is server-only; ~6-day revisit makes daily optimal — no information lost vs hourly | daily | none | unchanged |
| GPM IMERG accumulation / current_risk (EE) | **Server / GH Actions cron (unchanged)** | EE signing server-only; the computed risk classification needs EE reduction | daily | none | unchanged |
| **Rain now (NEW)** — RainViewer `radar.past` | **Client-side fetch at page-view** | CORS `*`, free, 10-min radar, ~4–10 min lag; cron would inject up to a day of staleness onto a product whose whole value is the last hour | every view (~5–10 min source lag, zero cron lag) | add `https://*.rainviewer.com` + `https://tilecache.rainviewer.com` to `connect-src`/`img-src` | **Defensible** — a fixed all-PH rain tile by bbox/zoom, identical bytes for every visitor; the user's lookup string is never in the request. The "lookup never leaves the browser" invariant is mathematically intact |
| **NRT optical flood (NEW, optional/subordinate)** — NASA GIBS `VIIRS_Combined_Flood_1-Day` | **Client-side fetch at page-view** | CORS `*`, NRT (~5 h), free, US-gov public domain; cron adds a day of lag for no benefit | every view, request latest available date | add `https://gibs.earthdata.nasa.gov` to `connect-src`/`img-src` | **Defensible** — same argument; fixed PH-bbox tile, no user input in the request |
| GFM faster-observed SAR (NEW) — EODC STAC | **Client-side STAC GET** (newest Luzon scene) → titiler XYZ; OR server-side COG pull in the existing cron | STAC CORS reflects origin and is unauthenticated; titiler tiles CORS `*`. Either is honest; client-side is fresher and adds no server work | per S1 pass (event-driven; "faster observed", not live) | add `https://stac.eodc.eu` + `https://titiler.services.eodc.eu` to `connect-src`/`img-src` (if client-side) | **Defensible** — STAC query is a fixed Luzon bbox, no user input |
| GloFAS riverine forecast (attributed context, optional) | **Client-side WMS tile overlay + outbound deep link** | `ows.globalfloods.eu` WMS CORS `*`, no token; rendered tile only, never parsed | daily run | add `https://ows.globalfloods.eu` to `connect-src`/`img-src` (if enabled) | **Defensible** — fixed-bbox external forecast tile, never absorbed into FloodWatch evidence |

Net CSP delta if every new layer ships (the entire price of going client-fresh):
`connect-src`/`img-src` gain `https://*.rainviewer.com`,
`https://tilecache.rainviewer.com`, `https://gibs.earthdata.nasa.gov`, and
(if enabled) `https://stac.eodc.eu`, `https://titiler.services.eodc.eu`,
`https://ows.globalfloods.eu`. All public government/meteorological origins. No
new server, no new function, no paid dep, no change to the
lookup-stays-in-browser invariant. Each origin gets one privacy-page sentence
(purpose + "contains no user input, same bytes for every visitor").

---

## 4. Recommended honest realtime architecture

1. **Keep the daily GH Actions cron exactly as is** for the two EE-derived layers (S1 flood extent, GPM accumulation/risk). EE cannot be browser-fetched; S1's ~6-day revisit makes daily optimal. Zero CSP/privacy change.
2. **Do NOT adopt Vercel Cron or a Vercel edge proxy** — Hobby cron is daily-only and worse-precision; a proxy is an unnecessary server surface that sees client IPs.
3. **Add the rain heartbeat client-side: RainViewer `radar.past` (PAGASA/PANAHON radar).** Freshest honest free+public source measured (4.2 min, 10-min cadence). Render only `radar.past` (observation); never `radar.nowcast` (forecast/extrapolation). RainViewer + PAGASA attribution on the map. Flag the ToS fragility (§7) and keep GPM IMERG Early (NASA, 4 h, server-cron) documented as the public-data resilience fallback if RainViewer withdraws.
4. **Add the faster-observed SAR layer: Copernicus EMS GFM via EODC STAC**, surfacing the same satellite FloodWatch already trusts ~16 h sooner than CDSE's 24 h GRD publication, with the flood mask already computed. Honest framing: still pass-gated (no S1 pass = no new GFM) → "faster observed", not "live"; label with the scene datetime; verify the CC BY 4.0 attribution wording (§7) before shipping.
5. **Add NASA LANCE VIIRS NRT flood (GIBS) as a clearly subordinate, default-off supplementary layer.** Fastest of all (~5 h) but optical and cloud-limited — exactly why SAR is primary. Label "supplementary observed, cloud-limited".
6. **Optionally add the GloFAS riverine WMS as an attributed external context overlay + deep link** — never parsed, with the riverine-only exclusion verbatim so it never blurs FloodWatch's pluvial/urban niche. (Framing decision deferred to Phase 3 — adding a forecast layer at all, even attributed, is a posture choice for Xavier.)
7. **All ground-truth feeds: document-as-future** with the exact blocking reason in the methodology table ("Planned — blocked on: no public agency API; community feeds dead/abandoned; partner programs agency-only and privacy-incompatible").
8. **Correct the stale S1 copy**: "~6–12 day revisit" → "~6-day revisit (S1A+S1C, restored ~May 2025), ~24 h product latency" everywhere it appears (Agent-F-gated copy patch in the v1.2 plan).

Resulting posture: S1/GPM honestly labelled "refreshed daily / last pass N days
ago"; rain + NRT-flood honestly labelled with a ticking source timestamp and a
nowcast/near-real-time class; no layer ever claims "live"; the privacy invariant
is intact because no client fetch carries the user's query.

---

## 5. Freshness-clock UX spec

Principle: **"as realtime as possible" = surface the freshest timestamp and
label it precisely; never render the word "live".** Reuse the v1.1.0
`scan_status` honest-empty pattern for stale/missing.

Every layer carries two machine fields the UI renders:
- `acquired_utc` / `issue_utc` — the source's own acquisition or issue time (NOT our fetch time, NOT the deploy time).
- `source_latency_class` — one of `nowcast` (<15 min), `near-real-time` (<24 h), `daily`, `archival`.

Per-layer caption (under the layer toggle/legend):
```
{LAYER NAME}
{relative age, ticking}  ·  acquired {YYYY-MM-DD HH:MM} UTC
source: {source}  ·  {latency class label}
```
Ticking relative age, recomputed client-side every 30 s:
- `< 60 min` → `"updated 23 min ago"`
- `< 24 h`  → `"updated 4 h 12 min ago"`
- `< 7 d`   → `"updated 2 days ago (last Sentinel-1 pass)"`
- `>= 7 d`  → `"last pass 9 days ago"` + amber dot

Per-layer wording:
- **Sentinel-1 flood extent:** `Last Sentinel-1 pass {DATE} · {age} · revisit ~6 days, ~24 h product latency`. Never "live".
- **GPM rainfall context:** `Rainfall window ending {DATE HH:MM} UTC · processed daily`. Never "live".
- **Rain now (RainViewer):** `Rain radar {HH:MM} UTC · {age} · nowcast (~10-min source)`. May use "now-ish"; never bare "live"; ticking age makes a stale fetch visible.
- **NRT flood overlay (GIBS):** `NASA optical flood, {DATE} · near-real-time (same-day, cloud-permitting)`.
- **GFM faster-observed SAR:** `Copernicus EMS GFM, S1 pass {DATETIME} · delivered <=8 h after acquisition`.

Global ticker (header/footer strip):
```
Freshest layer: Rain radar — updated 14 min ago (08:40 UTC).
Site rebuilt 06:17 UTC. Layers refresh independently — see each layer's clock.
```
"Freshest layer" = the layer with the most recent `acquired_utc`, recomputed
every 30 s. The site-rebuild line keeps the static build honest vs the
independently-fetched client layers.

Colour / urgency (minimal, non-alarmist):
- Default neutral grey, no dot — the clock is informational, not a hazard signal.
- Amber dot **only** when a layer is staler than its own expected cadence (S1 > 12 d; rain client fetch > 30 min old; GIBS > 48 h): "this layer may be behind", not "flood danger".
- Never red, never pulsing — FloodWatch is not an alert system; faux-urgency would be a false claim.

Stale / missing (reuse v1.1.0 honest-empty):
- Client fetch fails: do not silently hide. Disabled toggle + caption `Rain radar unavailable — could not reach RainViewer ({HH:MM} UTC attempt). Other layers unaffected.`
- Cron layer empty: keep the existing v1.1.0 honest-empty message unchanged.
- Timestamp missing in the data file: show `acquisition time unavailable` — never default a missing time to "just now".

---

## 6. Sources

- EE IMERG V07 — https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07
- EE GSMaP v8 operational — https://developers.google.com/earth-engine/datasets/catalog/JAXA_GPM_L3_GSMaP_v8_operational
- NASA GPM IMERG runs/latency (Early 4 h) — https://gpm.nasa.gov/data/imerg
- GES DISC GPM_3IMERGHHE Early — https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imerghhe-07
- RainViewer API + ToS — https://www.rainviewer.com/api.html ; https://www.rainviewer.com/terms.html ; PH radars https://www.rainviewer.com/radars/philippines.html
- JAXA GSMaP — https://sharaku.eorc.jaxa.jp/GSMaP/ ; GSMaP_NOW https://sharaku.eorc.jaxa.jp/GSMaP_NOW/
- NOAA Himawari-9 open data — https://registry.opendata.aws/noaa-himawari/
- NASA GIBS / Worldview — https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml
- MCDWD/VCDWD User Guide Rev E (LANCE 3 h / 5 h to GIBS, 250 m) — https://www.earthdata.nasa.gov/s3fs-public/2025-04/MCDWD_VCDWD_UserGuide_RevE_04.22.25.pdf
- Copernicus EMS GFM PUM (≤8 h, 60-min lead-time, CC BY 4.0) — https://extwiki.eodc.eu/gfm_assets/gfm_pum_v20231005_compressed.pdf
- GFM EODC STAC — https://stac.eodc.eu/api/v1/collections/GFM
- Sentinel-1C user data opening 26 Mar 2025 — https://dataspace.copernicus.eu/news/2025-3-25-sentinel-1c-user-data-opening-26th-march
- CDSE Sentinel-1 timeliness (24 h GRD SLA) — https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel1.html
- Copernicus GloFAS — https://global-flood.emergency.copernicus.eu/ ; open WMS https://ows.globalfloods.eu/glofas-ows/ows ; CDS API https://cds.climate.copernicus.eu/how-to-api
- Google Flood Forecasting API + riverine-only scope — https://developers.google.com/flood-forecasting ; https://support.google.com/flood-hub/answer/15638004 ; https://support.google.com/flood-hub/answer/16508958
- Vercel Cron limits — https://vercel.com/docs/cron-jobs/usage-and-pricing
- GitHub Actions schedule reliability — https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule

---

## 7. Pre-ship verification flags (do not skip in the v1.2 plan)

1. **GFM licence wording.** The EODC STAC `license` field literally returns `proprietary` (an EODC catalog default). The governing GFM Product User Manual states CC BY 4.0 / "open and free licenses". Ship with the Copernicus EMS / CC BY 4.0 attribution citing the PUM, plus a one-line note that the STAC metadata default does not reflect Copernicus EMS policy. If Xavier wants a stricter reading, treat GFM as document-as-future pending an explicit Copernicus EMS data-policy citation. Decision belongs in Phase 3.
2. **RainViewer ToS.** "Personal or educational use only" + "no availability guarantee". Defensible for a civic/educational non-commercial project, but it is a third-party dependency that can change or withdraw. Keep GPM IMERG Early (NASA, public-data, server-cron) documented as the resilience fallback. Surface the attribution RainViewer requires.
3. **GloFAS as a forecast layer at all.** Even attributed and never-parsed, adding any forecast surface is a posture choice against the "FloodWatch never forecasts" line. The riverine-only exclusion must be verbatim. This is a Phase-3 framing decision for Xavier, not an automatic include.
4. **Corrected S1 number is a copy fix with data-integrity weight.** "~6–12 day" is stale; the verified current figure is "~6-day revisit, ~24 h product latency". Every instance must be found and patched (Agent-F-gated) — do not leave a stale specific number in public copy.
