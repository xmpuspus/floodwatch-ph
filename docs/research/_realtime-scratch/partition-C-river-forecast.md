# Partition C — Authoritative River / Forecast Feeds (Attributed External Context Only)

Research date: 2026-05-17. All latency/cadence figures cited. All access claims backed by pasted probe evidence.

Posture reminder: FloodWatch.PH is observation-only. Nothing below is ever restated as a FloodWatch claim. Each is at most an *attributed external pointer* with a link out and a precise scope caveat. The defensible niche (pluvial/urban/flash flooding that FloodWatch observes) must NOT be blurred by riverine-forecast copy.

---

## Decision Matrix

| Candidate | Product/feed (exact endpoint) | True latency / horizon (cited) | Cadence | Spatial resolution / point density | PH + Luzon basin coverage | Access mechanism (probed) | Licence + cost | Reproducible-in-CI? | Obs vs forecast |
|---|---|---|---|---|---|---|---|---|---|
| **1. Copernicus GloFAS — open WMS** | `https://ows.globalfloods.eu/glofas-ows/ows` (OGC WMS 1.3.0) | 30-day ensemble forecast horizon | Daily run from 00:00 UTC ECMWF IFS | River grid 0.1°×0.1° (~10 km); reporting points at catchments >50 km² | Global incl. PH (WMS bbox -180..180 / -85..85; GetMap over bbox 4–21 N, 116–127 E returns valid PNG) | **REST/OGC WMS, NO AUTH, CORS `access-control-allow-origin: *`** for GetCapabilities + GetMap. GetFeatureInfo on `reportingPoints`/`RPGM` fails (`cannot unpack non-iterable NoneType` — portal session/date context required) | Free, public. Copernicus EMS open licence; CDS-distributed data CC BY 4.0 | **WMS tile overlay: YES** (no token, stable host). Programmatic reporting-point GeoJSON: **NO** (portal-gated, manual form for new points) | Forecast |
| **1b. GloFAS via CDS API** | `cdsapi` → `cems-glofas-forecast` dataset on `cds.climate.copernicus.eu` | Same 30-day / daily | Daily | 0.1° river discharge | Global incl. PH | **Free account + personal access token in `$HOME/.cdsapirc` REQUIRED**; per-dataset Terms-of-Use acceptance | Free, account-gated. Data CC BY 4.0 | **Marginal** — works only if a free CDS token lives in GH secrets; counts as a token gate, NetCDF payloads heavy, async queue. Fragile for CI heartbeat | Forecast |
| **2. Google Flood Forecasting API** | `api.flood.google` (base 000 on HEAD/GET; documented REST/RPC) | Real-time riverine forecast (Flood Hub model) | Model-driven (riverine) | >240,000 locations / ~150 countries | **Philippines explicitly listed** in Flood Hub country coverage; basin-level (not confirmed which Luzon basins programmatically) | **Partner-gated pilot**: waitlist form → approval email → API key → enable in GCP project. `curl api.flood.google` returns empty (no public root) | Data CC BY 4.0, **no charge**, but **access partner-gated** (not open) | **NO** — waitlist + per-project API key, not a free public no-token endpoint. Fails no-fragile-gate posture | Forecast (riverine ONLY — excludes pluvial/urban/flash by Google's own docs) |
| **3. PAGASA / Project NOAH / PANaHON** | `bagong.pagasa.dost.gov.ph` (OctoberCMS PHP), `noah.up.edu.ph` (Angular SPA), `panahon.gov.ph` (Laravel) | Telemetered gauge (near-real-time) — N/A, no open feed | N/A | N/A | Metro Manila / Marikina / Pampanga gauges exist operationally | **SPA / server-rendered only. NO open JSON/XHR.** NOAH serves index.html for every path (`api/v1/stations`, `assets/config.json`, `stations.json` all → HTTP 200 `text/html`). PANaHON `ajax`/`api/v1/stations`/`stations.json` all → 404. main.js has no plaintext API base | Public site, no open data licence/endpoint published | **NO** — SPA catch-all + session-cookie sites, no stable bulk URL. Scraping = fragile, banned by posture | Gauge (observation) — but inaccessible |

---

## Per-candidate detail + probe evidence

### 1. Copernicus GloFAS (Global Flood Awareness System)

**Cadence & horizon (cited):** ECMWF-ENS = 51 members at ~9 km to day 15, ~36 km day 16–30. GloFAS 30-day uses the 00:00 UTC IFS medium-range run daily for day 1–15 and the latest extended-range for day 16–30; ENS aggregated to 24-hourly for the hydrological chain. Horizontal resolution 0.1°×0.1°, temporal resolution 24 h.
Sources: ECMWF Confluence "GloFAS meteorological forecasts"; HESS 27,1 (2023) "Daily ensemble river discharge reforecasts and real-time forecasts from the operational GloFAS"; GloFAS v3.1 page (0.1°×0.1°, 24 h).

**Open WMS — the one genuinely surfaceable surface:**

```
$ curl -s 'https://ows.globalfloods.eu/glofas-ows/ows?service=WMS&version=1.3.0&request=GetCapabilities'
<?xml version='1.0' encoding="UTF-8"?><WMS_Capabilities version="1.3.0" ...>   # 150,503 bytes, NO auth
Layers incl: GLOFAS_WMS, MajorRiverBasins, MajorRivers1, FloodHazard100y,
             reportingPoints, RPGM (medium-range), RPGH, RPGS, UpstreamArea ...
EX_GeographicBoundingBox: west -179.9 east 179.9 south -85.06 north 85.06   # global, covers PH

$ curl -sD- 'https://ows.globalfloods.eu/glofas-ows/ows?...request=GetCapabilities' -H 'Origin: https://example.com'
HTTP/2 200
content-type: text/xml; charset=UTF-8
access-control-allow-origin: *                # CORS open

$ curl 'https://ows.globalfloods.eu/glofas-ows/ows?...request=GetMap&layers=MajorRiverBasins&styles=default&bbox=4,116,21,127&width=300&height=300&format=image/png'
http=200 type=image/png bytes=14668           # renders a PH tile, no token
```

**What is NOT available open:** programmatic reporting-point GeoJSON. `GetFeatureInfo` on `reportingPoints`/`RPGM` returns `ServiceException: cannot unpack non-iterable NoneType object` (needs the portal's date/session parameters). WFS `GetCapabilities` also exceptions. ECMWF Confluence "Request GloFAS web reporting points": new points are a manual Contact-Us form, "do not follow a continuous update procedure". The downloadable bulk forecast data path is the CDS API (token-gated, below).

**CDS API path:** `cds.climate.copernicus.eu/how-to-api` confirms a free account + personal access token in `$HOME/.cdsapirc` is required, plus per-dataset Terms-of-Use acceptance. Dataset `cems-glofas-forecast`. This is a real token gate and heavy NetCDF — acceptable for an offline build job, **fragile as a live CI heartbeat**.

### 2. Google Flood Forecasting API

`developers.google.com/flood-forecasting`: "The Flood Forecasting API provides an interface to access real time riverine flood forecasts." "The data exposed by this API is under the CC BY 4.0 license and offered at no charge." Access: **"Accessing the Flood Forecasting API requires an API key and enabling the Flood Forecasting API"** — pilot, join a waitlist → approval email → API key → enable in a GCP project.

Scope (Flood Hub support 15638004, exact quote): *"We currently focus only on riverine floods, as opposed to flash/ coastal floods. We also do not generate flood maps for urban areas."* Coverage (support 16508958): *"more than 240,000 locations across river basins in roughly 150 countries"* — **Philippines explicitly listed**.

Probe: `curl -sI https://api.flood.google/` → empty (no public root); `https://api.flood.google/v1/` → no response. Consistent with a key-gated, non-discoverable API.

Verdict: free licence but **partner/waitlist-gated** — not a stable public no-token endpoint. Cannot be a reproducible-in-CI heartbeat without an approved key in secrets, and even then it's a pilot subject to change.

### 3. PAGASA / Project NOAH / PANaHON (telemetered gauges)

Re-verified the known PH civic-data failure mode. Evidence:

```
$ curl -sI https://bagong.pagasa.dost.gov.ph/      # OctoberCMS, set-cookie october_session, x-powered-by PHP/7.4
$ curl -sI https://noah.up.edu.ph/                 # nginx, 11,557-byte Angular shell (<base href="/">, mapbox-gl)
$ curl https://noah.up.edu.ph/this-path-does-not-exist-xyz123   # returns the SAME index.html shell
$ for p in api/v1/stations assets/config.json stations.json api/sensors; do curl -o/dev/null -w "$p %{http_code} %{content_type}\n"; done
  api/v1/stations -> 200 (text/html)   assets/config.json -> 200 (text/html)
  stations.json   -> 200 (text/html)   api/sensors       -> 200 (text/html)   # SPA catch-all, no JSON
$ curl https://noah.up.edu.ph/main.js | grep http   # 354 KB bundle, NO plaintext api/host base
$ for p in ajax api/v1/stations stations.json map/data data/stations; do curl panahon.gov.ph/$p; done
  all -> 404                                          # Laravel, session cookies, no open data route
```

NOAH = Angular SPA serving index.html for every path (the classic token/SPA gate — no stable bulk URL). PAGASA bagong = OctoberCMS with session cookies, no documented data API. PANaHON = Laravel, no open route. Web search confirms no published open JSON API; data is behind the SPA/portal. **Document-as-future. Do not build a scraper** (fragile, against posture, and the SPA renders data client-side from non-discoverable internal calls).

---

## Partition Recommendation

**Surfaceable now as an attributed external context pointer (exactly ONE):**

- **GloFAS open WMS tile overlay + deep link.** It is the only candidate with a stable, public, no-token, CORS-enabled endpoint (`ows.globalfloods.eu/glofas-ows/ows`, verified HTTP 200 PNG over the PH bbox with `access-control-allow-origin: *`). Surface it as an optional toggleable *attributed* map overlay (GloFAS `MajorRiverBasins` / `RPGM` medium-range layer) plus a "View on Copernicus GloFAS" deep link to `https://global-flood.emergency.copernicus.eu/`. Never parse it into FloodWatch evidence; it is a rendered external tile + link only. Reproducible-in-CI = the endpoint is static and unauthenticated (CI just needs to assert the GetCapabilities/GetMap 200, no secret).

  Exact honest-label UI string (literal):
  > "River flood forecast (riverine only — does not cover the pluvial/urban/flash flooding FloodWatch observes): 30-day ensemble, per Copernicus GloFAS. [Open GloFAS ↗]. Authoritative external forecast, shown for context, not a FloodWatch observation or claim."

  Toggle/overlay caption:
  > "Layer: Copernicus GloFAS medium-range river-flood forecast (daily run, 30-day horizon, 0.1° river grid). External forecast — context only, not FloodWatch data."

**Document-as-future (do NOT surface):**

- **GloFAS CDS API (`cems-glofas-forecast`)** — requires a free CDS account token in `$HOME/.cdsapirc` + per-dataset ToU + heavy async NetCDF. Acceptable for an offline analysis job, fragile for a live heartbeat. Reason logged: token gate + payload weight, not a no-token endpoint.
- **Google Flood Forecasting API** — partner/waitlist-gated pilot. Free licence (CC BY 4.0) but no public no-token endpoint and pilot-unstable. Reason logged: access gate + pilot status. (If ever granted a key, surface ONLY as an attributed riverine pointer with the precise exclusion below — Google's own words: *"We currently focus only on riverine floods, as opposed to flash/ coastal floods. We also do not generate flood maps for urban areas."*)
- **PAGASA / NOAH / PANaHON gauges** — SPA/portal-only, no open JSON, no stable bulk URL. Reason logged: SPA catch-all (every NOAH path → 200 text/html) and session-cookie portals; building a scraper violates the no-fragile-scrape posture.

**Posture risk flags:**

- The GloFAS WMS is the only thing that does NOT risk the no-paid-deps / no-token / no-scrape posture. It is a rendered tile + outbound link, never absorbed.
- Hard guardrail for copy: any GloFAS/Google surface must carry the riverine-only exclusion verbatim so it never blurs FloodWatch's pluvial/urban defensible niche. GloFAS and Flood Hub forecast *rivers*; FloodWatch observes *urban/pluvial* flooding — these are complementary, not substitutable, and the UI must say so.
- CDS and Google must NOT be wired even "behind a flag" in CI — a flag that needs a secret to be meaningful is a fragile gate by another name. Keep them as documented-future prose only.
