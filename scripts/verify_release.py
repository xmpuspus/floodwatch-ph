"""Full pre-release gate runner for FloodWatch.PH.

Runs every integrity check and prints a numbered checklist with [PASS]/[FAIL]/
[SKIP] tags. Exits 0 only when all gates pass.

Gates:
  1. Event-disjoint holdout (check_event_disjoint.py)
  2. Permanent-water masking (check_permanent_water.py)
  3. No-PII / barangay-aggregate (check_no_pii.py)
  4. site/src/data/events.json byte-identical to event/events.json (decision 4)
  5. requirements.txt fully pinned (all non-comment lines use ==)
  6. recurrence_clf_v1.joblib sha256 prefix (print only; Makefile hash-verify owns hard-fail)

`--gates-only` runs the same gates; the flag is accepted for CI compatibility.

Usage:
    python scripts/verify_release.py
    python scripts/verify_release.py --gates-only
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _gate(n: int, name: str, ok: bool | None, detail: str = "") -> bool:
    if ok is None:
        tag = "SKIP"
    elif ok:
        tag = "PASS"
    else:
        tag = "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"  {n}. [{tag}] {name}{suffix}")
    return bool(ok)


def _run_check(module_path: Path) -> bool:
    """Import a check script and call its main(), return True on exit-code 0."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_check", module_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    rc = mod.main()
    return rc == 0


def gate_event_disjoint() -> bool:
    return _run_check(REPO / "scripts" / "check_event_disjoint.py")


def gate_permanent_water() -> bool:
    return _run_check(REPO / "scripts" / "check_permanent_water.py")


def gate_no_pii() -> bool:
    return _run_check(REPO / "scripts" / "check_no_pii.py")


def gate_events_mirror() -> bool:
    """Assert site/src/data/events.json is byte-identical to event/events.json."""
    canonical = REPO / "event" / "events.json"
    mirror = REPO / "site" / "src" / "data" / "events.json"
    if not canonical.exists():
        print(f"    WARN: {canonical} not found", file=sys.stderr)
        return False
    if not mirror.exists():
        print(f"    WARN: {mirror} not found", file=sys.stderr)
        return False
    return canonical.read_bytes() == mirror.read_bytes()


def gate_requirements_pinned() -> bool:
    """Every non-comment line in requirements.txt must use == (exact pin)."""
    reqs = REPO / "requirements.txt"
    if not reqs.exists():
        print(f"    WARN: {reqs} not found", file=sys.stderr)
        return False
    unpinned: list[str] = []
    for line in reqs.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("-"):
            continue
        if "==" not in s:
            unpinned.append(s)
    if unpinned:
        print(f"    unpinned: {unpinned}", file=sys.stderr)
    return len(unpinned) == 0


def gate_clf_hash() -> tuple[bool | None, str]:
    """Print the clf sha256; return (None, detail) — Makefile hash-verify owns hard-fail."""
    clf = REPO / "model" / "recurrence_clf_v1.joblib"
    if not clf.exists():
        return None, "recurrence_clf_v1.joblib not present (run `make train`)"
    digest = hashlib.sha256(clf.read_bytes()).hexdigest()
    return None, f"sha256 prefix = {digest[:16]} (use `make hash-verify` to assert)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    ap.add_argument(
        "--gates-only",
        action="store_true",
        help="Run in CI gate mode (same checks; flag accepted for compatibility)",
    )
    ap.parse_args(argv)

    print("FloodWatch.PH release gate runner")
    print("=" * 40)

    passes = 0
    fails = 0

    def record(ok: bool | None) -> None:
        nonlocal passes, fails
        if ok is True:
            passes += 1
        elif ok is False:
            fails += 1
        # None = SKIP, not counted as pass or fail

    # Gate 1: event-disjoint
    print("\nRunning gate 1 — event-disjoint holdout...")
    ok1 = gate_event_disjoint()
    record(ok1)
    _gate(1, "event-disjoint holdout", ok1)

    # Gate 2: permanent-water
    print("\nRunning gate 2 — permanent-water masking...")
    ok2 = gate_permanent_water()
    record(ok2)
    _gate(2, "permanent-water masking on flood GeoJSONs", ok2)

    # Gate 3: no-PII
    print("\nRunning gate 3 — no-PII / barangay-aggregate...")
    ok3 = gate_no_pii()
    record(ok3)
    _gate(3, "no PII-adjacent keys in published outputs", ok3)

    # Gate 4: events.json mirror
    ok4 = gate_events_mirror()
    record(ok4)
    detail4 = (
        "byte-identical" if ok4
        else "site/src/data/events.json differs from event/events.json — run: "
             "cp event/events.json site/src/data/events.json"
    )
    _gate(4, "site/src/data/events.json mirrors event/events.json", ok4, detail4)

    # Gate 5: requirements pinned
    ok5 = gate_requirements_pinned()
    record(ok5)
    detail5 = "all lines use ==" if ok5 else "some lines use >=, ^, or ~ (see above)"
    _gate(5, "requirements.txt fully pinned", ok5, detail5)

    # Gate 6: clf hash (informational)
    skip6, detail6 = gate_clf_hash()
    _gate(6, "recurrence_clf_v1.joblib sha256", skip6, detail6)

    print("\n" + "=" * 40)
    print(f"FloodWatch.PH gate summary: {passes} PASS / {fails} FAIL")

    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
