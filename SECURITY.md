# Security Policy

## Reporting a vulnerability

Open a private security advisory via the GitHub Security tab:
https://github.com/xmpuspus/floodwatch-ph/security/advisories/new

Do not open a public issue. Acknowledged within 5 working days.

## In scope

- Code execution via crafted inputs to any script in `event/`, `model/`, `pipeline/`, or `scripts/`.
- Cross-site scripting on `floodwatch.ph` or any deployed preview.
- CSP bypass on the site.
- Path traversal in any file-cache or output-path lookup.
- Supply-chain issues against the pinned dependencies in `requirements.txt` and `pipeline/requirements.txt`.

## Out of scope

- Vulnerabilities in third-party services we call (Google Earth Engine, Copernicus Open Access Hub, WorldPop, OpenStreetMap Overpass, Vercel). Report to the upstream operator.
- Social engineering, phishing, physical attacks.

## Known-safe-by-design surfaces

- The FloodWatch.PH site is a static Astro build deployed to Vercel. No server-side handler processes user input at runtime. No database is exposed.
- The Earth Engine pipeline runs locally with a service-account key or interactive user auth. The key never enters Vercel, never enters git history. `.gitignore` and `.dockerignore` block common credential naming patterns.
- Barangay exposure data is pre-aggregated before publication. The site does not perform spatial joins at request time.

## joblib / pickle deserialization

`model/train.py` and `model/calibrate.py` write `recurrence_clf_v1.joblib`, and
`scripts/verify_clf.py` is used to load it. `joblib.load` is built on Python's
pickle module, which executes arbitrary code during deserialization.

**Only run `joblib.load` against classifier files you trust.** The shipped
`model/recurrence_clf_v1.joblib` is verifiable via `make hash-verify` (sha256
`b7c702532f92c43f`). If you fork the repo and someone sends you a classifier
file, verify its sha256 against a known-good source before invoking any `make` target
that loads it. `scripts/verify_clf.py` provides a convenience wrapper that exits
non-zero if the hash does not match before calling `joblib.load`.

## Data publication boundaries

Published flood extent and recurrence outputs are aggregated to barangay level. No
per-dwelling geometry, no household identifiers, no PII property keys appear in any
published GeoJSON. CI gate `scripts/check_no_pii.py` enforces this and exits non-zero
on any violation; the release gate (`make verify`) runs it before every publication.

Flood-extent polygon features identify only the date and event key, not any property
that could re-identify a dwelling.

If you observe a feature in the published dataset that appears to identify a specific
household or dwelling, open a private advisory immediately using the link above. See
also the takedown channel in `docs/privacy-impact-assessment.md`.
