"""Deploy the built site to Vercel, RE-ALIAS the public domain, verify the
LIVE alias, and roll back + page on failure.

WHY THIS EXISTS (the locked gotcha)
-----------------------------------
`vercel deploy --prod` creates a NEW immutable deployment URL. It does NOT
automatically repoint the project's public alias (e.g.
floodwatch-ph.vercel.app) at that new deployment unless the project is wired
for it. The product audit ranked "deploy without re-alias" the single
highest-likelihood incident: CI goes green, a fresh deployment exists, but the
public URL still serves the OLD build. This script makes the re-alias an
explicit, verified step.

FLOW
----
1. `vercel pull`            — sync project settings (non-secret).
2. `vercel build --prod`    — produce .vercel/output.
3. `vercel deploy --prebuilt --prod`  — upload, capture the new deployment URL.
4. `vercel alias set <newUrl> <publicDomain>`  — REPOINT the public alias.
5. Verify the LIVE alias with scripts/qa_live.py (real behavioral QA, not 200).
6. On verify failure:
     a. Re-alias the public domain back to the previous known-good deployment.
     b. Open a GitHub issue (the pager) with the failing detail.
     c. Exit non-zero so the workflow is red.

The "previous known-good deployment" is read from `vercel ls` BEFORE we deploy
(the current production deployment the alias points at). We stash it so a
failed new deploy can be reverted without guessing.

CREDENTIALS
-----------
All read from the environment (the workflow injects them from GitHub secrets):
  VERCEL_TOKEN       project-scoped token, deploy + alias scope only
  VERCEL_ORG_ID      team/org id (from site/.vercel/project.json if unset)
  VERCEL_PROJECT_ID  project id (from site/.vercel/project.json if unset)
  GITHUB_TOKEN       for the issue pager (Actions-provided; issues:write)
  GITHUB_REPOSITORY  "owner/repo" (Actions-provided)
Nothing is ever echoed.

Usage (from repo root):
    python scripts/deploy_realias.py \
        --site-dir site \
        --public-domain floodwatch-ph.vercel.app \
        [--skip-verify]        # build+deploy+alias only, no live QA
        [--dry-run]            # print the commands, touch nothing
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_URL_RE = re.compile(r"https://[a-z0-9.\-]+\.vercel\.app", re.I)


def _vercel_base(args: argparse.Namespace) -> list[str]:
    """Common `vercel` invocation with token + scope. Token never logged."""
    cmd = ["vercel", "--token", os.environ.get("VERCEL_TOKEN", "")]
    org = os.environ.get("VERCEL_ORG_ID")
    if org:
        cmd += ["--scope", org]
    return cmd


def _run(cmd: list[str], cwd: Path, *, dry: bool, capture: bool = True) -> str:
    """Run a command. Logs an arg-masked form so the token never appears."""
    masked = []
    skip = False
    for a in cmd:
        if skip:
            masked.append("***")
            skip = False
            continue
        masked.append(a)
        if a == "--token":
            skip = True
    print(f"  $ {' '.join(masked)}  (cwd={cwd})")
    if dry:
        return ""
    res = subprocess.run(
        cmd, cwd=str(cwd), text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    out = res.stdout or ""
    if capture and out:
        # Echo output but never print a line that could carry the token (we
        # never pass the token in stdout-bearing positions, but be safe).
        print("\n".join("    " + ln for ln in out.splitlines()[-25:]))
    if res.returncode != 0:
        raise RuntimeError(f"command failed (rc={res.returncode}): {' '.join(masked)}")
    return out


def _current_prod_url(args: argparse.Namespace, site: Path, dry: bool) -> str | None:
    """The deployment the public alias currently points at — our rollback target."""
    try:
        out = _run(_vercel_base(args) + ["ls", "--prod", "--yes"], site, dry=dry)
    except Exception as e:  # noqa: BLE001
        print(f"  [WARN] could not list current prod deployment: {e}")
        return None
    m = _URL_RE.search(out or "")
    return m.group(0) if m else None


def _deploy(args: argparse.Namespace, site: Path, dry: bool) -> str:
    _run(_vercel_base(args) + ["pull", "--yes", "--environment=production"],
         site, dry=dry)
    # `vercel build` reuses a cached .vercel/output and Astro reuses dist/ and
    # .astro/, so a source change can build locally yet ship the OLD bundle
    # (HTTP 200 and __fwReady still pass because they exist in the stale JS;
    # only the content-hash in the script src reveals it). Clear them so every
    # refresh deploys the code that is actually on disk.
    if not dry:
        for stale in (".vercel/output", "dist", ".astro", "node_modules/.vite"):
            shutil.rmtree(site / stale, ignore_errors=True)
    _run(_vercel_base(args) + ["build", "--prod"], site, dry=dry)
    out = _run(_vercel_base(args) + ["deploy", "--prebuilt", "--prod", "--yes"],
               site, dry=dry)
    if dry:
        return "https://dry-run.vercel.app"
    m = _URL_RE.search(out or "")
    if not m:
        raise RuntimeError("could not parse new deployment URL from vercel deploy output")
    url = m.group(0)
    print(f"  new deployment: {url}")
    return url


def _alias(args: argparse.Namespace, site: Path, target_url: str,
           domain: str, dry: bool) -> None:
    print(f"  RE-ALIAS {domain} -> {target_url}")
    _run(_vercel_base(args) + ["alias", "set", target_url, domain], site, dry=dry)


_ASTRO_JS_RE = re.compile(r'/_astro/[A-Za-z0-9._-]+\.js')


def _verify_bundle_fresh(base: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    """Confirm the SERVED bundle is the new code, not a stale Vercel cache.

    HTTP 200 and the JS readiness flags both still passed on the stale bundle
    in the v1.1.0 incident — the only reliable tell was the content of the
    hashed _astro script actually served. So fetch the live HTML and its
    _astro JS and require a marker unique to the new code to be present. A
    miss means `vercel build` shipped a cached old bundle; fail so the caller
    rolls back and pages instead of declaring a stale deploy good.
    """
    try:
        html = urllib.request.urlopen(base, timeout=30).read().decode(
            "utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return False, f"could not fetch live HTML for bundle check: {e!r}"
    scripts = sorted(set(_ASTRO_JS_RE.findall(html)))
    if not scripts:
        return False, "no _astro/*.js in served HTML (unexpected build output)"
    haystack = html
    for path in scripts[:12]:
        try:
            haystack += urllib.request.urlopen(
                base + path, timeout=30).read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
    missing = [m for m in markers if m not in haystack]
    if missing:
        return False, (
            f"served bundle is STALE: marker(s) {missing!r} absent from the "
            f"live HTML + {len(scripts)} _astro script(s). vercel build "
            f"shipped a cached old bundle.")
    return True, f"served bundle fresh ({len(scripts)} _astro scripts checked)"


def _verify_live(domain: str, dry: bool) -> tuple[bool, str]:
    if dry:
        return True, "dry-run"
    base = f"https://{domain}"
    try:
        code = urllib.request.urlopen(base, timeout=30).status
    except Exception as e:  # noqa: BLE001
        return False, f"alias unreachable: {e!r}"
    if code != 200:
        return False, f"alias HTTP {code}"
    # Stale-cache detection (v1.1.0 incident): a marker unique to the current
    # code must be in the actually-served bundle, not just HTTP 200 / a
    # readiness flag that predates the change. __fwCorridor lives only on the
    # /map bundle, so checking it against the homepage always failed; the v1.5
    # AccountabilitySurface sets __fwAccountability on the homepage itself.
    fresh_ok, fresh_detail = _verify_bundle_fresh(base, ("__fwAccountability",))
    print(f"  bundle freshness: {fresh_detail}")
    if not fresh_ok:
        return False, fresh_detail
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "qa_live.py"), base],
        text=True, capture_output=True,
    )
    tail = "\n".join((res.stdout or "").splitlines()[-12:])
    print(tail)
    return res.returncode == 0, tail[-600:]


def _open_pager_issue(title: str, body: str) -> None:
    """Open a GitHub issue as the pager. Best-effort; never raises."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        print("  [WARN] GITHUB_REPOSITORY/GITHUB_TOKEN unset — pager issue skipped")
        return
    payload = json.dumps(
        {"title": title, "body": body, "labels": ["ops", "refresh-failure"]}
    ).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=payload, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "floodwatch-refresh-pager",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            num = json.loads(r.read()).get("number")
            print(f"  pager: opened GitHub issue #{num}")
    except Exception as e:  # noqa: BLE001
        print(f"  [WARN] pager issue failed to open: {e!r}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deploy + re-alias + verify + rollback")
    ap.add_argument("--site-dir", default="site")
    ap.add_argument("--public-domain", default="floodwatch-ph.vercel.app")
    ap.add_argument("--skip-verify", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    site = (REPO / args.site_dir).resolve()
    dry = args.dry_run
    domain = args.public_domain

    if not dry and not os.environ.get("VERCEL_TOKEN"):
        print("ERROR: VERCEL_TOKEN not set in environment.")
        return 2

    print("=== FloodWatch.PH deploy + re-alias ===")
    print(f"site={site} domain={domain} dry_run={dry}")

    prev = _current_prod_url(args, site, dry)
    print(f"  rollback target (current prod): {prev or 'UNKNOWN'}")

    try:
        new_url = _deploy(args, site, dry)
        _alias(args, site, new_url, domain, dry)
    except Exception as e:  # noqa: BLE001
        msg = f"deploy/alias step failed before going live: {e}"
        print(f"\nRESULT: FAIL — {msg}")
        _open_pager_issue(
            "FloodWatch refresh: deploy/alias FAILED",
            f"The scheduled refresh failed during deploy or alias.\n\n"
            f"```\n{msg}\n```\n\n"
            f"Public alias `{domain}` is unchanged (still the previous "
            f"deployment {prev or 'unknown'}). No bad data went live. "
            f"See the runbook: docs/ops/runbook.md.\n\nReviewed by Xavier Puspus",
        )
        return 1

    if args.skip_verify:
        print("\nRESULT: PASS (verify skipped by flag).")
        return 0

    ok, detail = _verify_live(domain, dry)
    if ok:
        print(f"\nRESULT: PASS — {domain} live and verified at {new_url}")
        return 0

    # Live verification failed — do NOT leave a broken alias.
    print(f"\n[ROLLBACK] live verification failed: {detail[:200]}")
    if prev:
        try:
            _alias(args, site, prev, domain, dry)
            print(f"  rolled back: {domain} -> {prev}")
            rb = f"rolled back to previous good deployment {prev}"
        except Exception as e:  # noqa: BLE001
            rb = f"ROLLBACK ALSO FAILED: {e!r} — manual re-alias required"
            print(f"  [CRITICAL] {rb}")
    else:
        rb = ("no known previous deployment to roll back to — public alias may "
              "be serving the bad deploy; MANUAL re-alias required")
        print(f"  [CRITICAL] {rb}")

    _open_pager_issue(
        "FloodWatch refresh: LIVE verification FAILED — rolled back",
        f"The new deployment `{new_url}` failed live QA after re-alias.\n\n"
        f"Action taken: {rb}.\n\n"
        f"qa_live.py tail:\n```\n{detail}\n```\n\n"
        f"Runbook: docs/ops/runbook.md (rollback + manual re-alias steps).\n\n"
        f"Reviewed by Xavier Puspus",
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
