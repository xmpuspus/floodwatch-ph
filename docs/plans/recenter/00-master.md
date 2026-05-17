# North Star re-center — execution master (build, locked)

Worktree: `.claude/worktrees/northstar-recenter`, branch `feat/northstar-recenter` off origin/main @ dc74651.
Spec is `docs/research/recenter-plan.md` + `ghostwatch-study.md` + `flood-control-data-feasibility.md`. Do not relitigate.

## Architecture reality (governs the ghostwatch adaptation)

FloodWatch is a **static Astro site** (`site/`) + a **Python pipeline** that writes
JSON/GeoJSON into `site/public/data/`. There is **no FastAPI backend**. ghostwatch's
"API-layer un-strippable disclaimer" therefore maps onto the **data-generation layer**:

- The disclaimer is a hardcoded constant in a Python governance module. The pipeline
  imports it and writes it into the top-level `_meta.disclaimer` of every generated
  accountability JSON file AND into every aggregation record. Clients cannot strip it
  because it is baked into the published artifact, and CI fails the build if it is missing.
- **Aggregation-only public output:** the rendered file holds region/province ×
  project-type × budget-tranche aggregates + the cross-reference summary only. No array
  of named flagged projects anywhere the UI can list.
- **Named projects only via direct ID lookup:** a separate id-keyed map; the UI never
  renders a "flagged projects" list. Friction is intentional and load-bearing.
- "flagged for review" / "warrants independent investigation" — never "ghost",
  "failed", "caused", or any efficacy/causality claim.

## The distinct claim (FloodWatch's reason to exist)

flood-control project locations (BetterGovPH `bettergovph/dpwh-transparency-data`,
CC0, filter flood-control ≈9,855 projects, ₱545B) × FloodWatch's **own** signal:
`recurrence_prone.geojson` / `hazard_gap.geojson` (82 province polygons:
`city`=province, `province`=region, `recurrence_score`, `observed_events`, `gap`)
+ observed Sentinel-1 extent (`flood_carina_2024.geojson`, `flood_latest.geojson`).

Output shape, conservative, hardcoded: "₱X was allocated to flood control in this
province; Sentinel-1 still observed flooding on these dated passes; the recurrence
model rates it modeled-prone — this warrants independent investigation." NEVER a
verdict on any project.

## Locked decisions (do not re-ask)

- Split identity: spine = the product. ALL realtime (rain banner, Corridor watch,
  cinematic basemap) → ONE explicitly-secondary, fully-attributed (RainViewer/PAGASA)
  context surface. Never "freshest", never the lead.
- `/map` default = civic observed + hazard-gap view (Carina/hazard-gap tab). Realtime
  = tab 2, labelled context.
- Destination thesis: **"Where flood-control money was spent, and where the water
  still came."** Wave A names it as honest in-progress roadmap; wave B makes it
  data-backed.
- Posture: conservative civic-tech-ph. "warrants independent investigation", never an
  accusation. Mandatory disclaimer + all-data-is-public-record block on every
  accountability surface. RA 10173 posture intact.
- Plain-English / no-AI-fingerprint pass over **everything** (copy, code, docs,
  commits) — `~/.claude/rules/no-ai-jargon.md` is a hard ban; enforced by a release grep.

## The 337 collision (release-gate)

`site/src/data/metrics.ts` already publishes `uncharted_count: "337"` = modeled-prone
under-observed **provinces**. COA separately confirmed "337 **ghosts**" — UNRELATED.
Wave B must **not** use the COA-337 figure at all (we ingest BetterGovPH, which has no
COA ghost flags; our numbers are computed from our own pipeline). Release grep fails the
build if "337" ever appears adjacent to / conflatable with "ghost"/"confirmed" in any
site copy or data artifact.

## Partition + sequencing

Phase 1 (parallel, disjoint trees, one worktree):
- **Agent-WA** — owns `site/**` only. Wave A narrative re-center + plain-English pass +
  the accountability surface UI (codes against the schema in `10-wb-data-brief.md`,
  consumes the JSON like the existing `road_flood_exposure.geojson` fetch pattern).
- **Agent-WBD** — owns `floodwatch_ph/**`, `pipeline/**`, new data files, schema doc.
  FloodControlAdapter + BetterGovPH ingest + cross-reference + governance module
  (hardcoded disclaimer) + aggregated JSON + by-id map.

Phase 2 (sequential, after Phase 1 verified):
- **Agent-WBI** — integrity: CI gates, 337 grep, AI-jargon grep, pytest truth-tables,
  `verify_release.py` + `ci.yml` + `Makefile` + `qa_live.py` updates (qa_live's "Now is
  default" assertion flips with the /map default).

Orchestrator verifies every agent's output against source before integrating, runs the
honesty + data-integrity gates per wave, then the ship pipeline.

## Honesty gates (block ship)

Per wave: no false live/forecast/verdict; every layer dated; complementary-not-
replacement intact; every number [VERIFIED] with a source, computed before narrated;
no placeholder prose. The accountability surface carries the disclaimer + all-data-is-
public-record block. CI fails if a disclaimer is missing.
</content>
</invoke>
