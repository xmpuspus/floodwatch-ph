# P2 security / CSP recheck — v1.3 cinematic-visual wave

Scope: the four v1.3 visual surfaces P1 added over the v1.2 corridor — NASA
GIBS true-colour satellite basemap, SAR-as-raster, animated observed-rain
playback, and the dated Carina-2024 satellite hero. Question: does the new
surface introduce any new origin, secret, user-input, or privacy regression.

Verdict: **CLEAN. No Critical/High. No Medium. No vercel.json change made or
needed.**

Files inspected (read-only, no edits by P2 to any of these):
- `site/src/lib/realtimeClient.ts` (the v1.3 fetchers)
- `site/src/components/CorridorWatch.astro` (basemap + rain wiring)
- `site/src/components/MapView.astro` (Carina-tab basemap toggle)
- `site/src/pages/index.astro` (hero)
- `site/vercel.json` (CSP — read only, unmodified)

## (a) GIBS true-colour basemap uses an already-CSP-allowed origin

The v1.3 true-colour basemap host is `gibs.earthdata.nasa.gov` — the SAME
origin v1.2 already cleared for the VIIRS NRT flood layer. Evidence:

`fetchGibsTrueColor()` (realtimeClient.ts:307-340) fetches a single fixed URL:

    https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml

then builds the tile template from a fixed `TRUECOLOR_LAYERS` const
(`VIIRS_SNPP_CorrectedReflectance_TrueColor`, MODIS fallback) + the
capabilities-resolved date, on the same host. The CSP in
`site/vercel.json:25` already lists `https://gibs.earthdata.nasa.gov` in BOTH
`img-src` and `connect-src`. No new origin. **vercel.json is unchanged**
(`git status --short` shows it is not in the modified set; `git diff
site/vercel.json` is empty).

The v1.3 basemap therefore needs zero CSP edit. The new GIBS true-colour
product is a NEW data *source* (flagged by Agent F §7 note 5 for P3 to record)
but NOT a new *origin* — it is the same EOSDIS GIBS host, US-gov public
domain, no auth.

## (b) No secret / key / user-input in any v1.3 fetch

Every v1.3 request is a fixed URL or a fixed-template URL whose only variable
is a remote-capabilities-resolved date / a manifest-listed tile path:

- Basemap capabilities: hardcoded WMTSCapabilities.xml URL (no query string).
- Basemap tiles: fixed REST WMTS XYZ template
  `.../{id}/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg` —
  `{id}` from the fixed const, `{date}` from the GIBS capabilities XML,
  `{z}/{y}/{x}` are MapLibre tile coords (the fixed Luzon viewport), never
  user input.
- Rain playback frames: hardcoded `https://api.rainviewer.com/public/
  weather-maps.json`; `host` + per-frame `path` come from that manifest,
  every derived URL passes `assertAllowedUrl` before fetch/MapLibre.
- `getJSON` / `getText` (realtimeClient.ts:87-96) issue `fetch(url, {signal,
  mode:"cors"})` — no `Authorization` header, no credentials, no cookies, no
  custom headers. There is no API key anywhere in the v1.3 path (RainViewer
  public endpoint + GIBS public-domain WMTS are keyless by design).
- No `localStorage`, `location.search`, `searchParams`, `navigator.geo*`, or
  `prompt()` feeds any v1.3 fetch. The basemap + rain loop take a fixed
  nationwide/Luzon view; there is NO lookup query on this surface (the
  area/route lookup is the separate `/lookup` page, unchanged this wave).

Header-injection / SSRF: not reachable. The capabilities and manifest URLs
are string literals; the only externally-influenced values (RainViewer host,
manifest path; GFM STAC hrefs) are host-validated by `assertAllowedUrl`
(https-only, hostname against a closed allow-list) BEFORE they are fetched or
handed to MapLibre — defense-in-depth one layer before the browser CSP
(OWASP ASI06 RAG/manifest poisoning, ASI08 cascading).

## (c) assertAllowedUrl still gates manifest-derived URLs; GIBS host in it

`assertAllowedUrl` (realtimeClient.ts:111-126) is intact and is the gate for
every manifest-derived URL. Allow-list (https-only):

    rainviewer.com / *.rainviewer.com
    gibs.earthdata.nasa.gov     <-- the v1.3 basemap + VIIRS host, present
    stac.eodc.eu
    titiler.services.eodc.eu

`gibs.earthdata.nasa.gov` is in the list, so the v1.3 basemap tile URL (built
through `assertAllowedUrl(...)` at realtimeClient.ts:321) and the rain frame
URLs (`assertAllowedUrl(...)` at :364) are validated. Non-https or off-list
hosts throw and degrade to the honest-empty / OSM fail-safe — never a broken
or attacker-controlled tile. The allow-list still mirrors the
`vercel.json` CSP `connect-src`/`img-src` exactly (no drift).

## (d) RA-10173 (Data Privacy Act) invariant intact

The privacy posture is unchanged. The header comment at
realtimeClient.ts:11-12 states it and the code holds: every v1.3 request
carries a FIXED nationwide bbox / fixed tile coordinates; the user's
area-lookup query is never in any v1.3 request. The cinematic surfaces
(basemap, rain loop, SAR raster, hero) take no user input at all — they
render the fixed Luzon/Metro-Manila viewport. No new PII, no new client
storage, no new third-party beacon. The "lookup stays in the browser"
invariant is untouched (the lookup is a different page, not modified here).

## OWASP ASI quick pass (agentic/supply-chain relevant items)

- ASI04 (supply chain): no new SDK/dep; GIBS true-colour is the same EOSDIS
  host already vetted in v1.2. No pin change.
- ASI06 (data/manifest poisoning): `assertAllowedUrl` validates every
  manifest-derived host before use; poisoned RainViewer host or GFM href
  degrades to honest-empty, not a fetch to an attacker origin.
- ASI05 (RCE via output): no `eval`, no `innerHTML` of remote data in the
  v1.3 path. Basemap/rain set MapLibre raster `tiles` (string template) and
  `setLayoutProperty` visibility only; the SAR raster reuses the v1.2
  GeoJSON layer (appearance-only restyle, no new sink). Road popup HTML
  escaping is v1.2 code, unchanged.

## Conclusion

The v1.3 cinematic surface is additive over a security model that already
covered its only external origin. No new origin, no secret, no user input,
no privacy regression, no CSP edit. `site/vercel.json` is byte-unchanged.
Clean — Critical/High: 0, Medium: 0.
