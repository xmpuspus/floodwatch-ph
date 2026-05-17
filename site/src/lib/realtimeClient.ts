// Realtime client fetchers -- the three NEW v1.2 client-side layers.
//
// Each fetcher returns a typed RealtimeLayer on success or a typed
// RealtimeFailure on failure. The UI NEVER blanks and NEVER shows "just now":
// on failure it renders the section-4d honest-empty string. No API keys, no
// secrets, no user input in any request -- only the fixed Luzon / PH bbox. If
// the CSP blocks an origin (the +6 origins are P2's job), fetch() rejects and
// we degrade to the honest-empty failure exactly like a network error, so the
// page never crashes.
//
// PRIVACY (RA 10173): every request below carries a FIXED nationwide bbox /
// fixed tile coordinates. The user's area-lookup query is never in any of
// these requests. Identical bytes for every visitor.
//
// Sources (research realtime-sources.md §2b/§3):
//   - RainViewer  GET api.rainviewer.com/public/weather-maps.json
//                 -> newest radar.past frame -> tilecache XYZ (NEVER nowcast)
//   - Copernicus GFM  GET stac.eodc.eu/api/v1/search (GFM, fixed Luzon bbox)
//                 -> newest item -> its titiler tilejson asset -> XYZ
//   - NASA GIBS  GET .../WMTSCapabilities.xml -> latest VIIRS date -> WMTS XYZ

export type SourceLatencyClass =
  | "nowcast"
  | "near-real-time"
  | "daily"
  | "archival";

export interface RealtimeLayer {
  ok: true;
  tileUrl: string;
  // ISO 8601; the source's own acquisition / frame time, NOT our fetch time.
  acquiredUtc: string;
  sourceLatencyClass: SourceLatencyClass;
}

export interface RealtimeFailure {
  ok: false;
  // UTC "YYYY-MM-DD HH:MM" of the attempt -- feeds the §4d honest-empty string.
  attemptUtc: string;
}

export type RealtimeResult = RealtimeLayer | RealtimeFailure;

// ---- v1.3 satellite true-colour basemap (NASA GIBS) -----------------------
//
// The cinematic backdrop. A DATED daily mosaic, one pass per day, NOT live.
// {basemapDateUTC} is resolved from the GIBS WMTSCapabilities -- never the
// client clock, never the build time. F1 (highest-risk): if the date cannot
// resolve, this returns ok:false and the caller MUST stay on plain OSM and
// never draw true-colour tiles.
export interface BasemapLayer {
  ok: true;
  tileUrl: string;
  // Mosaic acquisition DATE (YYYY-MM-DD) -- the §1 {basemapDateUTC}.
  basemapDateUtc: string;
  // GoogleMapsCompatible top level for this layer -> raster source maxzoom,
  // so MapLibre overzooms instead of requesting unsupported tiles.
  maxZoom: number;
  // Which GIBS product resolved (for the verbatim attribution; both are
  // "NASA GIBS true-colour" in copy, this is diagnostic only).
  product: "VIIRS" | "MODIS";
}
export type BasemapResult = BasemapLayer | { ok: false };

// ---- v1.3 animated rain playback frames (RainViewer radar.past ONLY) -------
//
// One entry per OBSERVED past frame. radar.nowcast is never read here (§3d
// rule 1). Ordered oldest -> newest exactly as the manifest lists radar.past.
export interface RainFrame {
  tileUrl: string;
  // ISO 8601 UTC of that observed frame.
  frameUtc: string;
}
export interface RainFramesResult {
  ok: true;
  frames: RainFrame[];
}
export type RainPlaybackResult = RainFramesResult | RealtimeFailure;

// Fixed Luzon bbox: lon 120..122, lat 14..18. No user input ever.
const LUZON_BBOX = "120,14,122,18";

function attemptStamp(): string {
  return new Date().toISOString().slice(0, 16).replace("T", " ");
}

async function getJSON(url: string, signal?: AbortSignal): Promise<any> {
  const r = await fetch(url, { signal, mode: "cors" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function getText(url: string, signal?: AbortSignal): Promise<string> {
  const r = await fetch(url, { signal, mode: "cors" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.text();
}

function withTimeout(ms: number): { signal: AbortSignal; done: () => void } {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), ms);
  return { signal: ctrl.signal, done: () => clearTimeout(id) };
}

// Defense-in-depth (OWASP ASI06/ASI08): any URL derived from a remote manifest
// (the RainViewer host field, GFM STAC asset hrefs) must resolve to an
// expected public host before we fetch it or hand it to MapLibre. The shipped
// CSP already blocks off-list origins at the browser; this rejects a poisoned
// manifest one layer earlier so it degrades to the honest-empty state instead
// of a broken tile. The allow-list mirrors the site CSP connect-src/img-src.
function assertAllowedUrl(url: string): string {
  // Strip XYZ template tokens so the URL parses cleanly for host extraction.
  const u = new URL(url.replace(/\{-?[a-z]\}/gi, "0"));
  if (u.protocol !== "https:") throw new Error("non-https url");
  const h = u.hostname;
  const ok =
    h === "rainviewer.com" ||
    h.endsWith(".rainviewer.com") ||
    h === "gibs.earthdata.nasa.gov" ||
    h === "stac.eodc.eu" ||
    h === "titiler.services.eodc.eu";
  if (!ok) throw new Error(`disallowed host: ${h}`);
  return url;
}

// ---- 1. RainViewer ground-radar rain (Tier 1) -----------------------------
//
// Uses ONLY radar.past (observation). radar.nowcast is forecast/extrapolation
// and is gated out by the locked posture -- never read here.
export async function fetchRainViewer(): Promise<RealtimeResult> {
  const t = withTimeout(8000);
  try {
    const j = await getJSON(
      "https://api.rainviewer.com/public/weather-maps.json",
      t.signal,
    );
    const host: string = j?.host;
    const past: any[] = j?.radar?.past ?? [];
    if (!host || past.length === 0) throw new Error("no radar.past frame");
    const newest = past[past.length - 1];
    const pathSeg: string = newest?.path;
    const epoch: number = Number(newest?.time);
    if (!pathSeg || !Number.isFinite(epoch)) throw new Error("bad frame");
    // tilecache XYZ template: {host}{path}/{size}/{z}/{x}/{y}/{color}/{opts}.png
    // assertAllowedUrl: host comes from the remote manifest -- validate it.
    const tileUrl = assertAllowedUrl(
      `${host}${pathSeg}/256/{z}/{x}/{y}/2/1_1.png`,
    );
    return {
      ok: true,
      tileUrl,
      acquiredUtc: new Date(epoch * 1000).toISOString(),
      sourceLatencyClass: "nowcast",
    };
  } catch {
    return { ok: false, attemptUtc: attemptStamp() };
  } finally {
    t.done();
  }
}

// ---- 2. Copernicus GFM faster-observed SAR (Tier 2) -----------------------
//
// STAC search, fixed Luzon bbox, newest item, then its titiler tilejson asset.
export async function fetchGFM(): Promise<RealtimeResult> {
  const t = withTimeout(10000);
  try {
    const search =
      "https://stac.eodc.eu/api/v1/search?collections=GFM" +
      `&bbox=${LUZON_BBOX}&sortby=-properties.datetime&limit=1`;
    const j = await getJSON(search, t.signal);
    const item = j?.features?.[0];
    if (!item) throw new Error("no GFM item");
    const dt: string =
      item?.properties?.datetime ??
      item?.properties?.["start_datetime"] ??
      "";
    if (!dt) throw new Error("no datetime");

    // Prefer an explicit tilejson asset; else derive one from a COG asset via
    // the public EODC titiler. Both endpoints are CORS-clean (research §3).
    const assets = item.assets ?? {};
    let tileUrl = "";
    for (const k of Object.keys(assets)) {
      const a = assets[k];
      const type: string = a?.type ?? "";
      if (type.includes("tilejson") || /tilejson/i.test(a?.href ?? "")) {
        // a.href + tj.tiles[0] both come from the remote STAC manifest.
        const tj = await getJSON(assertAllowedUrl(a.href), t.signal);
        const arr: string[] = tj?.tiles ?? [];
        if (arr.length) {
          tileUrl = assertAllowedUrl(arr[0]);
          break;
        }
      }
    }
    if (!tileUrl) {
      // Derive a titiler XYZ from a COG flood-extent asset.
      const cogKey = Object.keys(assets).find((k) =>
        /flood|extent|ensemble|dlr_flood/i.test(k),
      );
      const cog = cogKey ? assets[cogKey]?.href : null;
      if (!cog) throw new Error("no renderable GFM asset");
      tileUrl = assertAllowedUrl(
        "https://titiler.services.eodc.eu/cog/tiles/{z}/{x}/{y}.png" +
          `?url=${encodeURIComponent(cog)}`,
      );
    }
    return {
      ok: true,
      tileUrl,
      acquiredUtc: new Date(dt).toISOString(),
      sourceLatencyClass: "near-real-time",
    };
  } catch {
    return { ok: false, attemptUtc: attemptStamp() };
  } finally {
    t.done();
  }
}

// ---- 3. NASA GIBS VIIRS NRT optical flood (Tier 3, default OFF) ------------
//
// Resolve the latest VIIRS_Combined_Flood_1-Day date from the WMTS
// capabilities, then build the WMTS XYZ template.
const VIIRS_LAYER = "VIIRS_Combined_Flood_1-Day";

export async function fetchVIIRS(): Promise<RealtimeResult> {
  const t = withTimeout(10000);
  try {
    const xml = await getText(
      "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml",
      t.signal,
    );
    // Find the VIIRS_Combined_Flood_1-Day layer block, then its newest Default
    // / latest date. The capabilities expose <ows:Identifier> then a
    // <Dimension> with <Default> and a <Value> list.
    const li = xml.indexOf(`<ows:Identifier>${VIIRS_LAYER}</ows:Identifier>`);
    if (li < 0) throw new Error("VIIRS layer not in capabilities");
    const block = xml.slice(li, li + 4000);
    let date = "";
    const def = block.match(/<Default>([^<]+)<\/Default>/);
    if (def) date = def[1].trim();
    if (!date) {
      const vals = [...block.matchAll(/<Value>([^<]+)<\/Value>/g)].map((m) =>
        m[1].trim(),
      );
      if (vals.length) date = vals[vals.length - 1];
    }
    if (!/^\d{4}-\d{2}-\d{2}/.test(date)) throw new Error("no VIIRS date");
    const day = date.slice(0, 10);
    const tileUrl = assertAllowedUrl(
      "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/" +
        `${VIIRS_LAYER}/default/${day}/` +
        "GoogleMapsCompatible_Level8/{z}/{y}/{x}.png",
    );
    return {
      ok: true,
      tileUrl,
      acquiredUtc: `${day}T00:00:00Z`,
      sourceLatencyClass: "near-real-time",
    };
  } catch {
    return { ok: false, attemptUtc: attemptStamp() };
  } finally {
    t.done();
  }
}

// ---- 4. NASA GIBS true-colour satellite basemap (v1.3, OFF by default) -----
//
// The cinematic backdrop. Resolve the mosaic date from the EPSG:3857 WMTS
// capabilities, NOT the client clock and NOT the build time. F1 fail-safe:
// any failure -- network, no layer block, an unparseable date -- returns
// { ok: false } so the caller stays on plain OSM and never draws an undated
// photographic Earth. VIIRS is tried first, MODIS Terra is the documented
// fallback (spec §1). Both are GoogleMapsCompatible_Level9 -> maxzoom 9.
const TRUECOLOR_LAYERS: { id: string; product: "VIIRS" | "MODIS" }[] = [
  { id: "VIIRS_SNPP_CorrectedReflectance_TrueColor", product: "VIIRS" },
  { id: "MODIS_Terra_CorrectedReflectance_TrueColor", product: "MODIS" },
];

// The capabilities encode the date Dimension's <Default> as the newest single
// date (verified: "2026-05-17"); the <Value> entries are start/end/P1D ranges.
// Take <Default> first, else the end date of the last <Value> range. Reject
// anything that is not a strict YYYY-MM-DD -- "today"/relative/empty must fail
// the basemap, never relabel it.
function resolveTrueColorDate(block: string): string | null {
  const strict = /^\d{4}-\d{2}-\d{2}$/;
  const def = block.match(/<Default>([^<]+)<\/Default>/);
  if (def) {
    const d = def[1].trim();
    if (strict.test(d)) return d;
  }
  const vals = [...block.matchAll(/<Value>([^<]+)<\/Value>/g)].map((m) =>
    m[1].trim(),
  );
  if (vals.length) {
    // last range like "2026-04-30/2026-05-17/P1D" -> the end date
    const parts = vals[vals.length - 1].split("/");
    const end = (parts.length >= 2 ? parts[1] : parts[0])?.trim();
    if (end && strict.test(end)) return end;
  }
  return null;
}

export async function fetchGibsTrueColor(): Promise<BasemapResult> {
  const t = withTimeout(10000);
  try {
    const xml = await getText(
      "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml",
      t.signal,
    );
    for (const { id, product } of TRUECOLOR_LAYERS) {
      const li = xml.indexOf(`<ows:Identifier>${id}</ows:Identifier>`);
      if (li < 0) continue;
      const block = xml.slice(li, li + 4000);
      const date = resolveTrueColorDate(block);
      if (!date) continue;
      // GIBS REST WMTS XYZ template, GoogleMapsCompatible_Level9, JPEG.
      const tileUrl = assertAllowedUrl(
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/" +
          `${id}/default/${date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`,
      );
      return {
        ok: true,
        tileUrl,
        basemapDateUtc: date,
        maxZoom: 9,
        product,
      };
    }
    // F1: no resolvable date for either product -> do NOT render true-colour.
    return { ok: false };
  } catch {
    return { ok: false };
  } finally {
    t.done();
  }
}

// ---- 5. RainViewer ALL observed past frames (v1.3 animated playback) -------
//
// Returns every radar.past frame oldest -> newest for the visitor-initiated
// loop. radar.nowcast is NEVER read here (§3d rule 1): forecast/extrapolation
// is gated out of the animation entirely. Honest-empty on any failure -- the
// caller falls back to the v1.2 single-frame caption, never a blank loop.
export async function fetchRainViewerFrames(): Promise<RainPlaybackResult> {
  const t = withTimeout(8000);
  try {
    const j = await getJSON(
      "https://api.rainviewer.com/public/weather-maps.json",
      t.signal,
    );
    const host: string = j?.host;
    const past: any[] = j?.radar?.past ?? [];
    if (!host || past.length === 0) throw new Error("no radar.past frames");
    const frames: RainFrame[] = [];
    for (const f of past) {
      const pathSeg: string = f?.path;
      const epoch: number = Number(f?.time);
      if (!pathSeg || !Number.isFinite(epoch)) continue;
      frames.push({
        tileUrl: assertAllowedUrl(
          `${host}${pathSeg}/256/{z}/{x}/{y}/2/1_1.png`,
        ),
        frameUtc: new Date(epoch * 1000).toISOString(),
      });
    }
    if (frames.length === 0) throw new Error("no usable radar.past frames");
    return { ok: true, frames };
  } catch {
    return { ok: false, attemptUtc: attemptStamp() };
  } finally {
    t.done();
  }
}
