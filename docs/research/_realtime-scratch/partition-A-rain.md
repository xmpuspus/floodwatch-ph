# Partition A — RAIN HEARTBEAT — Deep Research + Live Probes

Research date: 2026-05-17. Probe clock reference: all "now" comparisons against `2026-05-17T03:13–03:15Z` (UTC), measured live with `curl` on macOS.

Goal: pick the single most honest near-real-time rainfall heartbeat for PH expressway corridors (SLEX/NLEX/SCTEX/Skyway/CAVITEX/TPLEX), free + public only, reproducible in GitHub Actions CI, honestly labeled.

---

## Headline measured findings (probe evidence)

1. **Google Earth Engine does NOT serve a near-real-time IMERG/GSMaP run.**
   - `NASA/GPM_L3/IMERG_V07` catalog availability ends `2026-05-15T03:30:00Z`. At probe time `2026-05-17T03:13Z` that is **47.7 hours behind real time** (computed). This is effectively the Late/Final-class latency, NOT the Early run. The catalog only says products are `provisional` then `permanent` — no Early-run guarantee.
   - `JAXA/GPM_L3/GSMaP/v8/operational` (GSMaP_NRT) catalog availability ends `2026-05-15T14:00:00Z` → **~37 hours behind** at probe time. Also not realtime via EE.
   - Implication: the existing GEE integration in FloodWatch is fine for the climatology/observation layers but **cannot be the realtime heartbeat**.

2. **GPM IMERG Early (`GPM_3IMERGHHE`) has a 4-hour latency** (cited, NASA GPM) but the only authoritative distribution is GES DISC, which is **gated by Earthdata Login** (probe below) → token-fragile in CI.

3. **Himawari-9 on the NOAA anonymous S3 bucket has a MEASURED 10.5-minute latency** (probe below) but it is **cloud-top brightness, not rainfall**, and is raw HSD/netCDF requiring heavy processing — not a browser tile.

4. **RainViewer public `weather-maps.json` returned a radar frame 4.2 minutes old (MEASURED), is CORS-open (`access-control-allow-origin: *`), needs no API key, and sources Philippine radar from PAGASA/PANAHON (9 stations).** The catch is the ToS: **"free for personal or educational use only"** and **"We do not guarantee the availability of radar data."**

---

## Probe evidence (actual curl output)

### RainViewer CORS + freshness
```
$ curl -sI -H "Origin: https://floodwatch-ph-five.vercel.app" 'https://api.rainviewer.com/public/weather-maps.json'
HTTP/2 200
content-type: application/json
access-control-allow-origin: *          <-- CORS OPEN for direct browser fetch
cache-control: no-cache

$ curl -s '.../weather-maps.json'  (trimmed)
{"version":"2.0","generated":1778987427,"host":"https://tilecache.rainviewer.com",
 "radar":{"past":[ ... ,{"time":1778987400,"path":"/v2/radar/0162dffac8f6"}],
          "nowcast":[]},                      <-- nowcast EMPTY at probe time
 "satellite":{"infrared":[]}}                 <-- IR satellite EMPTY at probe time
```
- Latest radar frame epoch `1778987400` = `2026-05-17T03:10:00Z`. Now = `2026-05-17T03:14:11Z`.
- **MEASURED RainViewer radar lag = 4.2 minutes.** Cadence = 10 min (13 frames spanning ~2 h in `radar.past`).
- Tile probe over Manila (z7 x107 y58), `…/256/7/107/58/2/1_1.png` → `HTTP/2 200`, `content-type: image/png`, `access-control-allow-origin: *`. PNG decoded 256×256 RGBA, **1431 non-transparent pixels** = real radar echo present over Metro Manila at probe time (not a blank/placebo tile).
- Note: `nowcast` array was empty during this probe (no active nowcast frames) — RainViewer's free nowcast is intermittent; do not rely on it. Only `radar.past` (observation) is dependable.

### Himawari-9 NOAA S3 — anonymous + measured latency
```
$ curl -s 'https://noaa-himawari9.s3.amazonaws.com/?list-type=2&delimiter=/&prefix=AHI-L1b-FLDK/2026/05/17/'
  -> 19 time-slot folders today; latest = AHI-L1b-FLDK/2026/05/17/0300/

$ curl -s '.../?prefix=AHI-L1b-FLDK/2026/05/17/0300/'
  HS_H09_20260517_0300_B01_FLDK_R10_S0110.DAT.bz2  LastModified 2026-05-17T03:10:32.000Z
```
- Scan nominal start `03:00:00Z`; file in S3 at `03:10:32Z`. **MEASURED Himawari-9 latency = 10.5 min** (full-disk 10-min cadence). No auth header sent → anonymous S3 works.
- But: this is L1b radiance / L2 ISatSS netCDF (`.DAT.bz2`, multi-MB per segment, ~10 segments per band per slot). Converting to a rain proxy needs satpy/heavy processing in CI. It is cloud-top, not rain.

### GES DISC IMERG Early — Earthdata Login gate
```
$ curl -s 'https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHHE.07/2026/'
  <title>NASA IT Security Warning Banner</title>
  "By accessing and using this information system, you acknowledge and consent ..."
```
- The data pool is fronted by the NASA security banner and the data files redirect to `urs.earthdata.nasa.gov` for login. **Earthdata Login (machine token / .netrc) is required** → token-fragile, against the "no fragile token" constraint for CI.

### JAXA endpoints
```
$ curl -sI 'https://sharaku.eorc.jaxa.jp/GSMaP/'        -> HTTP/2 200 (static HTML portal)
$ curl -sI 'https://gportal.jaxa.jp/gpr/'               -> HTTP/2 200, sets fuel_csrf_token cookie
```
- GSMaP binary/CSV is on a **password-protected FTP requiring registration** (JAXA Users Guide). G-Portal is session/CSRF + account based. No anonymous tile/REST for GSMaP_NRT/_NOW. Fragile for CI.

---

## Candidate matrix

| # | Product / feed (exact ID / endpoint) | TRUE latency | Cadence | Spatial res | PH / SLEX-NLEX corridor coverage | Access mechanism + CORS | Licence + cost | Reproducible in CI? | Observation vs forecast | Honest UI label (literal string) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1a | **GPM IMERG via EE** `NASA/GPM_L3/IMERG_V07` | **~48 h** (MEASURED: catalog ends 2026-05-15T03:30Z vs now 2026-05-17T03:13Z) | 30 min | 0.1° (~11 km) | Yes, global incl. Luzon | Earth Engine (service account already in FloodWatch repo). No browser CORS — server/EE only | Free, public (NASA) | Yes, but NOT realtime — EE serves Late/Final-class | Observation (gauge-adjusted multi-sat estimate) | "Rainfall: GPM IMERG accumulation (NASA, via Earth Engine). Satellite estimate, not a gauge. Latest available {UTC}, typically ~1–2 days behind — not live." |
| 1b | **GPM IMERG Early** `GPM_3IMERGHHE.07` (GES DISC) | **4 h** target (CITED: NASA GPM — gpm.nasa.gov/data/imerg, "lowest latency available (4 hours)") | 30 min | 0.1° (~11 km) | Yes, global | GES DISC HTTPS data pool / OPeNDAP — **Earthdata Login required** (probe: NASA security banner + URS redirect). No browser CORS | Free but **token-gated** | **Fragile** — needs Earthdata token/.netrc secret in CI (machine token rotates) | Observation (forward-morphed multi-sat, no gauge) | "Rainfall: GPM IMERG Early estimate (NASA), ~4 h behind. Satellite estimate, not a gauge, not a forecast. Valid {UTC}." |
| 2 | **JAXA GSMaP_NRT** via EE `JAXA/GPM_L3/GSMaP/v8/operational` | **~37 h** (MEASURED: catalog ends 2026-05-15T14:00Z vs now) | Hourly | 0.1° (~11 km) | Yes, global incl. Luzon | Earth Engine. No browser CORS | Free, public (JAXA) | Yes but NOT realtime via EE | Observation (NRT, provisional) | "Rainfall: JAXA GSMaP hourly estimate (via Earth Engine). Satellite estimate. Latest {UTC}, ~1.5 days behind — not live." |
| 2b | **JAXA GSMaP_NRT** direct (sharaku/G-Portal) | ~4 h (cited, JAXA NRT) | Hourly | 0.1° | Yes | FTP/G-Portal — **registration + password / CSRF session** required. No anonymous tile/REST | Free but **registration-gated** | **Fragile** — credentialed FTP, no clean CI path | Observation (NRT provisional) | "Rainfall: JAXA GSMaP NRT, ~4 h behind. Satellite estimate, not a gauge. Valid {UTC}." |
| 2c | **JAXA GSMaP_NOW** (sharaku.eorc.jaxa.jp/GSMaP_NOW) | ~0 h (current hour) | Hourly | 0.1° | Yes | Same gated JAXA infra; viewer only, no public API | Free but gated | **Fragile** | **Partly FORECAST** — GSMaP_NOW blends a short-range forecast/extrapolation to reach ~0 h. Must label as not pure observation | "Rainfall: JAXA GSMaP_NOW — current-hour estimate, partly short-range forecast/extrapolation, not a pure observation. {UTC}." |
| 3 | **Himawari-9 AHI** (NOAA `s3://noaa-himawari9`, `AHI-L1b-FLDK` / `AHI-L2-FLDK-ISatSS`) | **10.5 min** (MEASURED: 0300Z scan → S3 LastModified 03:10:32Z) | 10 min full disk (2.5 min target sectors) | 0.5–2 km (vis/IR) | Yes — full disk covers all of Luzon/PH | **Anonymous S3** (no auth header needed, probe confirmed). No CORS for browser; raw `.DAT.bz2`/`.nc`, needs satpi processing → server cron only | Free, public (NOAA Open Data) | Yes (anonymous S3) but **heavy processing** in CI | **NOT rainfall** — cloud-top brightness temperature; rain is inferred only | "Storm clouds: Himawari-9 infrared cloud-top temperature (NOAA/JMA), ~10–15 min behind. This is cloud intensity, NOT measured rainfall. {UTC}." |
| 4a | **RainViewer** `api.rainviewer.com/public/weather-maps.json` + tilecache XYZ | **4.2 min** (MEASURED: frame 03:10:00Z vs now 03:14:11Z) | 10 min | Radar-native (~1 km mosaic) | **Yes — PAGASA/PANAHON, 9 PH radar stations; live echo over Metro Manila confirmed in probe (1431 px). Covers SLEX/NLEX/Skyway corridor (Subic, Tagaytay, Baler/Aparri, etc.)** | **REST JSON + XYZ tiles, CORS `access-control-allow-origin: *` (PROBED on both JSON and PNG tile). Direct browser fetch works, no key** | **Free for "personal or educational use only" (ToS, probed). "We do not guarantee availability of radar data." Attribution to RainViewer required** | Yes — pure client-side fetch, zero secrets, zero CI dep | Observation (ground radar reflectivity → rate). `nowcast` array exists but was empty at probe — use `radar.past` only | "Rain radar: PAGASA national radar via RainViewer, ~5–10 min behind (last frame {UTC}). Ground-radar observation, not a forecast. Source: RainViewer / PAGASA." |
| 4b | **OpenWeatherMap** radar/precip tiles (free tier) | n/a (not probed in depth — disqualified) | varies | coarse | global | XYZ tiles **require API key**; free tier rate-limited (60/min, 1M/mo) | Free tier but **API key = secret in client or CI**; key in client is exposed | Possible but key-exposure / rate-limit risk | Mix (precip layer often model-blended) | (not recommended — key exposure) |

---

## Probe-backed disqualifications

- **EE IMERG / EE GSMaP**: measured 37–48 h behind. Good for the existing observation/climatology layers; cannot be the realtime heartbeat. Keep as the "context / accumulation" layer, not the heartbeat.
- **GES DISC IMERG Early & JAXA direct**: 4 h latency is honest and good, but both require a credential (Earthdata Login / JAXA FTP registration). That violates "no fragile token / no fragile scrape" for GitHub Actions CI. Viable only as a *server-cron with a stored secret* fallback, explicitly second-choice.
- **Himawari-9**: best latency (10.5 min, anonymous) but it is cloud-top IR, not rainfall, and needs heavy raster processing — wrong tool for a "rainfall heartbeat", though excellent as an optional "storm clouds" context layer (correctly labeled).
- **OpenWeatherMap**: API key requirement = secret exposed client-side or a CI secret; precip layer is model-blended. Disqualified on key-exposure + honesty.

---

## Partition recommendation — single best honest realtime rain heartbeat

**Primary heartbeat: RainViewer public `weather-maps.json` + tilecache XYZ radar layer (PAGASA/PANAHON-sourced), fetched CLIENT-SIDE.**

Why:
- **Freshest honest source measured: 4.2-minute lag, 10-minute cadence** — by far the closest to "as realtime as honestly possible" of every free public option.
- It is **true ground-radar observation over the exact corridors** (PAGASA national network, 9 PH stations; live echo over Metro Manila confirmed in the probe), not a coarse 0.1° satellite estimate and not a forecast.
- **Zero CI burden, zero secrets, zero scrape**: CORS is wide open (`access-control-allow-origin: *` confirmed on both the JSON manifest and a PNG tile). The browser fetches `weather-maps.json` directly and renders the latest `radar.past` frame as a Leaflet/MapLibre XYZ overlay. Nothing to run in GitHub Actions for the heartbeat itself.
- Reproducible by anyone: the manifest URL is public, documented, no key.

**Client-side fetch vs server cron:** client-side. The data is CORS-open and unauthenticated, so the freshest possible frame is whatever the browser pulls at page load — server-cron would only add staleness and a moving part. (This also keeps it a true static Astro/Vercel site with no new backend.)

**Freshest cadence honestly achievable:** new radar frame every **10 minutes**, surfaced **~5–10 min after observation** (4.2 min measured at probe; budget 5–10 min to be conservative). Label with the actual frame timestamp from the manifest, never a generic "live".

**Mandatory honesty + risk handling (must be enforced in the UI/code):**
- Literal label string: **`Rain radar: PAGASA national radar via RainViewer — last frame {frameUTC} (~{age} min ago). Ground-radar observation, not a forecast. Source: RainViewer / PAGASA.`**
- Always render the manifest's frame timestamp; if the newest frame is older than ~30 min, show a "radar feed delayed" state instead of pretending freshness.
- Use only `radar.past` (observation). Do **not** surface `radar.nowcast` — it was empty at probe and, when present, is extrapolation/forecast; mixing it would break the observation-vs-forecast honesty constraint.
- Attribution to RainViewer + PAGASA visible on the map (ToS requires it).
- **Licensing caveat to flag to the team:** RainViewer ToS says the public API is "free for personal or educational use only" and gives "no guarantee of availability." FloodWatch.PH is a civic/educational non-commercial project so this is defensible, but it is a real dependency-fragility note (third-party can change/withdraw the feed). Recommended secondary heartbeat for resilience: **GPM IMERG Early (GPM_3IMERGHHE, 4 h, NASA, fully public-data)** behind a GitHub Actions server-cron using an Earthdata machine token — explicitly slower (4 h) and clearly the fallback, but pure NASA data with no ToS ambiguity. And keep the **existing EE IMERG/GSMaP as the multi-day accumulation/context layer** (honestly labeled "~1–2 days behind, not live").

Net: RainViewer/PAGASA radar is the heartbeat (minutes-fresh, observation, no CI/secrets), with NASA IMERG Early as the public-data fallback and EE IMERG as the accumulation context — a layered design where every layer carries its own honest latency label.

---

## Sources
- EE IMERG V07 catalog — https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07
- EE GSMaP V8 operational catalog — https://developers.google.com/earth-engine/datasets/catalog/JAXA_GPM_L3_GSMaP_v8_operational
- NASA GPM IMERG runs/latency — https://gpm.nasa.gov/data/imerg
- GES DISC GPM_3IMERGHHE Early (Earthdata) — https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imerghhe-07
- RainViewer API docs / ToS — https://www.rainviewer.com/api.html ; https://www.rainviewer.com/terms.html
- RainViewer PH (PAGASA/PANAHON, 9 stations) — https://www.rainviewer.com/radars/philippines.html
- JAXA Global Rainfall Watch / GSMaP — https://sharaku.eorc.jaxa.jp/GSMaP/ ; GSMaP_NOW https://sharaku.eorc.jaxa.jp/GSMaP_NOW/
- NOAA Himawari-9 open data (anonymous S3) — probed `s3://noaa-himawari9` ; registry https://registry.opendata.aws/noaa-himawari/
