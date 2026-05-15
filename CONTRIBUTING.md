# Contributing to FloodWatch.PH

Thanks for considering a contribution. This repo welcomes:

1. **Verified false-positive reports** on the recurrence-prone layer or flood-extent
   polygons. Open an issue with the barangay name, event key, and a screenshot or
   coordinate pair. Label it `data-quality`.
2. **Additional validation events** -- GFD events with a published ground-truth
   polygon that can serve as an independent IoU benchmark for Track A. Open an issue
   first with the GFD event ID and the acquisition date you intend to use.
3. **New typhoon events** for Track A. See [examples/run_on_new_event.md](examples/run_on_new_event.md)
   for the recipe. Events added without a published ground-truth reference should be
   registered with `_meta.gauged: false`.
4. **Bug fixes and code review** on anything in `event/`, `model/`, `pipeline/`, or
   `scripts/`.
5. **Site improvements** (accessibility, mobile layout, performance) in `site/`.
   Open a PR with `pnpm typecheck` and `pnpm build` both passing.

Please do not open PRs that modify `model/embeddings/floodwatch_embeddings_v1.npz`,
`model/holdout_events.json`, or `model/recurrence_clf_v1.joblib` without first
opening an issue discussing the change. These files are the integrity core of the
deterministic build.

## Dev setup

```bash
git clone https://github.com/xmpuspus/floodwatch-ph
cd floodwatch-ph
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest

# Verify the deterministic build before changing anything.
make train          # builds recurrence_clf_v1.joblib from cached floodwatch_embeddings_v1.npz
make hash-verify    # asserts sha256 b7c702532f92c43f
pytest tests/ -q
```

For the Astro site:

```bash
cd site
pnpm install
pnpm dev            # http://localhost:4321
pnpm typecheck      # must be clean before opening a PR
pnpm build          # production build, must succeed
```

For Track A event change detection (requires an authenticated Earth Engine
environment -- `earthengine authenticate` first):

```bash
make event EVENT=carina_2024    # runs fetch_s1_event.py + flood_extent.py for the named event
```

## PR conventions

- Branch naming: `fix/<short-slug>`, `feat/<short-slug>`, `docs/<short-slug>`.
- One logical change per PR. Bundling unrelated changes makes review slow and
  increases the chance of revert.
- Update `CHANGELOG.md` under the `Unreleased` heading with one line describing
  the change.
- If the change touches the deterministic-build chain (requirements pinning,
  `train.py`, `calibrate.py`, embeddings cache): re-run `make hash-verify` and
  update `EXPECTED_HASH` in the Makefile if the hash legitimately moves. Document
  why the hash moved in the PR body.
- If the change affects any CI gate script in `scripts/`, re-run the full gate
  suite (`make verify`) before opening the PR.
- If the change touches flood GeoJSON output, verify `_meta.permanent_water_masked`
  is `true` and `make verify` exits zero.

## Testing expectations

| Change type | Required tests |
|---|---|
| New helper function | Pure-function test in `tests/test_<module>.py` |
| Bug fix | Regression test that fails on the broken code and passes after the fix |
| New event registration | `event/events.json` is valid JSON; `make verify` exits zero |
| Site UI change | `pnpm typecheck` clean and `pnpm build` succeeds; describe browser checks in the PR body |
| Pipeline behavior change | Manual rerun against the cached data; diff against prior output included in PR |

Never silence a failing test by editing the assertion. If the test was wrong, document why in the PR body.

## Code style

- Python: 3.11+, `ruff format`, `ruff check`. No bare `except:` outside of the
  documented urllib-retry shims.
- TypeScript: strict mode, Astro, no `any` in new code unless cast at a library
  boundary.
- Markdown: no em-dashes (use `--`, comma, or period). No AI-jargon listed in the
  project notes. Match the existing tone in `README.md`.

## Reporting a security issue

Do not open a public issue. Use the [GitHub Security Advisory form](https://github.com/xmpuspus/floodwatch-ph/security/advisories/new). See [SECURITY.md](SECURITY.md) for what is in scope.

## Code of conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). Be kind, ask before assuming, no harassment.
