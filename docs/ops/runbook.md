# FloodWatch.PH ops runbook — scheduled refresh

The near-real-time data chain (Sentinel-1 flood, GPM rainfall context,
expressway exposure) is regenerated and redeployed by the
`.github/workflows/refresh.yml` GitHub Actions workflow. This is the operator
guide for that loop: cadence, what each state means, how the gate decides,
how the public alias is repointed, and how to recover when something breaks.

## 1. Cadence and triggers

- **Scheduled:** daily at `17 18 * * *` UTC (~02:17 PH time, off-peak,
  deliberately an off-minute).
- **Manual:** `workflow_dispatch` from the Actions tab. Optional input
  `skip_deploy` (boolean) regenerates the data and runs the gate but does not
  deploy or re-alias — use it to validate a fix without touching production.
- **Never** on `pull_request`. The workflow handles secrets; a fork PR must
  never be able to run it.

Why daily: Sentinel-1 revisits the Philippines about every 6 days (Sentinel-1A + Sentinel-1C, restored ~May 2025) with ~24 h product latency, so a new SAR
pass appears at most once a day's worth of latency after acquisition. GPM
IMERG latency is ~30 minutes to a few hours, so a daily run keeps the rainfall
context current without hammering Earth Engine. If a major event is in
progress and you want the freshest possible pass, trigger `workflow_dispatch`
manually — do not lower the cron frequency (EE quota + Vercel deploy noise).

## 2. What each `scan_status` means operationally

The three files each carry `_meta.scan_status`. Operationally:

| File | status | Meaning | Operator action |
|---|---|---|---|
| flood_latest | `ok` | Real S1 flood polygons published | None — normal |
| flood_latest | `no_usable_pass` | No S1 acquisition with enough AOI coverage in the lookback window | None — honest, site says "no recent usable pass". Expected most days (revisit gap) |
| flood_latest | `degenerate_threshold` | A pass exists but Otsu found no water/land separation | None — honest, site says "no reliable water signal" |
| flood_latest | `low_confidence` | Detected area exceeds the plausibility cap (speckle/agri) | None — honest, site says "inconclusive" |
| current_risk | `ok` | Rainfall accumulation sampled over prone areas | None — normal |
| current_risk | `no_data` | No IMERG image available | None — honest empty |
| current_risk | `low_confidence` | IMERG present but unreliable | None — honest empty |
| road_flood_exposure | `ok` | Real road∩water intersections computed | None — normal |
| road_flood_exposure | `no_usable_pass` / `degenerate_threshold` / `low_confidence` | Carried from flood_latest; segments emitted with `exposure="unknown"` | None — honest, site says "no usable pass" |

Key principle: **an honest empty state is the product working, not an
incident.** The site is built to say "no recent usable pass" truthfully. Do
not "fix" a `no_usable_pass` — it just means no satellite flew a usable track.

## 3. How to read the gate (`scripts/gate_realtime.py`)

Runs before any deploy. Validates all three files and exits:

- **PASS (exit 0)** — safe to deploy. Possibly with **WARN** lines (e.g.
  `as_of` older than S1 20 days / GPM 24h). Stale-but-honest is a warning, not
  a block: an old `no_usable_pass` is still the truth and must reach the site.
- **BLOCK (exit 1)** — broken/garbage detected. The deploy does NOT run; the
  last known-good deployment stays live.

The gate BLOCKS on, in order: invalid JSON, not a FeatureCollection, missing
required `_meta` keys, an unknown `scan_status`, unparseable `as_of`,
`feature_count` not matching `features[]`, **`scan_status=="ok"` with zero
features** (claims water, ships none — contradictory envelope), or a **non-ok
status shipping fabricated geometry** (claims no usable data, ships polygons).
It also runs the locked `check_permanent_water.py` (covers `flood_latest`
through the `flood_*.geojson` glob) and `check_no_pii.py`.

Run it locally exactly as CI does:

```
.venv/bin/python scripts/gate_realtime.py
# tighten staleness into a hard fail (e.g. for a paranoid manual deploy):
.venv/bin/python scripts/gate_realtime.py --strict-stale \
    --s1-max-age-days 20 --gpm-max-age-hours 24
```

## 4. Deploy + RE-ALIAS (the locked gotcha)

`vercel deploy --prod` creates a NEW immutable deployment URL. It does **not**
repoint the public domain. `scripts/deploy_realias.py` makes the re-alias an
explicit, verified step:

1. Record the current production deployment URL (the rollback target).
2. `vercel pull` → `vercel build --prod` → `vercel deploy --prebuilt --prod`.
3. **`vercel alias set <newDeploymentUrl> <publicDomain>`** — repoint the
   public domain at the new deployment.
4. Verify the LIVE alias with `scripts/qa_live.py` (real behavioral QA — map
   paints, `window.__fwReady`, the three data files reachable, honest-empty
   accepted as PASS) — not a bare HTTP 200.

Manual equivalent if you ever deploy by hand:

```
cd site
vercel --token "$VERCEL_TOKEN" pull --yes --environment=production
vercel --token "$VERCEL_TOKEN" build --prod
URL=$(vercel --token "$VERCEL_TOKEN" deploy --prebuilt --prod --yes | tail -1)
vercel --token "$VERCEL_TOKEN" alias set "$URL" floodwatch-ph.vercel.app
python ../scripts/qa_live.py https://floodwatch-ph.vercel.app
```

## 5. Rollback procedure

`deploy_realias.py` does this automatically when live verification fails: it
re-aliases the public domain back to the previous known-good deployment
captured in step 1. Manual rollback to a specific prior deployment:

```
cd site
# list recent prod deployments, pick the last-known-good URL:
vercel --token "$VERCEL_TOKEN" ls --prod --yes
# repoint the public domain back to it:
vercel --token "$VERCEL_TOKEN" alias set https://<good-deployment>.vercel.app floodwatch-ph.vercel.app
# confirm:
python ../scripts/qa_live.py https://floodwatch-ph.vercel.app
```

If the automatic rollback itself failed (the pager issue will say
`ROLLBACK ALSO FAILED` or `no known previous deployment`), do the manual
re-alias above immediately — the public domain may be serving the bad deploy.

## 6. The GitHub-issue pager

`deploy_realias.py` opens a GitHub issue (labels `ops`, `refresh-failure`)
when either:

- a deploy/alias step fails before going live (alias unchanged, no bad data
  shipped), or
- live verification fails after re-alias (rollback attempted; issue records
  whether rollback succeeded and the `qa_live.py` tail).

It uses the Actions-provided `GITHUB_TOKEN` (`issues:write`) and
`GITHUB_REPOSITORY`. The issue body links back to this runbook. Triage: read
the issue, decide whether the gate should have caught it (tighten
`gate_realtime.py`) or it was a transient Vercel/network failure (re-run
`workflow_dispatch`).

## 7. Manual trigger

Actions tab → `refresh` → "Run workflow". Set `skip_deploy=true` to validate
the regeneration + gate without deploying (use after a code fix to confirm the
gate is green before letting it go live).

## 8. Required GitHub secrets / variables (names + least-privilege scope)

Secrets (`Settings → Secrets and variables → Actions → Secrets`):

| Name | What | Least-privilege scope |
|---|---|---|
| `EE_SERVICE_ACCOUNT_KEY` | Earth Engine service-account key JSON (full file contents) | A dedicated EE service account with read-only access to the public image collections used (Sentinel-1 GRD, GPM IMERG, JRC water, datasets). No other GCP roles. Never committed — `.ee-key.json` is gitignored and materialised to a runtime tmpfile only |
| `VERCEL_TOKEN` | Vercel access token | Scoped to the `floodwatch-ph` project / its team only. Deploy + alias scope. Not a personal account-wide token |
| `VERCEL_ORG_ID` | Vercel team/org id | Identifier only (matches `site/.vercel/project.json` `orgId`) |
| `VERCEL_PROJECT_ID` | Vercel project id | Identifier only (matches `site/.vercel/project.json` `projectId`) |
| `GITHUB_TOKEN` | Actions-provided token for the pager | Workflow grants `issues: write` only at the job level; everything else is `contents: read` |

Variable (optional, `Actions → Variables`):

| Name | What | Default |
|---|---|---|
| `VERCEL_PUBLIC_DOMAIN` | Public domain to re-alias | `floodwatch-ph.vercel.app` |

The EE key is read by `floodwatch_ph/eeauth.py` / the realtime modules via the
`EE_KEY_FILE` env var, which the workflow points at a `${runner.temp}` tmpfile
created with `umask 077` and shredded in an `if: always()` cleanup step. It is
never written to the repo and never echoed.

## 9. Residual risk

- The data chain depends on three external services (Copernicus/EE,
  NASA GPM, OpenStreetMap Overpass). A regeneration script failing hard fails
  the workflow before the gate — the previous good deploy stays live, the
  workflow goes red, but the GitHub-issue pager only fires from
  `deploy_realias.py`; a regeneration/gate failure surfaces as a red workflow
  run (watch Actions or add a notification on the `refresh` workflow).
- Vercel CLI / API behaviour can change; the CLI is version-pinned
  (`vercel@39.1.3`) to limit drift.
- The `/lookup` page check in `qa_live.py` is intentionally lenient until
  Agent G's route lands (skips on 404). Re-tighten it once `/lookup` is live.
