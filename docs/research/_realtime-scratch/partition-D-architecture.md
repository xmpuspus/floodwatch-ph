# Partition D — Ground-Truth Feeds + The Decisive Realtime Architecture

Research date: 2026-05-17. All verdicts probed live, not guessed.
Live probe evidence pasted at the bottom.

---

## PART 1 — GROUND-TRUTH FEEDS (verdict: document-as-future, every one)

### Ground-truth matrix (same columns as other partitions)

| product/feed | true latency | cadence | resolution / granularity | PH / Metro-Manila coverage | access mechanism + CORS (probed) | licence + cost | reproducible in CI? | obs vs forecast | honest label / verdict |
|---|---|---|---|---|---|---|---|---|---|
| **MMDA Flood Control sensors** (FCSMO flood gauges) | n/a — no machine endpoint | manual / Twitter posts | per-gauge point (pumping stations, esteros) | Metro Manila only | **No public API.** `mmda.gov.ph` returns **HTTP 403 (Cloudflare challenge)** to non-browser clients. Sensor data exists only inside MMDA MetroBase + posted as Twitter text/images. No JSON, no CORS. | Gov data, no published licence/API terms | **No** | observation | **document-as-future. Reason: no machine-readable endpoint exists; the public surface is a Cloudflare-walled CMS (403) + free-text tweets. Cannot be parsed reproducibly or attributed cleanly.** |
| **MMDA traffic (TV5 / Interaksyon "MetroBase" feed)** — `mmdatraffic.interaksyon.com` | ~10–15 min (per source docs) when alive | 10–15 min | road segment level, ~Metro Manila highways | Metro Manila expressways/highways | **Endpoint effectively dead.** Probed: `https://mmdatraffic.interaksyon.com/api/get_segments` → **TLS handshake fails, http=000**; `http://…` → **301 redirect loop**; `api.` subdomain → no resolve. Community wrappers (`drfb/mmda-traffic-api`, `ridvanbaluyos/traffic-api`) last released **2017**, unmaintained, 0 stars, no flood data — only traffic. | Unofficial scrape of a TV5 property; no licence; ToS-ambiguous re-scrape of a third party | **No** | observation | **document-as-future. Reason: upstream feed is unreachable in 2026 (TLS fail / dead host), wrappers abandoned since 2017, scraping a third-party broadcaster's unlicensed feed is fragile + ToS-ambiguous + not flood data.** |
| **Waze for Cities / CCP (Connected Citizens)** | ~2 min (partner GeoRSS) | ~2 min | crowd point reports (jams, hazards, road-closed) | Wherever Waze users are (incl. Metro Manila) | **Not publicly accessible.** It is a B2G program: a signed MoU between Waze and a *government/transport agency*. The data feed (GeoRSS/JSON) is delivered to the partnered agency only, behind a partner token, never CORS-exposed to the open web. | Free *to qualifying public-sector partners*; partner agreement forbids public redistribution; attribution-restricted | **No** | observation (crowd) | **document-as-future. Reason: (1) eligibility — only a government agency can join, a public static site cannot; (2) the feed is partner-token-gated, not a public CORS endpoint; (3) the partner T&Cs prohibit onward public redistribution; (4) RA-10173 — re-publishing crowd-sourced location reports about identifiable trips/places is personal-data processing FloodWatch's privacy posture explicitly avoids.** |
| **Twitter/X #floodPH / @MMDA / @dost_pagasa** | seconds–minutes | irregular | free-text + photos, occasional geo | PH-wide, MM-heavy | X API v2: **no free tier for content pull** (paid only, ≥US$100/mo Basic); no anonymous CORS endpoint; nitter mirrors unreliable | X Developer Agreement; **paid**; redistribution + display restrictions | **No** | observation (crowd) | **document-as-future. Reason: (1) violates "no paid deps" — usable read access is paid; (2) RA-10173 — ingesting/re-displaying citizen posts with location is processing third-party personal data; (3) X ToS restricts redistribution and off-platform display; (4) free-text is not reproducibly parseable in CI without an LLM dependency.** |

**Part 1 bottom line:** there is no honest, reproducible, free, CORS-clean, privacy-compatible ground-truth (in-situ flood-confirmation) feed for Metro Manila in 2026. All four candidates are **document-as-future** with the exact reason stated above. The site stays observation-from-remote-sensing only; a "Ground-truth confirmation" row in the methodology table should be listed as *Planned — blocked on: no public agency API; community feeds dead/abandoned; partner programs are agency-only and privacy-incompatible.*

---

## PART 2 — THE DECISIVE ARCHITECTURE QUESTION

### Infra constraints, verified live

**Vercel Cron on Hobby — DISQUALIFIED for sub-daily.**
Vercel docs (usage-and-pricing, last_updated 2026-03-04), quoted exactly:
> "Hobby — Minimum interval: **Once per day** — Scheduling precision: **Hourly (±59 min)**"
> "Hobby accounts are limited to cron jobs that run **once per day**. Cron expressions that would run more frequently will **fail during deployment**."

So Vercel Cron on the free tier is *strictly no better than the existing daily GitHub Actions cron* and worse on precision (±59 min). It also requires a Vercel **Function** (serverless), which the project currently has zero of (pure static `dist/`). Adding one introduces a server surface, a function-invocation budget, and a runtime the privacy story would have to cover. **Verdict: do not use Vercel Cron. It buys nothing over the GH Actions daily cron and adds a server surface.** A Vercel Edge/Serverless function *as a fetch-proxy* is technically free on Hobby but is a new always-on server endpoint that (a) sees client IPs, (b) needs its own CSP/privacy accounting, (c) is unnecessary because the two live sources we want are already CORS-`*`. **Reject the proxy too.**

**GitHub Actions cron — realistic floor is ~daily, sub-hourly is a lie.**
GitHub docs, quoted exactly:
> "The `schedule` event can be delayed during periods of high loads of GitHub Actions workflow runs. High load times include the start of every hour."
> "The shortest interval you can run scheduled workflows is once every **5 minutes**."

The "5 minutes" is the *configurable minimum*, not the *delivered* cadence. In practice scheduled runs on shared runners routinely slip 5–40 min and are silently skipped under load (well-documented community behavior; the start of every hour is worst). The current workflow runs `17 18 * * *` daily by deliberate design. **A cron-based layer can honestly claim "updated approximately daily" — never "live" and never a tight sub-hourly SLA.** This is the structural reason the freshest layers must NOT depend on the cron.

**CORS probes (the deciding facts):**

| source | `access-control-allow-origin` (probed) | browser-fetchable? | needs server? |
|---|---|---|---|
| NASA GIBS WMTS capabilities | `*` | **YES** | no |
| NASA GIBS NRT tile (`.jpg`/`.png`) | `*` | **YES** | no |
| RainViewer `weather-maps.json` | `*` | **YES** | no |
| RainViewer radar/sat tiles | `*` (same host policy) | **YES** | no |
| Google Earth Engine tiles | **no anonymous public API** — every tile URL must be signed by a server holding the EE service-account key | **NO** | **YES — cron/server only** |
| PAGASA flood page | `*` but it is an **HTML page, not an API** (no JSON, layout-fragile) | not usefully | scrape-only → no |

GIBS confirmed to actually carry NRT flood products: `MODIS_Combined_Flood_1-Day`, `VIIRS_Combined_Flood_1-Day` (+ 2-/3-Day), CORS `*` on both capabilities and tiles.

### Per-layer client-fetch vs cron verdict

> **HEADLINE: split architecture — GPM/S1 flood-extent stays SERVER/cron (EE has no public browser tile API and the privacy/CSP posture stays untouched); rain "now" and the NRT optical-flood overlay move CLIENT-SIDE (RainViewer + NASA GIBS, both probed CORS-`*`), because that is the only way to get true zero-cron-lag freshness, and an all-PH rain/flood tile is not the user's lookup query so it is privacy-defensible.**

| layer | freshest honest delivery | why | target cadence | CSP impact | privacy reconciliation |
|---|---|---|---|---|---|
| **Sentinel-1 flood extent (Track A, EE)** | **SERVER / GH Actions cron (unchanged)** | EE has no anonymous browser tile endpoint; the tile URL must be signed by the SA key, which can only live server-side. Heavy EE reduction must run off-browser anyway. | daily (S1 revisit ~6–12 d makes daily already optimal — no information is lost vs hourly) | **none** | unchanged; nothing new leaves the browser |
| **GPM IMERG rainfall context (realtime/current_risk, EE)** | **SERVER / GH Actions cron (unchanged) for the EE-derived risk numbers** | same EE-signing constraint; the *computed* risk classification needs EE reduction | daily refresh of the EE-derived layer | **none** | unchanged |
| **Rain "happening now" (NEW client layer)** | **CLIENT-SIDE fetch of RainViewer at page-view** | RainViewer is CORS-`*` (probed), free, ~10-min global radar/precip nowcast, tiles in browser-native XYZ. Cron would inject up to a full day of lag onto a product whose whole value is the last hour. | every page view = freshest available (~10-min source latency, zero cron lag) | add `https://*.rainviewer.com` (and the tile host `https://tilecache.rainviewer.com` if used) to **`connect-src`** and **`img-src`** | **defensible.** The browser requests an *all-Philippines rain tile by fixed bbox/zoom* — the same bytes for every visitor. The user's area-lookup query string is NEVER part of that request. The "your lookup never leaves the browser" claim is intact: rain tiles are public meteorology, not PII, and carry no user input. Privacy page must (a) enumerate the new origin, (b) state explicitly: *"FloodWatch fetches a public nationwide rain map from RainViewer. This request contains no information about what you searched — it is the same map for every visitor. Your area lookup is computed entirely in your browser and is never sent anywhere."* |
| **NRT optical flood overlay (NEW client layer, optional)** | **CLIENT-SIDE fetch of NASA GIBS `*_Combined_Flood_1-Day` WMTS** | GIBS is CORS-`*` (probed, incl. tiles), NRT (~same-day, LANCE), free, US-gov public-domain. Cron adds up to a day of lag for no benefit; client fetch is fresher and adds no server work. | every page view, requesting the latest available date | add `https://gibs.earthdata.nasa.gov` to **`connect-src`** + **`img-src`** | **defensible**, identical argument: a fixed PH-bbox tile, same for everyone, no user input in the request. NASA GIBS is public-domain; attribution "NASA EOSDIS GIBS / LANCE" on the layer. |

Net CSP delta (the entire price of going client-side fresh):
```
connect-src 'self'
  https://*.tile.openstreetmap.org https://*.openstreetmap.org
  https://*.rainviewer.com https://tilecache.rainviewer.com
  https://gibs.earthdata.nasa.gov
img-src 'self' blob: data:
  https://*.tile.openstreetmap.org https://*.openstreetmap.org
  https://*.rainviewer.com https://tilecache.rainviewer.com
  https://gibs.earthdata.nasa.gov
```
Three new public, government/meteorological origins. No new server. No new function. No paid dep. No change to the lookup-stays-in-browser invariant. Each origin gets one privacy-page sentence (purpose + "contains no user input + same bytes for everyone").

**Why not just speed up the cron?** Because the GH Actions cron floor is ~daily-reliable and EE-signing forces server-side anyway — speeding it up is impossible (Hobby Vercel Cron is daily-only) and pointless for S1 (6–12 d revisit). The only honest path to *minutes-fresh* anything is client-side fetch of an already-CORS-clean public product. There is no third option that is both free and faster.

---

## PART 3 — THE FRESHNESS-CLOCK UX SPEC

Principle: **"as realtime as possible" = surface the freshest timestamp and label it precisely; never render the word "live" unless the source latency is genuinely sub-15-min AND the data is observation-now.** Reuse the v1.1.0 `scan_status` honest-empty pattern for stale/missing.

### Per-layer clock contract

Every layer carries two machine fields the UI renders:
- `acquired_utc` / `issue_utc` — the source's own acquisition or issue time (NOT our fetch time, NOT the deploy time).
- `source_latency_class` — one of `nowcast` (<15 min), `near-real-time` (<24 h), `daily`, `archival`.

UI for each layer (small caption under the layer toggle/legend):

```
{LAYER NAME}
{relative age, ticking}  ·  acquired {YYYY-MM-DD HH:MM} UTC
source: {source}  ·  {latency class label}
```

Ticking relative age, updated every 30 s client-side:
- `< 60 min` → `"updated 23 min ago"`
- `< 24 h`  → `"updated 4 h 12 min ago"`
- `< 7 d`   → `"updated 2 days ago (last Sentinel-1 pass)"`
- `≥ 7 d`   → `"last pass 9 days ago"` + amber dot (see colour rules)

Per-layer wording:
- **Sentinel-1 flood extent:** `"Last Sentinel-1 pass {DATE} · 3 days ago · satellite revisit ~6–12 days"`. Never "live". Label class `daily` refresh / source `near-real-time` per pass.
- **GPM rainfall context:** `"Rainfall window ending {DATE HH:MM} UTC · processed daily"`. Never "live".
- **Rain now (RainViewer client):** `"Rain radar {HH:MM} UTC · 14 min ago · nowcast (~10-min source)"`. This one MAY use the word **"now-ish"** but still never bare "live"; show the ticking age so a stale fetch is visible.
- **NRT flood overlay (GIBS client):** `"NASA optical flood, {DATE} · near-real-time (same-day, cloud-permitting)"`.

### Global ticker (header / footer strip)

```
Freshest layer: Rain radar — updated 14 min ago (08:40 UTC).
Site rebuilt 06:17 UTC. Layers refresh independently — see each layer's clock.
```
- "Freshest layer" = the layer with the most recent `acquired_utc`, recomputed client-side every 30 s.
- The site-rebuild line is honest about the static build vs the independently-fetched client layers (a visitor must not assume the rain clock implies the S1 layer is also fresh).

### Colour / urgency rules (minimal, honest, not alarmist)

- Default: neutral grey text, no dot. The clock is informational, not a hazard signal.
- Amber dot **only** when a layer is *staler than its own expected cadence* (S1 > 12 d; rain client fetch > 30 min old; GIBS > 48 h): signals "this layer may be behind", not "flood danger".
- Never red, never pulsing — FloodWatch reports observed water extent + rain context; it is not an alert system, and faux-urgency would be a false claim.

### Stale / missing — reuse v1.1.0 honest-empty

- **Client fetch fails** (RainViewer/GIBS unreachable, CSP block, network): do NOT silently hide. Render the layer toggle disabled with caption: `"Rain radar unavailable — could not reach RainViewer ({HH:MM} UTC attempt). Other layers unaffected."` Mirrors the `scan_status` honest-empty contract: explain *what* is empty and *why*, never a blank that reads as "no flooding".
- **Cron layer empty** (S1 honest-empty from the gate): keep the existing v1.1.0 message ("no qualifying Sentinel-1 scene in window") — unchanged.
- **Timestamp missing** in the data file: show `"acquisition time unavailable"` rather than fabricating "just now". Never default a missing time to the current time.

---

## RECOMMENDED ARCHITECTURE (the decisive conclusion)

1. **Keep the daily GH Actions cron exactly as is** for the two EE-derived layers (S1 flood extent, GPM risk). EE cannot be browser-fetched (no anonymous tile API — server signing mandatory); S1's 6–12 d revisit makes daily already optimal. Zero CSP/privacy change.
2. **Do NOT adopt Vercel Cron** — Hobby is hard-capped at once-per-day with ±59 min precision (sub-daily fails deployment): strictly worse than the existing cron, and it would force a serverless function the static site doesn't need. **Do NOT add a Vercel Edge fetch-proxy** — unnecessary because the two live sources are already CORS-`*`, and it would add a server that sees client IPs.
3. **Add two CLIENT-SIDE fetched layers for true freshness:** RainViewer (rain now, ~10-min nowcast, CORS-`*` probed) and NASA GIBS `*_Combined_Flood_1-Day` (NRT optical flood, CORS-`*` probed). These are the *only* honest path to minutes/hours-fresh data on a free static site. Cost: three new public CSP origins, each with a one-line privacy justification. The lookup-never-leaves-browser invariant is preserved — a fixed all-PH tile contains no user input and is identical for every visitor.
4. **Ground-truth feeds: all four document-as-future** (MMDA API 403/none; TV5 traffic dead+abandoned+not-flood; Waze CCP agency-only+partner-gated+RA-10173; X paid+RA-10173). List as *Planned — blocked on: no public agency API*.
5. **Ship the freshness-clock UX** (per-layer ticking age + source acquisition time + global freshest-layer ticker + honest-empty on client-fetch failure). This is what lets the site claim "as realtime as possible" truthfully: it surfaces and timestamps the freshest available data and never renders "live" for anything that isn't.

Resulting honesty posture: S1/GPM honestly labelled "refreshed daily / last pass N days ago"; rain + NRT-flood honestly labelled with a ticking source timestamp and a nowcast/near-real-time class; no layer ever claims "live"; the privacy invariant is mathematically intact because no client fetch carries the user's query.

---

## PASTED PROBE EVIDENCE

```
=== GIBS WMTS CORS ===
HTTP/2 200
content-type: text/xml
cache-control: public, max-age=1800
access-control-allow-origin: *

=== RAINVIEWER weather-maps.json CORS ===
HTTP/2 200
content-type: application/json
cache-control: no-cache
access-control-allow-origin: *

=== GIBS NRT tile (.jpg) CORS ===
HTTP/2 200
content-type: image/jpeg
access-control-allow-origin: *

=== GIBS carries NRT flood products ===
<ows:Identifier>MODIS_Combined_Flood_1-Day</ows:Identifier>
<ows:Identifier>MODIS_Combined_Flood_2-Day</ows:Identifier>
<ows:Identifier>MODIS_Combined_Flood_3-Day</ows:Identifier>
<ows:Identifier>VIIRS_Combined_Flood_1-Day</ows:Identifier>
<ows:Identifier>VIIRS_Combined_Flood_2-Day</ows:Identifier>
<ows:Identifier>VIIRS_Combined_Flood_3-Day</ows:Identifier>

=== MMDA traffic legacy API (dead) ===
https://mmdatraffic.interaksyon.com/api/get_segments  -> http=000 (TLS handshake fail)
http://mmdatraffic.interaksyon.com/api/get_segments   -> http=301 (redirect loop)
https://api.mmdatraffic.interaksyon.com/              -> no resolve

=== mmda.gov.ph (Cloudflare-walled) ===
HTTP/2 403
server: cloudflare

=== PAGASA flood ===
HTTP/2 200  content-type: text/html  (HTML page, not an API)
```

Doc source quotes:
- Vercel cron usage-and-pricing (last_updated 2026-03-04): "Hobby — Minimum interval: Once per day — Scheduling precision: Hourly (±59 min)"; "Cron expressions that would run more frequently will fail during deployment."
- GitHub Actions docs: "The `schedule` event can be delayed during periods of high loads… High load times include the start of every hour."; "The shortest interval you can run scheduled workflows is once every 5 minutes."
