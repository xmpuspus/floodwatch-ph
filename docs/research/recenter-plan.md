# Re-centering plan — FloodWatch.PH

Date: 2026-05-17. Status: PROPOSAL — direction not yet locked. No build until
AskUserQuestion gate is answered (same gate discipline as the v1.2 wave).

Basis: docs/research/skeptic-walkthrough.md, docs/research/product-audit-
reframed.md, docs/research/related-work.md §3, memory:
floodwatch-ph-weather-app-drift, floodwatch-honesty-vs-strategy-lesson.

## The finding in one paragraph

The defensible spine is built and strong (capability ≈88/100): the
recurrence-vs-historical-record gap, single-repo bit-exact reproducibility, and
observed pluvial/urban extent for the class forecasters exclude — all already
live and honest in /methodology, /recurrence, /safety, /faq, /privacy, the
/map Carina tab, and the /lookup evidence matrix. Strategic prominence is ≈28/100:
the two pages a new visitor sees (`/`, `/map`) and the map's default tab lead
with RainViewer-sourced rain and a 10-row null expressway table; the spine sits
~68% down the homepage and on a non-default tab. **This is a foregrounding
problem, not a capability problem. The fix is demotion and reorder, not
features.** Likely net change: LESS realtime prominence, fewer surfaces.

---

---

## NORTH STAR RECALL (2026-05-17, post-gate) — supersedes the headline question

At the AskUserQuestion gate the user did not pick a headline. They said: *"the
goal of this project was supposed to be to correlate flood control projects or
lack thereof to floods."* Verified against the repo and the locked spec:

- **Zero** flood-control / DPWH / COA / appropriation / infrastructure-project
  reference exists anywhere in the codebase or data (`site/public/data/` is
  flood extent + recurrence + exposure + roads only).
- The locked v1.0 spec (`docs/research/floodwatch-spec.md` §1) thesis is
  *"where the water goes vs where the maps say it goes"* — observed extent vs
  hazard maps / NDRRMC damage assessments. **Not** flood-control spending.
- The flood-control-accountability idea is the original **seed** (spec cites
  `solar-map-ph/docs/research/next-ideas.md`, FloodWatch entry idea #1, 27/30).
  It was substituted away **at spec time** and never built.

### There are two drifts, not one

- **Drift 1 (v1.1→v1.3, the brief's subject):** realtime rain + cinematic
  chrome buried the recurrence-vs-record spine. (Phases 1–2.)
- **Drift 0 (seed→v1.0 spec):** the original **accountability** thesis
  (flood-control spending/absence × observed flooding — the DPWH/COA civic
  question, the same playbook as paper-trail-ph / infrawatch-ph / budget-trace-
  ph) was replaced by a **measurement** thesis (observed extent + recurrence vs
  the fetchable GFD record). The "defensible spine" Phases 1–2 fought to
  promote is itself a *substitute* for the real North Star.

Drift 0 was almost certainly forced by the civic-tech-ph "government data fails
3 ways" constraint: at seed time DPWH flood-control project data was PDF/SPA/
no-clean-geo, so the build took the fetchable substitute (GFD on Earth Engine).
Locally honest, cumulatively off-thesis — the same failure mode as
[[floodwatch-honesty-vs-strategy-lesson]], one level deeper.

### Why the accountability North Star is the right re-center (and stronger now)

- It is the single best answer to "why use this not RainViewer/Flood Hub/NOAH":
  **none of them cross-references public flood-control spending against observed
  flooding.** It is not a weather product — it is an accountability product
  that uses flood observation as evidence. That structurally ends the
  weather-app drift: rain/extent become *evidence for a spending claim*, not
  the product.
- It fits the user's civic-tech cluster exactly: public spend × independent
  signal. FloodWatch becomes "infrawatch for flood control."
- The 2025 PH flood-control corruption scandal forced large volumes of DPWH
  flood-control project data into the public domain (project databases, COA
  findings, hearing exhibits) — the seed-era data blocker is materially
  weaker now, though geo-resolution will still hit the schema-gap failure mode
  (many records are "Brgy/Municipality" text, not coordinates).

### The hard honesty constraint (leads the decision)

FloodWatch's **live data has no flood-control layer today.** Re-centering the
*narrative* onto flood-control accountability without the data would claim a
finding the product cannot back — a direct violation of data-integrity.md
("compute before narrating", "every number needs a source") and the
civic-tech-ph conservative-language / defamation posture. So the re-center is
honestly **two staged things**:

- **(A) Narrative + structure re-center — no new data, this wave.** Demote
  realtime/cinematic (locked: split identity). Reframe the *existing* spine as
  *step 1 of the accountability question* — "where does it repeatedly flood:
  the observed substrate we will hold flood-control spending against" — with
  the flood-control layer named as the explicit, in-progress **destination**
  (honest roadmap, not a claim).
- **(B) Flood-control accountability layer — a separate data wave.** Source
  DPWH/COA flood-control project records, geolocate (the hard part, schema-gap
  caveat), cross-reference vs observed Sentinel-1 extent + recurrence, output
  conservative "warrants investigation" indicators with the mandatory
  disclaimer block. The real North Star, but its own data + legal-language
  gate. **Not** part of this wave.

### Locked at the gate (2026-05-17)

- Realtime posture: **split identity** — spine is the product; all realtime
  survives as one explicitly-secondary, fully-attributed context surface.
- `/map` default: **civic/observed view default, realtime as 2nd tab.**
- Wave scope: **entry + lookup synthesis.**
- Headline thesis: **superseded by the North Star recall** — re-gated below.

---

## DEMOTE / CUT (reduce realtime + cinematic prominence)

| # | Item | Now | Proposed | Why |
|---|------|-----|----------|-----|
| D1 | Global "Freshest observation: rain radar … via RainViewer" banner | First sentence of `/` and `/map`, top of page | Removed from lead. Rain becomes a dated context strip BELOW the spine, labelled "rainfall context (source: RainViewer/PAGASA — not produced by FloodWatch)" | Leads with the one signal FW doesn't produce; an incumbent owns it |
| D2 | `/map` default tab = "Now (latest observed pass)" | Default; weather + null Corridor watch | Civic/observed-extent + hazard-gap view becomes default; "Now (rain + expressways)" demoted to clearly-secondary context tab | The default route hides the spine |
| D3 | Corridor watch as a headline H2 | Prominent on `/` and `/map` Now | Demoted to a small context module, not a headline; honest "10× no overlap this pass" framing kept but not foregrounded | Steady state is null; recruits a commuter the copy then turns away |
| D4 | v1.3 cinematic GIBS basemap | Off by default already | Formally retire as a default concern; do not invest further | Sunk cost, zero default audience (audit theme 5) |
| D5 | Rain radar as a default-checked top map layer | Default-checked, top of layer list, "Freshest" badge | Keep available, move below observed/recurrence layers, drop "Freshest" superlative framing | Freshness is borrowed; it should not headline the layer stack |
| D6 | "where the water actually went" extent as the homepage H1 (×2) | The H1, twice | Demote to a supporting section under the spine hero | Extent is GFM/UNOSAT's operational ground; not FW's distinct claim |

Open decision for the gate: does D3 go all the way to **cut** (remove the
realtime/Corridor surface from the primary product entirely, link out to
RainViewer/PAGASA) or stop at **demote-to-context**? See Decision 1 below.

## PROMOTE (make the defensible spine foreground)

| # | Item | Now | Proposed | Why |
|---|------|-----|----------|-----|
| P1 | Recurrence-vs-record gap finding (337 modeled-prone, under-observed) | Block 7, ~68% scroll, faint tile | The homepage hero / H1 thesis, above the fold, in 10s | This is the §3 contribution; it must be the first thing |
| P2 | Single-repo bit-exact reproducibility ("hash-verified, ~30s, no GPU, SolarMap analog") | Only on /recurrence, 4 clicks deep | Stated on the homepage hero and near the `/map` civic view | The sharpest checkable differentiator vs GFM and closed forecasters |
| P3 | The pluvial/urban "forecaster-excluded class" framing | Implicit in related-work, not on entry | One explicit line on `/` and `/map`: "the flood class Google Flood Hub says it does not model — observed, after the fact, openly" | Names exactly why FW is complementary, not redundant |
| P4 | `/lookup` evidence matrix | 3rd nav item, query required | Promote in nav order and link prominently from the spine hero; it IS the spine as a usable tool | Strongest civic surface, currently under-routed |
| P5 | Privacy-preserving client-side design | Filed as /privacy disclosure | Promote as part of the reproducibility differentiator on entry | An under-used asset that reinforces the spine |

## REFRAME (same data, sharper civic framing — honesty preserved)

| # | Item | Reframe | Why |
|---|------|---------|-----|
| R1 | Homepage H1 | From "Where the water actually went." (extent) to a recurrence-gap-first thesis line (exact wording = Decision 2) | The headline must carry the differentiator, not the commodity |
| R2 | `/lookup` + map result | Synthesize "modeled-prone + thin historical record → under-observed-prone" as ONE explicit, conservative sentence per result, not two of five rows the user must infer | The civic signal must be stated, not left to inference; keep conservative-language posture (civic-tech-ph rule) |
| R3 | Rain everywhere | Always "rainfall context (source: RainViewer / PAGASA)" — never "freshest", never a lead, never a FW-branded freshness clock | Attribution honesty must not read as FW's headline value |
| R4 | "Not a forecast — use PAGASA/MMDA" disclaimer | Keep (required), but pair with a positive "what FloodWatch IS for" line so the page is not net-deflecting | Currently the strongest call-to-action points away from the product |
| R5 | Realtime/"Now" language | Reframe from a realtime promise to "most recent observed pass, lagged — the open reproducible record, not a live feed" | Stops competing on liveness it cannot win; competes on reproducibility it owns |

---

## LOCKED (AskUserQuestion rounds 1+2, 2026-05-17)

| Decision | Locked value |
|---|---|
| Realtime posture | **Split identity** — spine is the product; all realtime survives as one explicitly-secondary, fully-attributed context surface |
| `/map` default | **Civic/observed view default; realtime as the 2nd tab** |
| Wave scope (A) | **Entry + lookup synthesis** |
| North Star sequencing | **Re-center now (wave A), flood-control data layer = wave B next** |
| Data feasibility | **Sweep first — done.** Verdict: see below |
| Framing posture | **Conservative civic-tech-ph** — "warrants investigation", never an accusation; mandatory disclaimer + all-data-is-public-record block on every accountability surface |
| Destination thesis | **"Where flood-control money was spent — and where the water still came."** |

The headline question was superseded by the North Star recall (see above).
Both gates are answered. Wave A is direction-locked; **no code starts until
the user gives an explicit build go** (this session's brief: diagnosis +
strategy only).

---

## Feasibility verdict (docs/research/flood-control-data-feasibility.md)

**YELLOW — proceed with constraints.** The data exists, is CC0, and is
geolocated: BetterGovPH HuggingFace `bettergovph/dpwh-transparency-data`,
~9,855 flood-control projects (₱545B, 2022–2025) with coordinates; COA audits
have flagged confirmed ghosts; no paywalls/auth. The structural constraint is
the **geolocation trap**: DPWH MYPS coordinates are planning-stage, not
as-built; COA proves ~10–15% mislabeled/relocated/non-existent. Therefore the
defensible claim is **budget-accountability + audit-finding correlation, NOT
flood-prevention efficacy or causality.** Honest claim shape: "₱X was
allocated to flood control near here; Sentinel-1 still observed flooding on
these dated passes; this warrants independent investigation" — never "this
project failed" or "this project is a ghost."

## Wave B blueprint = ghostwatch (docs/research/ghostwatch-study.md)

ghostwatch is the proven, deployed sibling that already does exactly this
pattern (248k DPWH contracts × Sentinel-2, adapter ingestion, 3-layer
conservative-language governance, CI disclaimer gates) — and it ingests the
**same BetterGovPH dataset** the feasibility sweep independently found.
Directly reusable for wave B:

- **Adapter ingestion** (`ghostwatch/adapters/philippines.py`) — column-variant
  detection, status normalization, geolocation extraction. Copy as a
  `FloodControlAdapter`.
- **3-layer conservative-language governance** (`api/routers/analytics.py`;
  `tests/test_api.py:279-306`) — disclaimer hardcoded at the API layer
  (un-strippable), aggregation-only output (region/type/budget tranche, never
  named-project "flagged" lists), "flagged for review" never "ghost", CI gate
  that fails the build if a disclaimer is missing. **Non-negotiable; copy
  exactly.** This is ghostwatch's load-bearing pattern.
- **Config-as-Pydantic-Settings thresholds**, classifier truth-table CI tests.

**FloodWatch's distinct question vs ghostwatch (the differentiator):**
ghostwatch verifies *was the structure built* (optical construction
detection). FloodWatch wave B verifies *was the money spent here and did the
water still come* — flood-control project locations × FloodWatch's own
observed Sentinel-1 flood extent + recurrence. ghostwatch checks construction;
FloodWatch checks **outcome adjacency** (allocation near observed recurrent
flooding), without claiming causality. That combination exists nowhere else —
it is the strongest possible answer to the skeptic's "why not RainViewer/Flood
Hub/NOAH". SAR construction-detection (`sar-ghostwatch`) is research-stage —
reference its risk-gating framework, do not port the SAR pipeline.

### Data-integrity landmines (flag now, enforce at wave B)

- **The 337 collision.** FloodWatch already publishes "337 modeled-prone
  under-observed provinces". The feasibility sweep notes COA flagged "337
  confirmed ghosts". These are **unrelated numbers**. They must never appear
  adjacent or be conflatable in any copy, tile, or chart. Treat as a
  release-gate grep.
- **No efficacy/causality claims** (feasibility constraint + civic-tech-ph).
- **Geolocation_confidence** must be carried and surfaced; ~10–15% coordinate
  uncertainty stated honestly per the geolocation trap.
- Aggregation-only public outputs; named projects only via direct ID lookup
  (ghostwatch friction pattern).

---

## Wave A (this re-center) — concrete, no new data

DEMOTE/PROMOTE/REFRAME tables above stand, now pointed at the locked
destination thesis. Net of wave A:

1. **Split identity:** `/` and `/map` lead with the spine; all realtime (rain,
   Corridor watch, cinematic) collapses to one explicitly-secondary,
   fully-attributed context surface (RainViewer/PAGASA credited as the real
   source, never "freshest", never the lead).
2. **`/map`** defaults to the civic observed + hazard-gap view; realtime is
   tab 2, clearly labelled context.
3. **Homepage hero** = the recurrence-vs-record spine reframed as *step 1 of
   the accountability question*, with **"Where flood-control money was spent —
   and where the water still came."** named as the explicit in-progress
   destination (honest roadmap line, not a claim — the data is wave B).
4. **`/lookup` + map result:** synthesize the gap as one explicit conservative
   sentence per result (R2), not five rows to infer.
5. Retire the cinematic basemap as a default concern.

Wave A claims nothing the live data can't back. It re-points the narrative at
the true North Star and demotes the weather chrome. Wave B (the flood-control
layer) is a separate build with its own data + legal-language gate, blueprinted
on ghostwatch, blocked until explicitly authorised.

No code, copy, or component changes until the user gives the build go.
