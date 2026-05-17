# Agent F — defensibility / overclaim audit, v1.2 "expressway corridor conditions"

Status: adversarial verdict file. Produced by the defensibility/copy auditor
(author of related-work.md + copy-audit.md). Grounded against the actual
shipped copy as read 2026-05-17 (FreshnessBanner.astro, NowView.astro,
index.astro, lookup.astro, AreaLookup.astro) and the locked posture
(realtime-sources.md §4/§5/§7, related-work.md §3, copy-audit.md cracks d/e).
READ-ONLY: no code or site file edited here.

---

## 0. One-paragraph verdict

The v1.2 corridor surface is defensible **only if it stays in the observation-
archive register the shipped site already uses** ("the most recent OBSERVED
satellite pass, not a live feed and not a forecast" / "Did the latest satellite
pass see water on the expressways?"). Decision 1 framing B ("Corridor
conditions, as of <times>") and framing C ("Is rain falling … right now?") both
import a present-tense register that the locked posture forbids for every layer
except the RainViewer rain heartbeat, and either one, if chosen naively, becomes
a **systemic present-tense overclaim** that leaks the word "now"/"current"/"live"
into 9-11 files (the same failure class as the historical "10 m" / "barangay" /
"6-12 day" systemic drifts). Framing A ("Corridor watch") is the only option
that is structurally safe across all layers because it never makes a
present-tense promise the dated SAR/GFM/GloFAS layers cannot keep. The single
most dangerous misread across every option is the routing/safety verdict — a
commuter seeing a red SLEX segment and concluding "SLEX is flooded right now,
don't drive it" — which the posture explicitly forbids FloodWatch from
implying; this is neutralized by the mandatory PAGASA/MMDA/DRRMO redirect +
"not a routing instruction" + the ticking as-of clock, all of which already
exist in NowView and must be carried verbatim onto the corridor surface.
Separately, the "~6-12 day" S1 figure is a confirmed **stale specific-number
systemic overclaim** (13 instances in shipped src + docs) that v1.2 must patch
to "~6-day revisit, ~24 h product latency" regardless of which framing wins.

---

## 1. Stale "6-12 day" instance count (data-integrity systemic drift, pre-existing)

copy-audit.md flagged FreshnessBanner.astro at lines ~6/105/139 — **confirmed
exact** at the current read: line 6 (comment), line 105 (`revisit ~6 to 12
days`), line 139 (`Sentinel-1 revisit is ~6 to 12 days`).

Full grep of `site/src/` + `docs/` + `README.md` + `CHANGELOG.md` (build
artifacts in `site/dist/` excluded — they regenerate). **Shipped/public copy
instances that MUST be patched in v1.2** (the "~6-day revisit, ~24 h product
latency" fix, §7 flag 4, data-integrity weight):

| File | Line | Surface |
|---|---|---|
| site/src/components/FreshnessBanner.astro | 6 | code comment |
| site/src/components/FreshnessBanner.astro | 105 | site-wide banner (carina/now/site) |
| site/src/components/FreshnessBanner.astro | 139 | carina banner detail |
| site/src/components/NowView.astro | 43 | expressway callout footer |
| site/src/components/NowView.astro | 286 | "no expressway flooded" line |
| site/src/components/AreaLookup.astro | 300 | lookup evidence row label |
| site/src/lib/areaLookup.ts | 359 | lookup not-usable detail |
| site/src/lib/areaLookup.ts | 371 | lookup inside-extent detail |
| site/src/pages/lookup.astro | 43 | lookup methodology footer |
| site/src/pages/index.astro | 101 | home corridor "no flooded" line |
| site/src/pages/index.astro | 108 | home corridor as-of line |
| README.md | 30 | scope/limitations bullet |
| docs/launch/linkedin-draft.md | 14 | launch copy |
| docs/ops/runbook.md | 19 | ops note (internal, lower priority but cite real cron reason) |
| docs/research/SCHEMA-latest.md | 14 | schema doc |

**Count: 13 public/shipped instances** (FreshnessBanner ×3, NowView ×2,
AreaLookup ×1, areaLookup.ts ×2, lookup.astro ×1, index.astro ×2, README ×1,
linkedin-draft ×1) + 2 internal docs (runbook, SCHEMA-latest). The research
docs under `docs/research/_realtime-scratch/*` and copy-audit.md/realtime-
sources.md themselves correctly state the new figure or quote the old one as
"stale" — leave those (they are the correction record, not public copy).

This is a **pre-existing systemic overclaim independent of the framing
decision** and is in the same class as copy-audit.md Patterns 1-4. It must be
on the v1.2 plan as an Agent-F-gated patch with a re-grep-to-zero verification
step. Recommended replacement string (matches realtime-sources.md §4.8):
`~6-day revisit (Sentinel-1A + Sentinel-1C, restored ~May 2025), ~24 h product
latency`. Shorter caption form where space-constrained: `~6-day revisit, ~24 h
product latency`.

---

## 2. Decision 1 — headline frame: per-option defensibility

The shipped voice to preserve (verbatim from the live site):
- FreshnessBanner now-variant line: *"This is the most recent OBSERVED
  satellite pass, not a live feed and not a forecast."*
- NowView H2: *"Did the latest satellite pass see water on the expressways?"*
- index.astro: *"This is the truthful current state of the latest pass, not an
  all-clear."*

This is an **observation-archive / past-perfect register**: the verb is always
"saw / was observed / on the {date} pass", never "is / now / current".

### D1-A — "Corridor watch" (observation-archive register)

- **Defensibility risk: LOW.**
- Most dangerous glancing misread: *"there's a 'watch' on the corridor =
  FloodWatch is issuing a watch/warning like PAGASA's typhoon Signal."* "Watch"
  is a loaded hydromet term (flood watch / storm watch) in the PH context.
- Neutralizing copy discipline: the word "watch" must never stand alone as a
  status. It is defensible **only** as `Corridor watch — what the satellites
  and radar have observed over the expressways` (the gloss is mandatory, not
  optional), plus the existing mandatory redirect ("Not a forecast. For live
  conditions, warnings … use PAGASA, MMDA Flood Control, your LGU DRRMO"). With
  the gloss, "watch" reads as "observation log", not "advisory". Structurally
  fixable and the lowest-risk option because the noun makes no temporal promise.

### D1-B — "Corridor conditions, as of <times>"

- **Defensibility risk: MEDIUM (HIGH if the timestamp is ever stale or absent).**
- Most dangerous glancing misread: *"'Conditions' = current road/flood
  conditions; this is telling me what the expressway is like right now"* — a
  present-tense state claim. The `as of <times>` qualifier is exactly the part a
  glancing commuter does not read; "conditions" is the part they do. This is
  the classic contradictory-envelope risk: the headline noun says "now", the
  small qualifier says "dated".
- Neutralizing copy discipline: requires the timestamp to be **in the headline
  itself, never a subordinate clause**, AND every layer to carry its own
  ticking age (the §5 spec), AND the honest-empty fallback to replace the whole
  phrase (not just blank the time) when any clock is missing — copy-audit.md's
  rule "never default a missing time to 'just now'". Even fully disciplined,
  "conditions" is a present-tense noun doing work the dated SAR layer cannot
  honor (the SAR pass may be 9 days old). Partially fixable, but it forces the
  present-tense register site-wide (see §4 systemic finding). The qualifier
  collapsing under a stale/missing clock is a structural weakness, not a
  wording one.

### D1-C — "Is rain falling on the corridor right now? (and what was last observed)"

- **Defensibility risk: MEDIUM.** Honest *only* for the RainViewer heartbeat
  layer; structurally dishonest if it heads a surface whose dominant visual is
  the dated SAR/GFM flood extent.
- Most dangerous glancing misread: *"the headline asks 'is it flooding right
  now' and shows me a red expressway → yes it is flooding on SLEX right now."*
  The question frame primes a yes/no read of whatever is most visually salient,
  and the most salient layer (red expressway segments) is the dated SAR
  intersection, not the rain. The question is scoped to rain in the author's
  head; it is not scoped to rain in the commuter's eye.
- Neutralizing copy discipline: the question must be **strictly bound to the
  rain layer's own caption and physically separated from the flood/expressway
  visual** ("Rain radar {HH:MM} UTC · nowcast (~10-min source)" per §5), and
  the flood/SAR caption must carry the dated/subordinate framing right next to
  it. This is fixable for the rain widget in isolation but **unfixable as a
  page headline** — a question headline over a flood map cannot stop a commuter
  from answering it with the flood map. Acceptable as a rain-layer
  micro-headline, rejected as the corridor-surface headline.

### D1 recommendation

**Recommended: D1-A "Corridor watch" — with the mandatory observation gloss
("what the satellites and radar have observed over the expressways").** It is
the only framing whose headline noun makes no present-tense promise, so it
cannot be falsified by a 9-day-old SAR pass or a failed rain fetch; it extends
the shipped "Did the latest satellite pass see water on the expressways?" voice
without a register change; and it keeps the rain-heartbeat as one honest
layer-clock inside the archive rather than promoting "right now" to the
headline. The locked posture (related-work.md §3: "never first/only/best, not a
forecaster, not a warning system") and the civic-tech-ph conservative-language
rule both push to the register that promises least. The one residual
discipline: never let "watch" appear without its gloss, and never style it red
or with a pulsing/alert affordance (§5: never red, never pulsing).

---

## 3. Decision 2 — per-layer hierarchy: per-option defensibility

### D2-A — flat peer layers, each with its own clock

- **Defensibility risk: MEDIUM.**
- Most dangerous misread: *"all four layers are equally current"* — a flat
  visual hierarchy implies equal freshness, so a commuter reads the 9-day-old
  SAR extent as being as live as the 5-minute rain radar, and treats the SAR
  red expressway as a now-state.
- Neutralizing discipline: each layer's §5 clock caption must state its
  latency *class label* ("nowcast" vs "near-real-time" vs "daily"), not just a
  timestamp, so the asymmetry is legible without the user computing date math.
  Fixable but fragile — relies on the user reading every caption; a glancing
  read of a flat stack defaults to "all same".

### D2-B — tiered: freshest-observation / dated-ground-truth / subordinate-optional

- **Defensibility risk: LOW.**
- Most dangerous misread: *"the top tier (rain) is the answer; the dated SAR
  below it is old/unimportant"* — i.e. the commuter over-weights the rain
  nowcast and under-reads the actual observed-flood layer.
- Neutralizing discipline: the tier labels must be descriptive of *kind*, not
  *priority* ("Freshest observation: rain radar" / "Dated ground truth:
  observed SAR flood" / "Supplementary, cloud-limited: optical"), and the SAR
  tier must keep the hero-layer visual weight it has in NowView (locked z-order:
  flood extent renders last/on top). The tiering communicates the honest
  freshness asymmetry instead of hiding it. Structurally the safest because it
  makes the central honest fact (different layers have radically different age)
  the organizing principle of the UI.

### D2-C — rain-heartbeat primary, all flood collapsed into one dated "last observed" expander

- **Defensibility risk: HIGH.**
- Most dangerous misread: *"FloodWatch's main signal is the rain heartbeat;
  the flood thing is a buried footnote → so if the rain widget is calm, the
  corridor is fine."* Collapsing the observed-flood evidence into an expander
  demotes FloodWatch's actual distinct contribution (observed pluvial/urban
  extent — related-work.md §3) beneath a rain layer that is the *least*
  FloodWatch-specific thing on the page (it is just re-rendered PAGASA radar).
- Neutralizing discipline: there is none that survives the architecture — an
  expander that hides the observed-flood layer behind a click structurally
  inverts the posture (FloodWatch is an observed-extent + recurrence artifact,
  not a rain-radar reskin). The misread is **structurally unfixable for this
  option**. Reject.

### D2 recommendation

**Recommended: D2-B tiered (freshest-observation / dated-ground-truth /
subordinate-optional), with kind-not-priority labels.** It makes the single
most important honest fact — that the rain nowcast, the dated SAR flood, and
the optical supplement have radically different ages and epistemic weight — the
*structure* of the UI rather than a caption a glancing user skips. It preserves
the shipped NowView locked z-order (observed flood is the hero, rendered last)
while honestly subordinating the optical layer. Flat (A) lets the user assume
equal freshness; collapsing flood into an expander (C) inverts the posture and
is unfixable.

---

## 4. /futureproof systemic-overclaim sweep

**Finding: YES — D1-B and D1-C create a systemic present-tense overclaim;
D1-A does not.**

The shipped site is uniformly written in the observation-archive register.
Choosing a present-tense headline frame (B "conditions"/C "right now") does not
just change one component — it forces a matching present-tense register
everywhere the corridor surface is described, or the site becomes internally
contradictory (headline says "conditions now", body says "most recent OBSERVED
pass, not live"). That contradiction is itself the overclaim. Enumerated blast
radius per framing:

**If D1-A "Corridor watch" (recommended): 1 file touched (new corridor
component only).** No register change anywhere else; the existing observation
voice in FreshnessBanner/NowView/index/lookup is consistent with "watch =
observed log". Plus the orthogonal 13-instance "6-12 day" data-integrity patch
(§1), which is owed regardless.

**If D1-B "Corridor conditions, as of <times>": 9 files need a matching
honest-language patch** to avoid the headline contradicting the body —
1. the new corridor component (headline + every layer caption),
2. site/src/components/FreshnessBanner.astro (the site-wide "Nothing here is
   live" line would now contradict a "conditions" headline),
3. site/src/components/NowView.astro ("not a live feed" sidebar + scan-status
   strings must be reconciled with "conditions"),
4. site/src/pages/index.astro (home corridor block + the inline script's
   "current state of the latest pass" wording),
5. site/src/pages/lookup.astro (lookup intro register),
6. site/src/components/AreaLookup.astro (result header register),
7. site/src/pages/methodology.astro (must explain why "conditions" is dated),
8. README.md (scope bullet, line 30 — already past-tense framed),
9. CHANGELOG.md (the v1.2 entry would have to defend the present-tense word),
plus docs/launch/linkedin-draft.md and the privacy page if "conditions" implies
any new freshness claim about the lookup. Realistic total **9-11 files**.

**If D1-C "right now" question headline: same 9-11 files as B**, and *worse* —
"right now" is a stronger present-tense claim than "conditions", so every
"not a live feed / not a forecast" string on the site (FreshnessBanner ×3
variants, NowView sidebar, index, lookup header, AreaLookup header) becomes a
visible contradiction of the headline, not just a register mismatch. This is
the exact multi-file present-tense leak the question asks to check for, and it
is the same failure shape as the historical "10 m"/"barangay"/"6-12 day"
systemic drifts in copy-audit.md (one wrong claim, replicated across every
surface that restates it).

Conclusion: **D1-A confines the v1.2 copy delta to one new component + the
owed 13-instance integrity patch. D1-B/C each open a 9-11-file present-tense
reconciliation that would have to be done perfectly and re-verified, with high
residual risk of one missed surface — precisely the systemic-overclaim trap.**
This is an independent, decisive argument for D1-A on top of the per-option
risk ratings.

### §5 freshness-clock spec — residual-overclaim check

The §5 spec (neutral grey default / amber only when staler than own cadence /
never red / never pulsing / honest-empty on fetch fail / never the word "live")
has **no residual overclaim** and is internally consistent with the shipped
honest-empty pattern (FreshnessBanner `is-degraded`, NowView scan_status). One
wording to harden:

- §5 line 161: *"Rain now (RainViewer): … **May use "now-ish"**; never bare
  'live'."* — "now-ish" is a softening that still asserts present-tense for a
  layer that can be 10+ minutes stale and whose ToS gives "no availability
  guarantee". **Harden to: drop "now-ish" entirely; use only the ticking
  relative age + class label** ("Rain radar 08:40 UTC · updated 14 min ago ·
  nowcast (~10-min source)"). The ticking age already conveys recency
  honestly; "now-ish" adds an unfalsifiable present-tense flavor with no
  informational value and is the one phrase in §5 that could seed a
  present-tense leak. Everything else in §5 is defensible as written; in
  particular the "Freshest layer: …" global ticker is honest because it names
  the layer and its absolute timestamp rather than asserting site-wide
  currency.

---

## 5. Decision 3 — posture flags (3a / 3b / 3c)

### 3a — GloFAS riverine forecast as attributed overlay vs exclude

**Recommended: EXCLUDE from the default surface; document-as-future OR ship
ONLY as a default-off, clearly-attributed external overlay + outbound deep
link, never a default layer — and this is genuinely Xavier's values call, not
a defensibility fact.** Defensibility argument for caution: related-work.md §3
states flatly "It is **not** a forecaster"; FloodWatch's entire niche
(related-work.md §1, Google Flood Hub row) is being the *observed pluvial/urban*
complement to riverine *forecasters*. A riverine forecast pixel on the corridor
map, even attributed, structurally blurs the one distinction the project
defends, and a glancing commuter cannot tell an attributed GloFAS tile from a
FloodWatch claim. If included at all it must be default-off, visually
distinct, captioned with the verbatim riverine-only exclusion (related-work.md:
"covers only riverine floods, as opposed to flash/coastal floods … pluvial
floods are not covered"), and never parsed into any FloodWatch number.
**Flagged as Xavier's call** (§7 flag 3): adding any forecast surface is a
posture choice against the "FloodWatch never forecasts" line — defensibility
says "safe only if rigidly walled and off by default", it does not say
"forbidden".

### 3b — RainViewer heartbeat (personal/educational ToS + no-availability) vs reject

**Recommended: ACCEPT, with the documented NASA GPM-Early server-cron fallback
— but the dependency-fragility appetite is Xavier's call, not a defensibility
fact.** Defensibility argument: a civic, non-commercial, open-source
educational project is squarely inside RainViewer's "personal or educational
use only" grant; the data is PAGASA/PANAHON ground radar (the same authority
the site already routes users to), and the privacy invariant holds (fixed
all-PH bbox tile, identical bytes per visitor, the user's lookup string never
in the request — realtime-sources.md §3). RA-10173 is unaffected (no personal
data, no user input transmitted). The real cost is dependency fragility ("no
availability guarantee"), which is mitigated, not eliminated, by documenting
the GPM IMERG Early (NASA, public-domain, server-cron, ~4 h) fallback.
**Flagged as Xavier's call** (§7 flag 2): whether to take a third-party
dependency that can withdraw is an appetite choice; defensibility only requires
the attribution RainViewer mandates and the honest-empty state when the fetch
fails (§5 line 180 — already specified correctly).

### 3c — GFM citing PUM CC BY 4.0 vs document-as-future on the STAC `proprietary` field

**Recommended: SHIP, citing the Copernicus EMS / GFM PUM CC BY 4.0, with the
one-line note that the EODC STAC `license: proprietary` is a catalog default
not the governing Copernicus EMS policy. This is a defensibility fact, not a
values call.** The governing instrument for Copernicus EMS data is the
Copernicus data policy / GFM Product User Manual (CC BY 4.0 / "open and free
licenses"), not an EODC catalog metadata default; treating a known-wrong
metadata default as authoritative over the documented product licence would be
*under*-claiming and would drop a legitimately-open, faster-observed SAR layer
for no real licence risk. The honest move is to ship with the PUM citation
*and* the transparency note about the STAC field discrepancy (this is exactly
the kind of caveat the site's voice already does well). Only escalate to
document-as-future if Xavier wants a maximally conservative reading (§7 flag 1)
— but defensibility does not require it; the citation + note is the correct,
honest, well-supported position.

### D3 recommendation summary

- **3a: EXCLUDE / default-off-walled-overlay only** (Xavier's values call) —
  forecast pixel blurs the defended niche.
- **3b: ACCEPT with GPM-Early fallback documented** (Xavier's dependency-
  appetite call) — civic/educational use is inside the ToS; privacy intact.
- **3c: SHIP citing PUM CC BY 4.0 + STAC-default note** (defensibility fact) —
  PUM governs; STAC `proprietary` is a known catalog default.

---

## 6. Locked guardrail-copy non-regression — where each block MUST appear on v1.2

All four guardrail blocks from copy-audit.md crack e are **confirmed present in
the shipped surface** and MUST be carried, unmodified, onto the v1.2 corridor
surface. No candidate framing regresses them *by itself*, but D1-B/C's
present-tense register would put the headline in tension with blocks 1 and 3
(another argument for D1-A). Required placement:

| Guardrail block | Confirmed shipped at | MUST appear on v1.2 corridor surface at |
|---|---|---|
| **Lookup-result header** ("observed and modeled evidence … not a forecast and not a safety instruction. It does not say this area will or will not flood.") | AreaLookup.astro:39-41 | Verbatim at the top of every corridor lookup/result, before any layer — unchanged. If the corridor view has its own result panel, it gets its own copy of this block. |
| **Evidence framing** (enumerates the observed/modeled/historical layers, "A thin record is not proof of safety; a high score is not a prediction.") | AreaLookup result body + lookup.astro:18-26 | Wrapping the corridor's returned layers; extend the enumeration to name the new rain/SAR-GFM layers with their as-of class, keep the "not proof of safety / not a prediction" clause verbatim. |
| **Mandatory PAGASA/MMDA/DRRMO redirect** ("Not a forecast. For live conditions, warnings, and routing during an active flood, use PAGASA … FloodWatch is complementary to and never a replacement for these and Project NOAH / Google Flood Hub.") | FreshnessBanner.astro:42-48, NowView.astro:43-48, index.astro:67-72, AreaLookup.astro:171 | Verbatim on the corridor surface itself (not only in the global banner) — this is the single block that neutralizes the routing/safety misread (§2, §3) and must be co-located with the expressway visual, exactly as NowView.astro:43-48 already does it. Non-negotiable. |
| **Public-records disclaimer** ("Observed flood extent derived from public satellite data. Patterns may have legitimate explanations; figures warrant independent verification.") | NowView.astro:150-153, lookup.astro:48-50, AreaLookup.astro:180 | Footer of the corridor surface and any corridor result panel — verbatim, the site's standard line. |

Additionally, the §0/§4 dynamic as-of clock (the ticking-age §5 spec) must be
present on **every** corridor layer; a corridor surface that shows a red
expressway without an adjacent as-of date + the redirect block is the single
configuration that makes the routing-verdict misread unrecoverable and must be
treated as a hard ship gate.

---

## 7. Hard ship gates for the v1.2 plan (carry into Phase 3 / Agent D)

1. Patch all 13 public "~6-12 day" instances (§1) → "~6-day revisit, ~24 h
   product latency"; re-grep to zero before ship. Data-integrity weight.
2. Headline = D1-A with mandatory observation gloss; never the bare word
   "watch" or "conditions" or "now" as a standalone status.
3. Layer structure = D2-B tiered, kind-not-priority labels, observed-flood
   keeps hero z-order.
4. Drop "now-ish" from §5 line 161; ticking age + class label only.
5. All four guardrail blocks present *on the corridor surface itself* per the
   §6 placement table — the redirect block co-located with the expressway
   visual is non-negotiable.
6. Every corridor layer carries its own as-of clock; honest-empty (not blank,
   not "just now") on any failed/missing fetch.
7. If 3a/3b/3c land as ship (Xavier's calls): GloFAS default-off + verbatim
   riverine exclusion; RainViewer attribution + GPM-Early fallback documented;
   GFM cites PUM CC BY 4.0 + STAC-default transparency note.
