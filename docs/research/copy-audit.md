# Copy audit — FloodWatch.PH (gates all public copy)

Status: audit-confirmed. Agent D applies these exact patches. This file is the
single source of truth for copy fixes this wave. Every patch is line-anchored
against the file as read 2026-05-16. READ-ONLY producer: no code/site file is
edited here.

Verdict summary:
- **True AlphaEarth scale = 300 m** (verified `model/fetch_embeddings.py:41`,
  `SCALE = 300`; confirmed in `recurrence_clf_v1_calibration.json` and
  `recurrence_clf_v1_metrics.json`, both already say "300 m"). Every "10 m"
  embedding claim is a **systemic stale overclaim** — fix all.
- **Metrics drift verdict: metrics.ts is CORRECT; the logs are stale.** Canonical
  source is the meta JSON (`flood_koppu_2015_meta.json` IoU 0.0542 / F1 0.0652;
  `flood_carina_2024_meta.json` peak 184.15 km²). `metrics.ts`, README, MODEL_CARD
  already match canonical (0.054 / 0.065 / 184). The `_koppu.log` (0.061/0.071)
  and `_carina.log` (206.7) are from an earlier non-canonical run — no copy
  change needed for the numbers; the fix is a **CI gate** so this can't drift.
- **`substitute_metrics.py` is wired to NOTHING** — not in `Makefile`, not in
  `ci.yml`. metrics.ts is correct only by manual luck. Recommend a CI gate.
- **Systemic "~10 MB" embeddings cache claim** — actual file is ~1 MB. README
  already says "~1 MB" (2×) but MODEL_CARD / spec / CHANGELOG / .zenodo.json /
  methodology.astro say "~10 MB". Fix all.
- **CHANGELOG.md is the worst-drift file**: "barangay" (v1.0 is province),
  "six" S1 dates (v1.0 is 4), `gap:"uncharted"` (actual `under_observed_prone`),
  "~10 MB". README/site already corrected to province/4/under_observed_prone —
  CHANGELOG/SECURITY/PIA were never updated.

---

## Patch table

| File | Line | Current text | Problem | Exact replacement text |
|---|---|---|---|---|
| MODEL_CARD.md | 56 | `...Satellite Embedding V1" (...), 10 m, 64-dim, unit-norm, annual, year **2017**.` | Overclaim — pipeline samples at 300 m, not native 10 m | `...Satellite Embedding V1" (\`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL\`), 64-dim, unit-norm, annual, year **2017**. AlphaEarth is natively 10 m; FloodWatch samples it at **300 m** (the embedding is mean-aggregated over the cell — flood recurrence is an area property; this is fast and reproducible). "Produced by Google and Google DeepMind." License: CC-BY-4.0.` |
| MODEL_CARD.md | 63 | `\| Committed cache \| ...floodwatch_embeddings_v1.npz\` (~10 MB) \|` | Stale — file is ~1 MB | `\| Committed cache \| \`model/embeddings/floodwatch_embeddings_v1.npz\` (~1 MB) \|` |
| MODEL_CARD.md | 159 | `Track B outputs are a 10-30 m sample grid, not a per-building assessment.` | Wrong — sampled/scored at 300 m | `Track B is sampled and scored on a 300 m grid, not a per-building assessment.` |
| README.md | 11 | `...a frozen Google AlphaEarth Foundations Satellite Embedding (2017, 64-dim, CC-BY-4.0)...` | OK as written (no scale stated here) — no change | (no change) |
| README.md | 89 | `It is bit-exact reproducible from the committed \`model/embeddings/floodwatch_embeddings_v1.npz\` (~1 MB, in git).` | Correct (~1 MB) — no change | (no change) |
| README.md | 20 | `...into the committed \`embeddings/floodwatch_embeddings_v1.npz\` cache (~1 MB, in git).` | Correct — no change | (no change) |
| README.md | 124 | `...at GFD's native 250 m, permanent water removed from both.` | Correct (GFD MODIS is 250 m) — no change | (no change) |
| README.md | 125 | `...a single 10 m SAR pass versus a multi-day 250 m optical product...` | CORRECT — this is Sentinel-1 SAR (~10 m), NOT the embedding. Do not change. | (no change) |
| MODEL_CARD.md | 159 (2nd clause) | `Do not interpret a positive point as a statement about a specific dwelling.` | Keep | (keep) |
| docs/research/floodwatch-spec.md | 70 | `(...), 10 m, 64-dim, unit-norm, annual` | Spec is "locked" but factually states 10 m where pipeline uses 300 m | Add a parenthetical (do not relitigate locked decisions; correct a factual error only): `(\`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL\`), natively 10 m but **sampled at 300 m** in this pipeline (see model/fetch_embeddings.py), 64-dim, unit-norm, annual` |
| site/src/pages/methodology.astro | 61 | `...Satellite Embedding V1" (...), 10 m resolution, 64-dim unit-norm vectors, annual 2017-2025, CC-BY-4.0.` | Overclaim | `...Satellite Embedding V1" (<code>GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL</code>), natively 10 m, sampled here at <strong>300 m</strong> (mean-aggregated per cell; flood recurrence is an area property), 64-dim unit-norm vectors, annual 2017-2025, CC-BY-4.0.` |
| site/src/pages/methodology.astro | 64 | `<code>model/embeddings/floodwatch_embeddings_v1.npz</code> (~10 MB).` | Stale | `<code>model/embeddings/floodwatch_embeddings_v1.npz</code> (~1 MB).` |
| site/src/pages/methodology.astro | 113 | `SAR at 10-20m resolution captures open water extents...` | CORRECT — Sentinel-1 native is ~10-20 m. Do not change. | (no change) |
| site/src/pages/recurrence.astro | 20 | `...Satellite Embedding V1" (...), 10 m resolution, 64-dimensional unit-norm vectors, annual cadence 2017-2025...` | Overclaim | `...Satellite Embedding V1" (<code>GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL</code>), natively 10 m, sampled here at <strong>300 m</strong> (mean-aggregated per cell; flood recurrence is an area property), 64-dimensional unit-norm vectors, annual cadence 2017-2025...` |
| site/src/pages/recurrence.astro | 65 | `...a FeatureCollection of Point features on a 10-30 m sample grid over the AOI.` | Wrong — 300 m grid | `...a FeatureCollection of Point features on a <strong>300 m</strong> sample grid over the AOI.` |
| site/src/pages/recurrence.astro | 74 | `Province-level aggregation is appropriate; individual-pixel claims are not.` | Keep (consistent) | (keep) |
| site/src/pages/privacy.astro | 17 | `Track B recurrence-prone sample-grid points. Points are on a 10-30 m grid, not building centroids.` | Wrong — 300 m grid | `Track B recurrence-prone sample-grid points. Points are on a <strong>300 m</strong> grid, not building centroids.` |
| docs/privacy-impact-assessment.md | 39 | `...a probability number on a 10-30 m sample grid...` | Wrong — 300 m | `...a probability number on a 300 m sample grid...` |
| docs/privacy-impact-assessment.md | 53 | `A recurrence-score point on a 10-30 m grid does not name a person.` | Wrong — 300 m | `A recurrence-score point on a 300 m grid does not name a person.` |
| CHANGELOG.md | 16-18 | `...Six real S1 acquisition dates: 2024-06-16, 06-28 (dry baseline), 07-10 (pre), 07-22, 07-30 (peak / recession), 08-03 (post).` | Stale — v1.0 ships 4 event dates; 06-16/06-28 are dry baseline, not slider frames (README/meta say "4 acquisition dates") | `Four real S1 event acquisition dates (2024-07-10, 07-22, 07-30, 08-03), with a dry pre-event baseline composite from 2024-06-16 and 06-28.` |
| CHANGELOG.md | 36-38 | `...Committed cache: \`model/embeddings/floodwatch_embeddings_v1.npz\` (~10 MB).` | Stale — ~1 MB | `...Committed cache: \`model/embeddings/floodwatch_embeddings_v1.npz\` (~1 MB).` |
| CHANGELOG.md | 42-43 | `**Barangay exposure join** (\`pipeline/exposure.py\`). WorldPop population and Microsoft GlobalML building counts aggregated to barangay level.` | Contradiction — v1.0 aggregates to province (FAO GAUL level-2); every site page says province | `**Province exposure join** (\`pipeline/exposure.py\`). WorldPop population and Microsoft GlobalML built-up area aggregated to province level (FAO GAUL level-2, ~82 Philippine provinces). City and barangay resolution is a documented v1.1 refinement.` |
| CHANGELOG.md | 46-49 | `**Hazard gap layer** (\`pipeline/hazard_gap.py\`). Barangay-level comparison of observed recurrence score (Track B) vs presence on the official UP NOAH / PAGASA / MGB hazard map. \`gap: "uncharted"\` flags barangays with observed recurrent flooding absent from the official hazard layer -- the headline civic finding.` | Triple error: barangay (→province), official-hazard comparison is v1.1 not v1.0, `gap:"uncharted"` is actually `under_observed_prone` vs the GFD historical record | `**Hazard gap layer** (\`pipeline/hazard_gap.py\`). Province-level comparison of modeled flood-proneness (Track B) vs the historical observed record (Global Flood Database). \`gap: "under_observed_prone"\` flags provinces modeled flood-prone but with few or no events in the historical observed record -- the headline civic finding. The official UP NOAH / PAGASA / MGB hazard-map cross-reference is a documented v1.1 refinement (those layers are token-gated or SPA-only).` |
| CHANGELOG.md | 50-52 | `**Astro + MapLibre site** (\`site/\`). Time-slider over the six Carina 2024 S1 acquisition dates. Click a barangay for exposed population, building count, and official hazard-map status.` | Stale — six→4, barangay→province, official-hazard status is v1.1 (UI shows "Not compared in v1.0") | `**Astro + MapLibre site** (\`site/\`). Time-slider over the four Carina 2024 S1 event acquisition dates. Click a province for exposed population, built-up area, observed historical events, and peak flood share.` |
| SECURITY.md | 26-27 | `Barangay exposure data is pre-aggregated before publication.` | Contradiction — province | `Province exposure data is pre-aggregated before publication.` |
| SECURITY.md | 44-46 | `Published flood extent and recurrence outputs are aggregated to barangay level. No per-dwelling geometry...` | Contradiction — province | `Published flood extent and recurrence outputs are aggregated to province level (FAO GAUL level-2). No per-dwelling geometry, no household identifiers, no PII property keys appear in any published GeoJSON.` |
| .zenodo.json | description | `...bit-exact reproducible from a committed ~10 MB embeddings cache...` | Stale — ~1 MB | `...bit-exact reproducible from a committed ~1 MB embeddings cache...` |
| docs/launch/linkedin-draft.md | 23 | `Live map: https://floodwatch.ph` | Pre-emptive — domain not yet registered (known external gate); live URL is the Vercel deployment | `Live map: https://floodwatch-ph-five.vercel.app` (revert to floodwatch.ph only once dot.ph registration completes) |
| docs/privacy-impact-assessment.md | 19, 34-37, 40, 54-56, 60, 66, 75, 94-95, 122 | Repeated "barangay level" / "barangay aggregate" | Systemic contradiction — v1.0 publishes province (FAO GAUL level-2). PIA must match the shipped boundary or the RA-10173 posture is misstated. | Replace "barangay level"/"barangay-level"/"barangay aggregate" → "province level (FAO GAUL level-2)"/"province-level"/"province aggregate" throughout; keep the legacy filename note (`barangay_exposure.json` retained for compatibility, contains province units). See systemic list below. |

---

## Systemic overclaim patterns (every instance — Agent D fixes ALL)

### Pattern 1 — "10 m" embedding scale (TRUE scale = 300 m)

Sampling scale is `SCALE = 300` (`model/fetch_embeddings.py:41`). The two
generated metric JSONs already say "300 m". Fix every copy instance:

- MODEL_CARD.md:56 — "10 m" in encoder row
- MODEL_CARD.md:159 — "10-30 m sample grid"
- docs/research/floodwatch-spec.md:70 — "10 m" (factual correction only; locked-decision text untouched)
- site/src/pages/methodology.astro:61 — "10 m resolution"
- site/src/pages/recurrence.astro:20 — "10 m resolution"
- site/src/pages/recurrence.astro:65 — "10-30 m sample grid"
- site/src/pages/privacy.astro:17 — "10-30 m grid"
- docs/privacy-impact-assessment.md:39 — "10-30 m sample grid"
- docs/privacy-impact-assessment.md:53 — "10-30 m grid"

NOT to change (these are Sentinel-1 SAR, genuinely ~10–20 m, correct):
- README.md:125 "single 10 m SAR pass"
- docs/launch/release-notes-v1.0.0.md:19 "single 10 m SAR pass"
- site/src/pages/methodology.astro:113 "SAR at 10-20m resolution"

### Pattern 2 — "~10 MB" embeddings cache (TRUE size ≈ 1 MB)

Actual: `model/embeddings/floodwatch_embeddings_v1.npz` = 1,059,411 bytes (~1 MB).
README already correct (~1 MB, lines 20 & 89). Fix the stale ones:

- MODEL_CARD.md:63
- docs/research/floodwatch-spec.md:84 ("~10 MB")
- CHANGELOG.md (Track B Added bullet)
- .zenodo.json (description)
- site/src/pages/methodology.astro:64

### Pattern 3 — "barangay" where v1.0 ships "province" (FAO GAUL level-2)

Site pages, README, MODEL_CARD already say province. The never-updated set:

- CHANGELOG.md:42,43,46,48,51 (Added bullets)
- SECURITY.md:27,44
- docs/privacy-impact-assessment.md: lines 19,34,35,36,37,40,54,55,56,60,66,75,94,95,122

Replace aggregation-unit "barangay" → "province (FAO GAUL level-2)". Keep the
literal filename `barangay_exposure.json` (compatibility — already noted on site).

### Pattern 4 — stale "six" / `gap:"uncharted"` / v1.0-official-hazard claims

Confined to CHANGELOG.md (lines 16-18, 46-52) and the Notes/Added section. Fix
per the patch table. Cross-check: README.md:15,126, index.astro:44 already say
"4". Final state must be uniformly "4 event acquisition dates" and
`under_observed_prone`.

---

## Privacy-page copy for the offline gazetteer (audit-confirmed crack c)

`site/vercel.json:25` CSP `connect-src` = `'self' https://*.tile.openstreetmap.org
https://*.openstreetmap.org` — there is **no geocoder endpoint**, so
`privacy.astro:67` "No geocoders" is currently **true**. Agent G's area/route
lookup MUST keep it true: a **client-side static bundled PH gazetteer** with
zero network calls for the query, in-browser point-in-polygon. Replace the
`privacy.astro` telemetry paragraph (lines 65-68) with this exact copy:

> **Telemetry, cookies, analytics, and the area lookup**
>
> No first-party cookies. No analytics scripts. No user accounts. No
> advertising. Vercel sets standard CDN cookies for cache routing; we do not
> read or use them. The site is a static build. The `vercel.json`
> Content-Security-Policy explicitly enumerates which endpoints the browser can
> reach: `'self'`, OSM tile servers for the basemap, and OSM attribution
> endpoints. No third-party geocoder, no analytics endpoints, no tracking.
>
> The "is this area flood-prone?" lookup runs **entirely in your browser**
> against a bundled offline place-name index (a static gazetteer shipped with
> the site). The text you type is matched locally and tested against the
> flood-evidence polygons with in-browser point-in-polygon. Your query is
> **never transmitted to any server, never logged, and never republished**. It
> is your own input about your own area of interest; under RA 10173 it is not
> collected or processed by FloodWatch because it never leaves your device.

Also append to the `What we don't publish` list (after privacy.astro:25):

> - Any record of an area or route a user looks up. The lookup is offline and
>   in-browser; FloodWatch receives nothing.

If Agent G's design ever requires a network call for the lookup, the "No
geocoders" / "never transmitted" copy becomes false — this is a hard gate:
the offline-gazetteer architecture and this copy must ship together.

---

## "Live"/present-tense framing fixes (audit-confirmed crack d)

The 2024 demo must never read as current. Apply these honest, as-of-dated
strings. Agent D wires the dynamic UTC timestamp from the new pipeline meta.

- **Track A freshness, exact string (banner + map intro):**
  > Most recent Sentinel-1 SAR pass shown is the demo's 2024-07/08 Carina
  > acquisitions. Sentinel-1 revisit is ~6–12 days — this is the latest
  > **observed** satellite pass for the selected window, **not a live feed and
  > not a forecast**.

- **Near-real-time mode string (when Agent D adds the latest-pass layer):**
  > Latest Sentinel-1 SAR acquisition over the AOI: {ACQ_DATE_UTC} (revisit
  > ~6–12 days; this is the most recent pass, not live).

- **Rainfall context string (GPM IMERG):**
  > Rainfall context: GPM IMERG accumulation as of {IMERG_UTC} UTC. Satellite
  > rainfall estimate, not a gauge reading and not a forecast.

- index.astro:15 currently "maps observed flood extent from real acquisition
  dates" — acceptable (already past/observed framed). Add no "live"/"current"
  wording anywhere. map.astro intro is past-tense — keep.

---

## Defensible guardrail copy block (crack e — exact strings for Agent G + D)

Agent G's lookup result surface and Agent D's freshness banner must carry this
verbatim. No "will flood" / "won't flood" / "safe" / binary anywhere.

**Lookup result header (every result, before any evidence):**
> This is **observed and modeled evidence as of dated satellite layers — not a
> forecast and not a safety instruction.** It does not say this area will or
> will not flood.

**Evidence framing (wraps the returned layers):**
> For the area you entered, FloodWatch shows: (1) observed Sentinel-1 SAR flood
> extent on its dated acquisition passes, (2) the Track B modeled
> recurrence-prone score (300 m grid, 2017 embedding), and (3) the historical
> Global Flood Database record. These are observations and a model, each
> as-of-dated. A thin record is not proof of safety; a high score is not a
> prediction.

**Mandatory redirect (every lookup result and the freshness banner):**
> Not a forecast. For live conditions, warnings, and routing during an active
> flood, use PAGASA (bagong.pagasa.dost.gov.ph), MMDA Flood Control, and your
> LGU DRRMO. FloodWatch is complementary to and never a replacement for these
> and Project NOAH / Google Flood Hub.

**Public-records disclaimer (footer of every relevant surface — already the
site's standard line; reuse verbatim):**
> Observed flood extent derived from public satellite data. Patterns may have
> legitimate explanations; figures warrant independent verification.

---

## Recommended CI gate (metrics-drift root cause)

`scripts/substitute_metrics.py` exists and is correct but is referenced by
**neither `Makefile` nor `.github/workflows/ci.yml`**. metrics.ts matches
canonical only by manual luck. Recommendation for Agent D (code change is out of
this agent's partition — flagged, not applied):

1. Add a `metrics` Makefile target: `$(PY) scripts/substitute_metrics.py`.
2. Add a CI step in the `gates` job that runs a **check mode**: re-derive every
   metric from the canonical artifacts (meta JSON, calibration JSON) and assert
   `site/src/data/metrics.ts` + the doc tokens already match — fail the build on
   any drift (the contradictory-envelope / single-source-of-truth rule).
3. The stale `event/_koppu.log` / `_carina.log` are not published copy; leave
   them or regenerate, but they must never be a metrics source — the meta JSON
   under `site/public/data/` is canonical.
