# P2 security pass — v1.2 Corridor watch client-fetch surface

Scope: the three NEW client-side fetchers (`site/src/lib/realtimeClient.ts`),
their MapLibre wiring (`site/src/components/CorridorWatch.astro`), the CSP
delta (`site/vercel.json`), and the privacy posture
(`site/src/pages/privacy.astro` vs the shipped CSP). Self-conducted, no
external skill. Evidence quoted from the worktree at branch
`worktree/v1.2-corridor-watch`.

## Verdict

**CLEAN — no Critical, no High.** One Medium defense-in-depth observation
(GFM manifest-derived URL host is not whitelisted in code) that is fully
contained by the CSP as shipped, plus one Low note. Nothing ship-blocking.

## 1. No client-side secret / API key / token — PASS

`grep -rniE "api[_-]?key|secret|token|password|bearer|authorization|apikey"`
over `realtimeClient.ts`, `freshnessClock.ts`, `CorridorWatch.astro`: the only
hit is the word "secrets" inside an explanatory comment
(`realtimeClient.ts:6`). No `process.env`, `import.meta.env`, `PUBLIC_`, or
`VITE_` in any client lib. All three sources (RainViewer public
`weather-maps.json`, EODC STAC search, NASA GIBS WMTS capabilities) are
unauthenticated public endpoints — by design no credential is needed or
present. Built bundle
(`site/dist/_astro/CorridorWatch.astro_astro_type_script_index_0_lang.*.js`)
contains only the public hostnames (`rainviewer`, `eodc`, `earthdata`,
`titiler`), no key material.

## 2. No user input in any of the 3 fetch URLs — PASS

All three exported fetchers take **zero arguments**:
`fetchRainViewer()`, `fetchGFM()`, `fetchVIIRS()`. `wireClientLayers(sarAsOf)`
passes only `sarAsOf` (an internal cron-derived S1 timestamp used for caption
text), and it is never placed in any URL. Every request URL is a string
literal plus the fixed module constant `LUZON_BBOX = "120,14,122,18"`. The
area-lookup query symbol set (`areaLookup`, `query`, `searchParams`,
`localStorage`, `input.value`, `location.`) does not appear in
`realtimeClient.ts` at all.

Verbatim outbound URLs (the entire client-fetch surface):

- `https://api.rainviewer.com/public/weather-maps.json` (realtimeClient.ts:77)
- `https://stac.eodc.eu/api/v1/search?collections=GFM&bbox=${LUZON_BBOX}&sortby=-properties.datetime&limit=1` (realtimeClient.ts:109-110)
- `https://titiler.services.eodc.eu/cog/tiles/{z}/{x}/{y}.png?url=${encodeURIComponent(cog)}` (realtimeClient.ts:144-145)
- `https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml` (realtimeClient.ts:170)
- `https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/${VIIRS_LAYER}/default/${day}/GoogleMapsCompatible_Level8/{z}/{y}/{x}.png` (realtimeClient.ts:191-193)

`bbox` is the fixed constant. `${day}` is regex-validated
(`/^\d{4}-\d{2}-\d{2}/`, realtimeClient.ts:188) date text parsed out of NASA's
own capabilities XML — not user input. `${cog}` is discussed in §5.

The RA-10173 / "lookup never leaves the browser" invariant holds: every
request carries the identical fixed nationwide bbox / fixed tile coordinates,
so the bytes are the same for every visitor and contain nothing about what
was looked up.

## 3. CSP delta is exactly +6 origins, nothing else widened — PASS

`git diff site/vercel.json` is a single changed line (the
`Content-Security-Policy` value). The same six origins
(`https://api.rainviewer.com https://*.rainviewer.com
https://tilecache.rainviewer.com https://gibs.earthdata.nasa.gov
https://stac.eodc.eu https://titiler.services.eodc.eu`) were appended to
`img-src` and to `connect-src`. `default-src`, `script-src` (`'self'
'unsafe-inline' blob:` — unchanged, no remote script origin),
`worker-src`, `style-src`, `font-src`, `frame-ancestors`, `base-uri`,
`form-action` are byte-for-byte identical. JSON re-parses
(`python3 -c "import json; json.load(open('site/vercel.json'))"` → OK). No
directive was loosened; no wildcard scheme was introduced (every new entry is
a fully-qualified `https://` host, the one wildcard `*.rainviewer.com` being
the documented RainViewer tilecache pattern).

## 4. Privacy invariant + privacy.astro vs CSP exact match — PASS

The privacy invariant holds by construction (§2: fixed bbox, no user input).
Reconciled against agentF-v1.2-copy §7 and the shipped `privacy.astro` (P3's
copy):

CSP origins (6): `api.rainviewer.com`, `*.rainviewer.com`,
`tilecache.rainviewer.com`, `gibs.earthdata.nasa.gov`, `stac.eodc.eu`,
`titiler.services.eodc.eu`.

`privacy.astro` enumerates (lines 78-80): `api.rainviewer.com,
*.rainviewer.com, tilecache.rainviewer.com` (RainViewer line),
`gibs.earthdata.nasa.gov` (NASA GIBS line), `stac.eodc.eu,
titiler.services.eodc.eu` (EODC line). Lead sentence (line 75) and the
"What we don't publish" `<li>` (line 27) both reaffirm "no information about
what you searched / never your lookup query."

**Exact match, both directions:** every origin in the CSP is named in
privacy.astro, and privacy.astro names no origin that is absent from the CSP.
The shipped privacy copy matches the actual CSP exactly. No drift.

## 5. OWASP-style review of the client fetchers

- **SSRF — N/A.** All request origins are fixed literals; no user-controlled
  destination.
- **Response handling — PASS.** Responses are consumed as `r.json()` /
  `r.text()`. No `eval`, no `Function(...)`, no `innerHTML` of any fetched
  body. The error-fallback path writes a static string into
  `.innerHTML` (CorridorWatch.astro ~line 961) but the content is a
  hard-coded literal, not fetched data — safe.
- **Tile URL host constraint — MEDIUM (defense-in-depth gap, contained).**
  `fetchGFM` reads `a.href` and `cog` (`assets[k].href`) straight out of the
  remote STAC JSON and either re-fetches it (`getJSON(a.href)`,
  realtimeClient.ts:127) or embeds it into a titiler URL
  (`?url=${encodeURIComponent(cog)}`, realtimeClient.ts:144-145), then hands
  the resulting `tileUrl` to MapLibre via
  `map.getSource(id).setTiles([url])` (CorridorWatch.astro:794-796).
  realtimeClient.ts performs **no host allow-list** on `a.href`/`cog` before
  use. A poisoned or MITM'd STAC response could therefore point `a.href` at
  an attacker origin.
  **Why this is contained, not High:** the shipped CSP `connect-src`/
  `img-src` only allow the 6 enumerated hosts. A tilejson fetch to a non-EODC
  host is blocked by `connect-src`; tile image requests to a non-allowed host
  are blocked by `img-src`. `script-src` has no remote origin and `setTiles`
  only issues image requests, so a poisoned manifest cannot execute script or
  exfiltrate the (already user-input-free) request. Failure degrades to the
  §4d honest-empty path, not a crash. Net real-world impact with the CSP in
  place: a blocked tile request (the layer simply shows honest-empty), no
  injection. **Recommendation (non-blocking, not P2's file to edit — log for
  a P1 follow-up):** validate `new URL(href).hostname` ends with
  `.eodc.eu` before fetching/embedding, so the integrity guarantee does not
  rest on CSP alone (defense in depth). Filed as a note, not bundled into
  this PR (scope discipline).
- **AbortController timeout — PASS.** Every fetcher wraps its work in
  `withTimeout(ms)` (8 s RainViewer, 10 s GFM, 10 s VIIRS) which calls
  `AbortController.abort()` on a `setTimeout`, with `finally { t.done() }`
  clearing the timer. No fetch can hang the page.
- **Failure degrades to honest-empty, not a crash — PASS.** Every fetcher
  has `catch { return { ok: false, attemptUtc: attemptStamp() }; }`. The
  caller (`wireClientLayers`) renders the verbatim §4d honest-empty string
  via `freshnessClock.honestEmpty()` and disables the toggle with
  `DISABLED_TOGGLE_TEXT`. The whole `init()` is itself wrapped so a thrown
  error shows "Could not load the Corridor watch data. No query was sent
  anywhere." rather than a blank/broken surface.

## 6. Low note

- `script-src 'unsafe-inline'` is pre-existing (Astro inline island
  bootstrap) and unchanged by v1.2 — out of scope for this delta, recorded
  only so the next reviewer does not re-flag it as introduced here.

## Bottom line

The v1.2 client-fetch surface ships **no secret**, **no user input in any
request**, a **minimal exact +6-origin CSP delta with nothing else widened**,
and **privacy copy that matches the CSP one-to-one**. The single Medium is a
code-level defense-in-depth hardening (host-allow-list the GFM
manifest-derived URL) that the shipped CSP already neutralizes for the
real-world threat; logged for a P1 follow-up, not ship-blocking and
deliberately not bundled into the P2 scope.
