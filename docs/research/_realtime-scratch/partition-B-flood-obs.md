# Partition B — Observed Flood Faster Than Sentinel-1

Research date: 2026-05-17. Every latency figure below is either measured by live probe (timestamped curl output pasted) or cited to a primary-source URL. No guessed numbers.

## TL;DR

There IS an honest, genuinely-faster-than-S1, 100%-public, CORS-fetchable observed flood layer worth adding — in fact **two**, at different speed/honesty trade-offs:

1. **NASA LANCE VIIRS/MODIS NRT Global Flood** via NASA GIBS WMTS — ~250 m, daily, **3 h LANCE latency, ~5 h max to GIBS imagery**, `access-control-allow-origin: *`, no token, live tile probed HTTP 200 over Manila for 2026-05-15. Optical, cloud-limited (the same typhoon cloud that makes SAR the primary). Add as **supplementary observed, cloud-limited**.
2. **Copernicus EMS GFM** (Sentinel-1 ensemble flood mask) via the **EODC public STAC** (`stac.eodc.eu`) — 20 m, per-S1-pass, **PUM-guaranteed ≤ 8 h timeliness (60-min internal lead-time)**, STAC CORS reflects `access-control-allow-origin: https://floodwatch.ph`, no token on STAC, CC BY 4.0. Probed: 3 real ensemble flood items over Luzon dated 2026-05-15/16, COG asset HTTP 200, titiler XYZ tilejson resolves. This is observed SAR flood **faster than FloodWatch's own raw-S1 pipeline** because GFM does the processing for you in <8 h vs CDSE GRD's 24 h publication SLA.

**Corrected honest current S1 number for FloodWatch's existing layer:** S1B failed Dec 2021; S1C operational since ~early May 2025; the constellation is now **S1A + S1C with a 6-day repeat cycle restored ~May 2025** (12-day per-satellite, 6-day combined where both cover). Acquisition→GRD-product publication on CDSE is **24 h (standard timeliness SLA)**. So FloodWatch's "latest usable pass" layer over Luzon is honestly **~6-day revisit + ~24 h publication latency**, not the older "6–12 day" framing — the 12-day figure was the single-satellite (S1A-only) era and is now out of date.

---

## Matrix

| Column | (1) NASA LANCE VIIRS/MODIS NRT Flood | (2) Copernicus EMS GFM | (3) FloodWatch's existing raw S1 (recalibrated) |
|---|---|---|---|
| Product / feed | `VIIRS_Combined_Flood_1-Day` / `_2-Day` / `_3-Day` and `MODIS_Combined_Flood_*` on NASA GIBS WMTS (`gibs.earthdata.nasa.gov/wmts/epsg4326/best`). Underlying: VCDWD (VIIRS) + MCDWD (MODIS) LANCE products. | Collection `GFM` on EODC STAC (`stac.eodc.eu/api/v1`), assets `dlr_flood_extent` / `tuw_flood_extent` / `list_likelihood` / `tilejson`. Also `api.gfm.eodc.eu/v1/` (token-gated) + WMS-T + GloFAS portal. | Sentinel-1 GRD IW VV via CDSE / ASF. |
| TRUE latency | **Measured/cited:** LANCE NRT "within the standard LANCE latency window of **3 hours or less from observation**"; "additional latency of about **2 hours** for ingest into GIBS/Worldview, resulting in potentially a **5 hour total latency (maximum)**" — *MCDWD/VCDWD User Guide Rev E §6.4, p.31–33* (PDF text extracted, pasted below). | **Cited:** "product timeliness **less than or equal to 8 hours**, for all Sentinel-1 GRD scenes that become available on the ESA data hubs within 5 hours from acquisition"; "Total lead-time of the GFM Product is **60 minutes**, to complete the entire operational NRT workflow from image acquisition to delivery" — *GFM Product User Manual GFM D 6.1, p.10* (PDF text extracted, pasted below). | **Cited:** CDSE Sentinel-1 GRD expected timeliness = **24 h after sensing** (CDSE timeliness SLA / FAQ). NRT-1h/NRT-3h GRD streams exist at ESA but are not the routinely-published CDSE/ASF standard product. |
| Cadence | Daily composites. 1-Day (lowest latency, cloud-shadow false-positive risk), 2-Day, 3-Day (more robust, more latency). GIBS time dim is `P1D`, extends to today. | Per Sentinel-1 pass (event-driven, every GRD scene processed). | Per S1 pass; **6-day** combined revisit (S1A+S1C) over areas both cover. |
| Spatial resolution | ~250 m (MODIS native 250 m; VIIRS native **375 m** resampled to the 250 m MODIS grid — cited User Guide §1, §3). | **20 m** (`OC020M` = output 20 m grid; observed in asset paths). | ~10 m (GRD IW). |
| PH + Metro-Manila / SLEX-NLEX coverage | **Confirmed.** Live probe: GIBS VIIRS flood tile at z6/x52/y19 (covers Luzon ~121E/14.5N) returned HTTP 200, real 26 KB PNG, `layer-time-actual: 2026-05-15`. Global product, MODIS h-v tiling, 287 tiles, Luzon covered. | **Confirmed.** Live STAC query `bbox=120,14,122,15` returned 3 ensemble flood items, bboxes spanning lon 120.2–122.9 / lat 11.8–17.2 (Manila Bay → central Luzon, includes the NLEX/SLEX corridor band). | Global; Luzon covered. |
| Access mechanism | WMTS / XYZ PNG tiles, browser-fetchable. **Probed CORS: `access-control-allow-origin: *`** on WMTSCapabilities and tiles. No token, no Earthdata login for GIBS imagery (login only needed for raw HDF/GeoTIFF off LANCE). Not in Google Earth Engine NRT (EE only has historical `GLOBAL_FLOOD_DB/MODIS_EVENTS/V1`, 2000–2018). | **STAC REST**, public, no token. **Probed CORS: STAC reflects `access-control-allow-origin: https://floodwatch.ph`** with `Origin` header. Assets: COG GeoTIFF on `data.eodc.eu` (HTTP 200, **no ACAO** — not directly browser-cross-origin, fetch server-side or via titiler), and a **titiler XYZ `tilejson`** (`titiler.services.eodc.eu/cog/...`, CORS `*`) that IS browser-renderable as a raster tile layer. `api.gfm.eodc.eu/v1/` requires a 5-h token (avoid; use the open STAC instead). | CDSE OData/STAC + ASF; token/Earthdata for bulk; FloodWatch already integrates it. |
| Licence + cost | Free, public, no cost, no token for GIBS imagery. NASA open data. | **CC BY 4.0** (PUM: "reuse of this document is authorised under the Creative Commons Attribution 4.0 International (CC BY 4.0) licence"; "all components for the RESTful API access are distributed as open and free licenses"). STAC `license` field literally returns `"proprietary"` — this is an EODC catalog metadata default; the governing Copernicus EMS policy is free+open / CC BY 4.0. Cite Copernicus EMS, not the STAC field. Free. | Copernicus free+open. |
| Reproducible-in-CI? | **Yes.** Stable documented WMTS endpoint + ISO8601 time dimension. CI can resolve "latest available date" by reading `WMTSCapabilities.xml` (a single `curl`, no auth) and pin the tile template. No scrape. | **Yes.** Documented STAC API (OGC API Features + STAC). CI does `GET /search?collections=GFM&bbox=...&sortby=-properties.datetime&limit=1`, no auth, gets newest scene + asset hrefs deterministically. No scrape, no fragile portal. | Yes (already in pipeline). |
| Observation vs forecast | **Observation** (optical water/flood detection). | **Observation** (SAR ensemble flood extent). | **Observation.** |
| EXACT honest-label UI string | `Supplementary observed flat-water signal: NASA LANCE VIIRS NRT flood, {DATE} 1-day composite. Optical (~250 m), cloud-limited — typhoon cloud often blanks it. Not the primary layer, not live, not a forecast.` | `Faster observed SAR flood: Copernicus EMS GFM ensemble, Sentinel-1 pass {DATETIME} (delivered ≤8 h after acquisition). 20 m, all-weather radar. Observed, not a forecast; gaps where no recent S1 pass.` | `Latest usable Sentinel-1 SAR pass: {DATE}. S1A+S1C, ~6-day revisit, ~24 h product latency. Dated ground truth — not live, not a forecast.` |

---

## Probe output (pasted, timestamped 2026-05-17 ~03:13–03:16 UTC)

### NASA GIBS WMTS — CORS + layer list

```
$ curl -sI 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml'
HTTP/2 200
content-type: text/xml
access-control-allow-origin: *
cache-control: public, max-age=1800

# flood/water identifiers found:
MODIS_Combined_Flood_1-Day / _2-Day / _3-Day
MODIS_Water_Mask
VIIRS_Combined_Flood_1-Day / _2-Day / _3-Day
```

### GIBS flood layer time dimension (live, extends to today)

```
VIIRS_Combined_Flood_1-Day  Dimension Time  Default 2026-05-16  Value 2025-06-24/2026-05-16/P1D  TileMatrixSet 250m  Format image/png  bbox -180 -90 / 180 90
MODIS_Combined_Flood_1-Day  Dimension Time  Default 2026-05-17  Value 2023-07-26/2026-05-17/P1D  TileMatrixSet 250m
```

### GIBS VIIRS flood tile over Manila — live fetch

```
$ curl -sI '.../VIIRS_Combined_Flood_1-Day/default/2026-05-15/250m/6/19/52.png'
HTTP/2 200
content-type: image/png
content-length: 26431
layer-identifier-actual: VIIRS_Combined_Flood_1-Day_v2.0_NRT
layer-time-request: 2026-05-15
layer-time-actual: 2026-05-15T00:00:00Z
```

### LANCE MCDWD/VCDWD User Guide Rev E — latency (PDF text extracted)

> "The NRT download sites are updated in near real-time ... This should be within the standard LANCE latency window of **3 hours or less from observation**." (§6.4)
> "For Worldview, there is an additional latency of about **2 hours** for ingest into GIBS/Worldview, resulting in potentially a **5 hour total latency (maximum)** from observation to the product appearing in Worldview." (§6.4, p.33)
> "two global daily ~250 m resolution NRT flood products: MCDWD ... and VCDWD"; "the VIIRS instrument resolution is coarser, at **375 m**, compared to MODIS at 250 m ... generated at 250 m resolution" (§1, §3)
> Source PDF: https://www.earthdata.nasa.gov/s3fs-public/2025-04/MCDWD_VCDWD_UserGuide_RevE_04.22.25.pdf

### Copernicus GFM EODC STAC — collection + Luzon query

```
$ curl 'https://stac.eodc.eu/api/v1/collections/GFM'
id: GFM   title: Global Flood Monitoring   license: proprietary
temporal: 2015-01-01 .. (open)   spatial: global
description: "...processing and analysing in near real-time (NRT) all incoming SAR imagery acquired by Sentinel-1 ... IW mode ... GRD products."

$ curl 'https://stac.eodc.eu/api/v1/search?collections=GFM&bbox=120,14,122,15&limit=3&sortby=-properties.datetime'
returned: 3
 ENSEMBLE_FLOOD_20260516T095810_VV_OC020M_E057N111T3  datetime 2026-05-16T09:58:10Z  bbox [120.23,11.75,122.87,14.52]
 ENSEMBLE_FLOOD_20260516T095745_VV_OC020M_E057N111T3  datetime 2026-05-16T09:57:45Z
 ENSEMBLE_FLOOD_20260515T100647_VV_OC020M_E057N114T3  datetime 2026-05-15T10:06:47Z  bbox [120.19,14.46,122.86,17.22]
assets: tilejson, thumbnail, advisory_flags, dlr_likelihood, exclusion_mask, tuw_likelihood, list_likelihood, dlr_flood_extent, tuw_flood_extent
```

### GFM asset + titiler + CORS probes

```
$ curl -sI '.../GFM_NRT_INTERIM/flood_extent/.../DLR_FLOOD_20260516...T3.tif'
HTTP/2 200   content-type: image/tiff; application=geotiff   content-length: 128855
# (no access-control-allow-origin on data.eodc.eu COG -> not browser cross-origin direct; use titiler/STAC)

$ curl 'https://stac.eodc.eu/api/v1/search?...' -H 'Origin: https://floodwatch.ph'
HTTP:200
access-control-allow-origin: https://floodwatch.ph        <-- STAC is browser-fetchable

titiler tilejson resolves: titiler.services.eodc.eu/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=<COG>&colormap=...
(titiler responds with access-control-allow-origin: *)
```

### GFM Product User Manual (GFM D 6.1) — latency + license (PDF text extracted)

> "the entire GFM consortium is used to ensure a **product timeliness less than or equal to 8 hours**, for all Sentinel-1 GRD scenes that become available on the ESA data hubs **within 5 hours from acquisition**." (p.10)
> "**Total lead-time of the GFM Product is 60 minutes**, to complete the entire operational NRT workflow from image acquisition to delivery." (Table 3, p.10)
> "the reuse of this document is authorised under the **Creative Commons Attribution 4.0 International (CC BY 4.0) licence**"
> "all components for the RESTful API access are distributed as **open and free licenses**"
> Note: `api.gfm.eodc.eu/v1/` needs a token valid 5 h (avoid). The **public STAC at stac.eodc.eu needs no token** — confirmed by unauthenticated 200s above.
> Source PDF: https://extwiki.eodc.eu/gfm_assets/gfm_pum_v20231005_compressed.pdf

### Sentinel-1 constellation + CDSE latency (cited)

- S1B anomaly Dec 2021 (mission ended). S1C launched 5 Dec 2024, **user data opening 26 Mar 2025**, operational ~early May 2025 end of commissioning → **6-day repeat restored, S1A+S1C** (S1D opened 17 Apr 2026, triple-sat overlap mid-Apr→Jun 2026, final S1C/S1D 6-day config from late Jun 2026).
  - https://dataspace.copernicus.eu/news/2025-3-25-sentinel-1c-user-data-opening-26th-march
  - https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel1.html
- **CDSE Sentinel-1 GRD expected timeliness = 24 h after sensing** (standard SLA). https://documentation.dataspace.copernicus.eu/FAQ.html , https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel1.html

---

## Recommendation

**Add both, ranked, both client-fetch (no cron needed).**

**Primary new "faster observed" layer → Copernicus EMS GFM via EODC STAC.** It is observed SAR flood (all-weather, the right physics for typhoons), 20 m, delivered ≤8 h after a Sentinel-1 pass — i.e. it surfaces the *same* satellite FloodWatch already trusts, but ~16 h sooner than waiting on CDSE's 24 h GRD publication and with the flood mask already computed. Access is a single unauthenticated STAC `GET` (CORS reflects the site origin) → newest scene over a Luzon bbox → render the `tilejson` (titiler XYZ, CORS `*`) or pull `dlr_flood_extent` COG server-side. Reproducible-in-CI with one documented STAC query, no scrape, no token, CC BY 4.0. **Honest framing:** still pass-gated (no S1 pass = no new GFM), so it is "faster observed", not "live"; label with the scene datetime, never imply continuous coverage. Caveat to verify before shipping: the STAC `license` field literally says `proprietary` — attribute to Copernicus EMS / CC BY 4.0 in the credit line and add a one-line note that the EODC STAC metadata default does not reflect the open Copernicus EMS policy; if a stricter reading is wanted, treat GFM as document-as-future pending an explicit Copernicus EMS data-policy citation, but the PUM language ("open and free licenses", CC BY 4.0) supports shipping it.

**Secondary supplementary layer → NASA LANCE VIIRS NRT flood via GIBS.** Fastest of all (3 h LANCE, ~5 h to GIBS imagery), trivial CORS-`*` WMTS tiles, zero auth, daily. But it is optical and cloud-limited — during the exact typhoon conditions FloodWatch cares about, cloud blanks it, which is precisely why SAR is primary. Ship it strictly as **"supplementary observed, cloud-limited"** with the literal label above, default off or clearly subordinate, and let GFM/S1 carry the load when cloud wins. Reproducible-in-CI by reading `WMTSCapabilities.xml` to pin the latest date.

**Client-fetch vs cron:** both are client-fetch. STAC and GIBS WMTS are CORS-enabled and cheap; the browser resolves "latest scene/date" at view time. No server, no cron, no key — consistent with FloodWatch's no-paid-deps / no-fragile-scrape constraint. (If you want CI to *verify* the feeds stay alive, add a 1-request smoke check per feed to the existing CI, not a data cron.)

**Corrected honest current S1 number to surface in FloodWatch's existing layer copy:** revisit is now **~6 days (S1A + S1C, restored ~May 2025)**, not 6–12; product publication latency is **~24 h (CDSE GRD standard SLA)**. Update the existing S1-layer caption — the "6–12 day" wording is stale single-satellite-era framing.

File: `/Users/xavier/Desktop/floodwatch-ph/docs/research/_realtime-scratch/partition-B-flood-obs.md`
