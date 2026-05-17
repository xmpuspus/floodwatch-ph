// Freshness clock -- per-layer ticking age + the global ticker.
//
// Pure functions plus a tiny client init. All user-visible strings are the
// Agent-F v1.2 copy spec section 4 VERBATIM (no "now-ish", no "live", no
// present-tense softener; the ticking relative age carries recency). The
// colour rule is section 4c: neutral grey by default, an amber dot ONLY when a
// layer is staler than its own cadence, never red, never pulsing.
//
// Times are UTC, format YYYY-MM-DD HH:MM unless a caption says otherwise.
// A missing acquisition time is never defaulted to "just now"; it renders the
// section-4d "acquisition time unavailable" string.

export type LatencyClassLabel =
  | "nowcast (~10-min source)"
  | "near-real-time (delivered within ~8 h of the pass)"
  | "daily build of the latest pass (~6-day revisit, ~24 h product latency)"
  | "near-real-time (same-day, cloud-permitting)"
  | "daily (rainfall window, processed once a day)";

// Each layer declares its own expected cadence so the amber dot can fire ONLY
// when the layer is staler than its OWN cadence (section 4c thresholds).
export type LayerCadenceKey = "sentinel1" | "rainviewer" | "viirs";

const STALE_THRESHOLD_MS: Record<LayerCadenceKey, number> = {
  // Sentinel-1 > 12 days
  sentinel1: 12 * 24 * 60 * 60 * 1000,
  // RainViewer client fetch > 30 min
  rainviewer: 30 * 60 * 1000,
  // VIIRS > 48 h
  viirs: 48 * 60 * 60 * 1000,
};

// Format an acquisition timestamp for display in Philippine time (PHT,
// UTC+8, no DST), explicitly labelled so it is never ambiguous. The stored
// source value stays UTC ISO everywhere; only the displayed string is
// localised. An ISO date-only value stays a calendar date (a pass date is
// tz-neutral; inventing a PHT clock time on a date-only value would be fake
// precision). The label is mandatory: an unlabelled local time would
// regress the "dated, unambiguous" honesty rule.
export function fmtPHT(iso: string | null | undefined): string {
  if (!iso) return "acquisition time unavailable";
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const ph = new Date(d.getTime() + 8 * 60 * 60 * 1000);
  return ph.toISOString().slice(0, 16).replace("T", " ") + " PHT";
}

// Back-compat alias: existing call sites used fmtAcqUTC; it now yields
// PHT-labelled local time via fmtPHT (the " UTC" literal that used to
// follow it in templates has been removed at each call site).
export const fmtAcqUTC = fmtPHT;

// Section 4a ticking-age strings (exact). `nowMs` is injectable for tests.
export function tickingAge(
  acquiredIso: string | null | undefined,
  nowMs: number = Date.now(),
): string {
  if (!acquiredIso) return "acquisition time unavailable";
  const t = new Date(acquiredIso).getTime();
  if (isNaN(t)) return "acquisition time unavailable";
  const diff = Math.max(0, nowMs - t);
  const min = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (diff < 60 * 60 * 1000) {
    return `updated ${min} min ago`;
  }
  if (diff < 24 * 60 * 60 * 1000) {
    const m = min - hours * 60;
    return `updated ${hours} h ${m} min ago`;
  }
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    return `updated ${days} days ago (last Sentinel-1 pass)`;
  }
  return `last pass ${days} days ago`;
}

// Section 4c: an amber dot appears ONLY when a layer is staler than its own
// expected cadence. Never red. The >= 7 d ticking string also carries an
// amber dot per 4a; both routes resolve here.
export function isStale(
  cadence: LayerCadenceKey,
  acquiredIso: string | null | undefined,
  nowMs: number = Date.now(),
): boolean {
  if (!acquiredIso) return false;
  const t = new Date(acquiredIso).getTime();
  if (isNaN(t)) return false;
  return nowMs - t > STALE_THRESHOLD_MS[cadence];
}

// Section 4a per-layer caption template (verbatim shape):
//   {LAYER NAME}
//   {ticking age} · acquired {acqDateUTC} UTC
//   source: {source} · {latency class label}
export function layerCaption(args: {
  layerName: string;
  acquiredIso: string | null | undefined;
  source: string;
  latencyClass: LatencyClassLabel;
  nowMs?: number;
}): { line1: string; line2: string; line3: string } {
  const now = args.nowMs ?? Date.now();
  const acq = fmtAcqUTC(args.acquiredIso);
  return {
    line1: args.layerName,
    line2: `${tickingAge(args.acquiredIso, now)} · acquired ${acq}`,
    line3: `source: ${args.source} · ${args.latencyClass}`,
  };
}

// Section 4b global ticker template (verbatim). `freshLayer` is the layer with
// the most recent acquisition time; `rebuiltUtc` is the static build time.
export function globalTicker(args: {
  freshLayer: string | null;
  freshAcquiredIso: string | null;
  rebuiltUtc: string;
  nowMs?: number;
}): string {
  const now = args.nowMs ?? Date.now();
  if (!args.freshLayer || !args.freshAcquiredIso) {
    return (
      `Freshest layer: acquisition time unavailable. ` +
      `Site rebuilt ${args.rebuiltUtc}. Layers refresh independently — see each ` +
      `layer's own clock.`
    );
  }
  const age = tickingAge(args.freshAcquiredIso, now).replace(/^updated /, "").replace(/^last pass /, "");
  const acq = fmtAcqUTC(args.freshAcquiredIso);
  return (
    `Freshest layer: ${args.freshLayer} — updated ${age} ago (${acq}). ` +
    `Site rebuilt ${args.rebuiltUtc}. Layers refresh independently — see each ` +
    `layer's own clock.`
  );
}

// Pick the freshest of a set of (name, iso) pairs by most-recent acquisition.
export function freshestOf(
  layers: { name: string; acquiredIso: string | null | undefined }[],
): { name: string; acquiredIso: string } | null {
  let best: { name: string; acquiredIso: string } | null = null;
  let bestT = -Infinity;
  for (const l of layers) {
    if (!l.acquiredIso) continue;
    const t = new Date(l.acquiredIso).getTime();
    if (isNaN(t)) continue;
    if (t > bestT) {
      bestT = t;
      best = { name: l.name, acquiredIso: l.acquiredIso };
    }
  }
  return best;
}

// Section 4d honest-empty strings (verbatim). Substitute the attempt time.
export function honestEmpty(
  layer: "rainviewer" | "gfm" | "viirs",
  attemptUtc: string,
): string {
  if (layer === "rainviewer") {
    return (
      `Rain radar unavailable — could not reach RainViewer (${attemptUtc} ` +
      `attempt). Other layers unaffected.`
    );
  }
  if (layer === "gfm") {
    return (
      `Faster observed SAR unavailable — could not reach the Copernicus GFM ` +
      `catalogue (${attemptUtc} attempt). Other layers unaffected.`
    );
  }
  return (
    `Supplementary optical layer unavailable — could not reach NASA GIBS ` +
    `(${attemptUtc} attempt). Other layers unaffected.`
  );
}

// Section 4d: disabled toggle text when a client layer failed (verbatim).
export const DISABLED_TOGGLE_TEXT = "unavailable — see caption";

// Section 4d: missing timestamp string (verbatim — never "just now").
export const MISSING_TIMESTAMP_TEXT = "acquisition time unavailable";

// ---- small client init: recompute the ticking captions every 30 s ---------
//
// Reuses FreshnessBanner's client-init style: pure DOM, no framework. Elements
// opt in with data-fw-clock="<cadenceKey>" and data-fw-acq="<iso>"; the init
// rewrites their .fw-clock-age / .fw-clock-dot children on a 30 s tick.

export interface ClockTarget {
  el: HTMLElement;
  cadence: LayerCadenceKey;
  acquiredIso: string | null;
}

export function startClockTicker(
  targets: ClockTarget[],
  tickerEl: HTMLElement | null,
  tickerArgs: { rebuiltUtc: string } & {
    layers: { name: string; acquiredIso: string | null }[];
  },
): () => void {
  const paint = (): void => {
    const now = Date.now();
    for (const t of targets) {
      const ageEl = t.el.querySelector<HTMLElement>(".fw-clock-age");
      const dotEl = t.el.querySelector<HTMLElement>(".fw-clock-dot");
      if (ageEl) ageEl.textContent = tickingAge(t.acquiredIso, now);
      if (dotEl) {
        const stale = isStale(t.cadence, t.acquiredIso, now);
        dotEl.style.display = stale ? "inline-block" : "none";
        dotEl.setAttribute(
          "title",
          stale ? "this layer may be behind" : "",
        );
      }
    }
    if (tickerEl) {
      const fresh = freshestOf(tickerArgs.layers);
      tickerEl.textContent = globalTicker({
        freshLayer: fresh?.name ?? null,
        freshAcquiredIso: fresh?.acquiredIso ?? null,
        rebuiltUtc: tickerArgs.rebuiltUtc,
        nowMs: now,
      });
    }
  };
  paint();
  const id = window.setInterval(paint, 30000);
  return () => window.clearInterval(id);
}
