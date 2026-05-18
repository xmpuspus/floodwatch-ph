// Area / route flood-evidence lookup, 100% client-side.
//
// PRIVACY (RA 10173): the user's typed query is matched against the bundled
// static gazetteer (imported at build time, see ../data/gazetteer.json) with
// in-browser string matching. The query string is NEVER sent over the network,
// never logged, never republished. The only network reads are the SAME-ORIGIN
// static evidence GeoJSON files the site already publishes (/data/*.geojson),
// loaded once and tested in-browser with @turf point-in-polygon / distance.
// There is no geocoder and no per-query request. If you add a network call for
// the query here you break the site's audited "no geocoders" privacy posture.
//
// Available @turf packages (verified in site/package.json, do not add deps):
//   @turf/boolean-point-in-polygon, @turf/distance, @turf/centroid, @turf/area
// No @turf/buffer / @turf/nearest-point-on-line; the corridor proximity test
// is implemented here with @turf/distance against polygon representative points
// and sampled corridor vertices.

import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import distance from "@turf/distance";
import gazetteer from "../data/gazetteer.json";
import { fmtPHT } from "./freshnessClock";

export type GazEntry = {
  name: string;
  kind: string;
  province: string;
  lng: number;
  lat: number;
  aliases?: string[];
};

export const GAZ: GazEntry[] = (gazetteer as any).places as GazEntry[];
export const GAZ_META = (gazetteer as any)._meta as Record<string, string>;

// Greater Metro Manila + SLEX/NLEX corridor working bbox (superset of the
// flood/road AOIs). Outside this -> honest out-of-scope, not a wrong answer.
export const SCOPE_BBOX = { w: 119.7, s: 13.7, e: 121.9, n: 15.7 };

export function inScope(lng: number, lat: number): boolean {
  return (
    lng >= SCOPE_BBOX.w &&
    lng <= SCOPE_BBOX.e &&
    lat >= SCOPE_BBOX.s &&
    lat <= SCOPE_BBOX.n
  );
}

// ---- fuzzy place match (in-browser, no network) ---------------------------

function norm(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // strip diacritics (ñ -> n, é -> e)
    .replace(/[^a-z0-9 ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// Tiny bounded Levenshtein for one-token typo tolerance.
function editDistance(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  if (Math.abs(m - n) > 2) return 3;
  const prev = new Array(n + 1);
  const cur = new Array(n + 1);
  for (let j = 0; j <= n; j++) prev[j] = j;
  for (let i = 1; i <= m; i++) {
    cur[0] = i;
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
    }
    for (let j = 0; j <= n; j++) prev[j] = cur[j];
  }
  return prev[n];
}

export type Match = { entry: GazEntry; score: number };

// Returns ranked candidate matches. Higher score = better. Entirely local.
export function searchGazetteer(query: string, limit = 6): Match[] {
  const q = norm(query);
  if (!q) return [];
  const out: Match[] = [];
  for (const entry of GAZ) {
    const names = [entry.name, ...(entry.aliases ?? [])].map(norm);
    let best = 0;
    for (const cand of names) {
      if (cand === q) {
        best = Math.max(best, 100);
        continue;
      }
      if (cand.startsWith(q) || q.startsWith(cand)) {
        best = Math.max(best, 80 - Math.abs(cand.length - q.length));
        continue;
      }
      if (cand.includes(q) || q.includes(cand)) {
        best = Math.max(best, 60);
        continue;
      }
      // token overlap
      const qt = new Set(q.split(" "));
      const ct = new Set(cand.split(" "));
      let shared = 0;
      qt.forEach((t) => {
        if (ct.has(t) && t.length > 2) shared++;
      });
      if (shared > 0) best = Math.max(best, 40 + shared * 8);
      // single-token fuzzy (one typo)
      if (q.length >= 4 && cand.length >= 4) {
        const d = editDistance(q, cand);
        if (d <= 2) best = Math.max(best, 50 - d * 10);
      }
    }
    if (best > 0) out.push({ entry, score: best });
  }
  out.sort((a, b) => b.score - a.score || a.entry.name.localeCompare(b.entry.name));
  return out.slice(0, limit);
}

// ---- evidence geometry helpers --------------------------------------------

type Pt = [number, number]; // [lng, lat]

// Representative point of a polygon ring (centroid of outer ring vertices),
// enough for a coarse proximity test without @turf/centroid on every feature.
function ringRep(coords: number[][]): Pt {
  let sx = 0;
  let sy = 0;
  let k = 0;
  for (const c of coords) {
    sx += c[0];
    sy += c[1];
    k++;
  }
  return k ? [sx / k, sy / k] : [0, 0];
}

function polyRings(geom: any): number[][][] {
  if (!geom) return [];
  if (geom.type === "Polygon") return geom.coordinates as number[][][];
  if (geom.type === "MultiPolygon")
    return (geom.coordinates as number[][][][]).flat();
  if (geom.type === "GeometryCollection")
    return (geom.geometries || []).flatMap((g: any) => polyRings(g));
  return [];
}

function lineSegs(geom: any): number[][][] {
  if (!geom) return [];
  if (geom.type === "LineString") return [geom.coordinates as number[][]];
  if (geom.type === "MultiLineString") return geom.coordinates as number[][][];
  if (geom.type === "GeometryCollection")
    return (geom.geometries || []).flatMap((g: any) => lineSegs(g));
  return [];
}

// Does point fall inside any polygon of this feature?
function pointInFeature(pt: Pt, feature: any): boolean {
  const g = feature?.geometry;
  if (!g) return false;
  try {
    if (g.type === "Polygon" || g.type === "MultiPolygon")
      return booleanPointInPolygon(pt, g as any);
    if (g.type === "GeometryCollection") {
      for (const sub of g.geometries || []) {
        if (
          (sub.type === "Polygon" || sub.type === "MultiPolygon") &&
          booleanPointInPolygon(pt, sub as any)
        )
          return true;
      }
    }
  } catch {
    return false;
  }
  return false;
}

// Min distance (km) from a point to any polygon representative point; coarse,
// used only to say "near" vs "intersects", never as a measurement.
function nearestPolyKm(pt: Pt, features: any[]): number {
  let min = Infinity;
  for (const f of features) {
    for (const ring of polyRings(f.geometry)) {
      const rep = ringRep(ring);
      const d = distance(pt, rep, { units: "kilometers" });
      if (d < min) min = d;
    }
  }
  return min;
}

// Nearest grid sample point (recurrence / rainfall layers are Point features).
function nearestGridPoint(
  pt: Pt,
  features: any[],
): { props: any; km: number } | null {
  let best: { props: any; km: number } | null = null;
  for (const f of features) {
    const g = f?.geometry;
    if (!g || g.type !== "Point") continue;
    const c = g.coordinates as Pt;
    const d = distance(pt, c, { units: "kilometers" });
    if (!best || d < best.km) best = { props: f.properties, km: d };
  }
  return best;
}

// Build a corridor as evenly sampled points between two endpoints, then test
// each (point-in-polygon + nearest-grid). Buffer half-width in metres.
export function corridorSamplePoints(
  a: Pt,
  b: Pt,
  stepMeters = 350,
): Pt[] {
  const totalKm = distance(a, b, { units: "kilometers" });
  const n = Math.max(2, Math.min(120, Math.ceil((totalKm * 1000) / stepMeters)));
  const pts: Pt[] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    pts.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
  }
  return pts;
}

// ---- evidence assembly ----------------------------------------------------

export const CORRIDOR_BUFFER_M = 400; // documented half-width, see lookup page

export type LayerResult = {
  state: "intersects" | "near" | "clear" | "unavailable" | "withheld";
  asOf: string | null;
  detail: string;
};

export type EvidenceBundle = {
  recurrence: LayerResult;
  gfd: LayerResult;
  latest: LayerResult;
  rainfall: LayerResult;
  roads: LayerResult & { segments: string[] };
};

// R2: state the recurrence-vs-record gap as ONE conservative sentence per
// result, instead of leaving the user to infer it across two of five rows.
// Derived only from the recurrence (model) and gfd (historical record)
// layers already computed. Conservative civic-tech-ph language: it never
// says an area will or will not flood, never an accusation; the strongest
// form is "warrants verification".
export function synthesizeGap(ev: EvidenceBundle): string {
  const modeledProne =
    ev.recurrence.state === "intersects" || ev.recurrence.state === "near";
  const recordThin =
    ev.gfd.state === "near" || ev.gfd.state === "clear";
  const recordHas = ev.gfd.state === "intersects";

  if (ev.recurrence.state === "unavailable" || ev.gfd.state === "unavailable") {
    return (
      "The flood-prediction model or the past flood records are unavailable for " +
      "this place, so the gap between the two cannot be stated here. The dated " +
      "evidence rows below still apply."
    );
  }
  if (modeledProne && recordThin) {
    return (
      "The flood-prediction model says this place floods often, while the past " +
      "flood records (2002-2017) are thin or empty here: this is the " +
      "predicted-to-flood-but-barely-on-record gap. A thin record is not proof " +
      "of safety; check it against local records."
    );
  }
  if (modeledProne && recordHas) {
    return (
      "The flood-prediction model says this place floods often, and the past " +
      "flood records also show flooding here, so the two agree. Predicted to " +
      "flood and on record, not a gap."
    );
  }
  if (!modeledProne && recordHas) {
    return (
      "The past flood records show flooding here, while the nearest model " +
      "sample is below the level the model calls flood-prone. On record but " +
      "not predicted to flood at this sample; check against local records."
    );
  }
  return (
    "Neither the flood-prediction model nor the past flood records flag this " +
    "exact place as flood-prone. A thin record is not proof of safety; the " +
    "dated evidence rows below describe what was observed."
  );
}

// Same-origin static file load, identical to the site's existing MapView
// pattern. This is the ONLY network read and it carries no query data.
async function loadJSON(url: string): Promise<any | null> {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

let _cache: Record<string, any> | null = null;
async function loadAll(): Promise<Record<string, any>> {
  if (_cache) return _cache;
  const [recurrence, hazardGap, latest, rainfall, roads] = await Promise.all([
    loadJSON("/data/recurrence_prone.geojson"),
    loadJSON("/data/hazard_gap.geojson"),
    loadJSON("/data/flood_latest.geojson"),
    loadJSON("/data/current_risk.geojson"),
    loadJSON("/data/road_flood_exposure.geojson"),
  ]);
  _cache = { recurrence, hazardGap, latest, rainfall, roads };
  return _cache;
}

function classifyDistance(km: number): "intersects" | "near" | "clear" {
  if (km <= 0.05) return "intersects";
  if (km <= 1.0) return "near";
  return "clear";
}

// One point of interest -> the five evidence layers.
async function evidenceForPoints(pts: Pt[]): Promise<EvidenceBundle> {
  const d = await loadAll();

  // 1. Track B modeled recurrence-prone (300 m grid, 2017 embedding).
  let recurrence: LayerResult;
  if (!d.recurrence?.features) {
    recurrence = { state: "unavailable", asOf: "2017 model data", detail: "Flood-prediction layer unavailable." };
  } else {
    let bestScore = -1;
    let bestKm = Infinity;
    for (const p of pts) {
      const ng = nearestGridPoint(p, d.recurrence.features);
      if (ng && ng.km < bestKm) {
        bestKm = ng.km;
        bestScore = Number(ng.props?.score ?? -1);
      }
      if (ng && Number(ng.props?.score ?? -1) > bestScore) bestScore = Number(ng.props?.score ?? -1);
    }
    if (bestScore < 0 || bestKm > 2.5) {
      recurrence = {
        state: "clear",
        asOf: "AlphaEarth 2017",
        detail: "No flood-prediction sample point within about 2.5 km of this place.",
      };
    } else {
      const cls = bestScore >= 0.6 ? "modeled flood-prone" : bestScore >= 0.4 ? "modeled marginal" : "modeled low";
      recurrence = {
        state: bestScore >= 0.6 ? "intersects" : "near",
        asOf: "2017 model data (Google AlphaEarth)",
        detail: `Nearest Track B sample point (~${bestKm.toFixed(2)} km away): calibrated recurrence score ${bestScore.toFixed(2)}, ${cls}. 300 m grid; a high score is not a prediction.`,
      };
    }
  }

  // 2. GFD historical observed record (province observed_events from hazard_gap).
  let gfd: LayerResult;
  if (!d.hazardGap?.features) {
    gfd = { state: "unavailable", asOf: "GFD 2002-2017", detail: "Historical record layer unavailable." };
  } else {
    let hit: any = null;
    for (const f of d.hazardGap.features) {
      if (pts.some((p) => pointInFeature(p, f))) {
        hit = f;
        break;
      }
    }
    if (!hit) {
      gfd = {
        state: "clear",
        asOf: "GFD 2002-2017",
        detail: "Location is outside the v1.0 province reference region for the historical record (Carina + Koppu AOI union).",
      };
    } else {
      const ev = Number(hit.properties?.observed_events ?? 0);
      const prov = hit.properties?.province ?? hit.properties?.city ?? "this province";
      gfd = {
        state: ev > 0 ? "intersects" : "near",
        asOf: "Global Flood Database, 2002-2017",
        detail: `${prov}: ${ev} historical observed flood event${ev === 1 ? "" : "s"} in the Global Flood Database (2002-2017). GFD ends 2017; events since (Odette 2021, Paeng 2022, Carina 2024) are not in this count. A thin record is not proof of safety.`,
      };
    }
  }

  // 3. Latest observed Sentinel-1 pass, carry scan_status honestly.
  let latest: LayerResult;
  const lmeta = d.latest?._meta;
  if (!d.latest || !lmeta) {
    latest = { state: "unavailable", asOf: null, detail: "Latest Sentinel-1 layer unavailable." };
  } else {
    const status = lmeta.scan_status;
    const asOf = lmeta.as_of ?? null;
    if (status !== "ok") {
      const reason =
        status === "no_usable_pass"
          ? `no usable Sentinel-1 pass in the last ${lmeta.lookback_days ?? "N"} days`
          : status === "degenerate_threshold"
            ? `the most recent pass (${asOf}) had no reliable water signal`
            : `the most recent pass (${asOf}) was inconclusive`;
      latest = {
        state: "withheld",
        asOf,
        detail: `Most recent satellite pass was not usable: ${reason}. This is NOT "clear", no observation was possible. Sentinel-1 has a ~6-day revisit with ~24 h product latency.`,
      };
    } else {
      const inPoly = pts.some((p) =>
        (d.latest.features || []).some((f: any) => pointInFeature(p, f)),
      );
      const km = inPoly ? 0 : nearestPolyKm(pts[0], d.latest.features || []);
      const cls = inPoly ? "intersects" : classifyDistance(km);
      latest = {
        state: cls === "clear" ? "clear" : cls,
        asOf,
        detail: inPoly
          ? `This place falls inside the flooded area Sentinel-1 radar saw on the ${asOf} satellite pass. Observed, NOT live, NOT a forecast (about a 6-day revisit, roughly 24 h product latency).`
          : cls === "near"
            ? `Nearest observed Sentinel-1 open-water polygon on the ${asOf} pass is ~${km.toFixed(1)} km away. Observed, NOT live.`
            : `No observed Sentinel-1 open water near this location on the most recent usable pass (${asOf}). This describes one dated pass only, not "no flooding".`,
      };
    }
  }

  // 4. GPM rainfall context (nearest prone-grid sample, not a forecast).
  let rainfall: LayerResult;
  const rmeta = d.rainfall?._meta;
  if (!d.rainfall?.features || !rmeta) {
    rainfall = { state: "unavailable", asOf: rmeta?.as_of ?? null, detail: "Rainfall context layer unavailable." };
  } else if (rmeta.scan_status && rmeta.scan_status !== "ok") {
    rainfall = {
      state: "withheld",
      asOf: rmeta.as_of ?? null,
      detail: `GPM IMERG rainfall context not available for the most recent window (${rmeta.scan_status}).`,
    };
  } else {
    let best: { props: any; km: number } | null = null;
    for (const p of pts) {
      const ng = nearestGridPoint(p, d.rainfall.features);
      if (ng && (!best || ng.km < best.km)) best = ng;
    }
    if (!best || best.km > 8) {
      rainfall = {
        state: "clear",
        asOf: rmeta.as_of ?? null,
        detail: "No nearby rainfall sample point for this place.",
      };
    } else {
      const r24 = Number(best.props?.rain_mm_24h ?? 0);
      const r72 = Number(best.props?.rain_mm_72h ?? 0);
      const flag = String(best.props?.context_flag ?? "none");
      rainfall = {
        state: flag === "none" ? "near" : "intersects",
        asOf: rmeta.as_of ?? null,
        detail: `Nearest prone-area GPM IMERG sample (~${best.km.toFixed(1)} km): ${r24.toFixed(0)} mm/24h, ${r72.toFixed(0)} mm/72h, context band "${flag}". Satellite rainfall accumulation as of ${fmtPHT(rmeta.as_of)}, already-fallen rain, not a gauge reading and not a forecast.`,
      };
    }
  }

  // 5. Nearby monitored expressway segments flagged in the latest pass.
  let roads: LayerResult & { segments: string[] };
  const rdMeta = d.roads?._meta;
  if (!d.roads?.features || !rdMeta) {
    roads = { state: "unavailable", asOf: rdMeta?.as_of ?? null, detail: "Expressway exposure layer unavailable.", segments: [] };
  } else if (rdMeta.scan_status && rdMeta.scan_status !== "ok") {
    roads = {
      state: "withheld",
      asOf: rdMeta.as_of ?? null,
      detail: `No usable Sentinel-1 pass, expressway exposure could not be computed (${rdMeta.scan_status}).`,
      segments: [],
    };
  } else {
    const named = new Map<string, string>();
    for (const f of d.roads.features as any[]) {
      const ex = f.properties?.exposure;
      if (ex !== "flooded" && ex !== "near") continue;
      // proximity: any segment vertex within the corridor/area buffer
      const segs = lineSegs(f.geometry);
      let hit = false;
      for (const seg of segs) {
        for (const v of seg) {
          for (const p of pts) {
            if (distance(p, v as Pt, { units: "kilometers" }) <= CORRIDOR_BUFFER_M / 1000 + 0.6) {
              hit = true;
              break;
            }
          }
          if (hit) break;
        }
        if (hit) break;
      }
      if (hit) {
        const nm = f.properties?.road_name || f.properties?.ref || "unnamed road";
        named.set(`${nm} (${ex})`, ex);
      }
    }
    const list = Array.from(named.keys()).slice(0, 12);
    if (list.length === 0) {
      roads = {
        state: "clear",
        asOf: rdMeta.as_of ?? null,
        detail: `No monitored expressway segment intersects the most recent observed extent within the buffer of this location (as of ${rdMeta.as_of}).`,
        segments: [],
      };
    } else {
      roads = {
        state: "intersects",
        asOf: rdMeta.as_of ?? null,
        detail: `Monitored expressway/major-road segments flagged flooded or near on the ${rdMeta.as_of} observed pass within ~${CORRIDOR_BUFFER_M} m + 600 m of this location:`,
        segments: list,
      };
    }
  }

  return { recurrence, gfd, latest, rainfall, roads };
}

export async function lookupArea(lng: number, lat: number): Promise<EvidenceBundle> {
  return evidenceForPoints([[lng, lat]]);
}

export async function lookupCorridor(
  a: Pt,
  b: Pt,
): Promise<EvidenceBundle> {
  return evidenceForPoints(corridorSamplePoints(a, b, 350));
}
