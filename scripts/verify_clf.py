"""Verify a classifier joblib against a canonical sha256 prefix.

Wraps the hash-verify logic from `make hash-verify`. Use this before invoking
any `joblib.load`-based code on a classifier file received from a third party.
`joblib.load` is built on pickle and executes arbitrary code during
deserialization — never load without verifying.

Usage:
    python scripts/verify_clf.py model/recurrence_clf_v1.joblib
    python scripts/verify_clf.py model/recurrence_clf_v1.joblib abc123def456

Exit code 0 = hash matches (or no expected prefix given), 1 = mismatch or
file missing.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    p.add_argument("path", type=Path, help="path to a classifier .joblib file")
    p.add_argument(
        "expected_prefix",
        nargs="?",
        default=None,
        help="sha256 prefix to assert (optional; if omitted, just prints the hash)",
    )
    args = p.parse_args(argv)

    if not args.path.exists():
        print(f"[verify_clf] FAIL: {args.path} not found", file=sys.stderr)
        return 1

    digest = sha256_file(args.path)

    if args.expected_prefix is None:
        print(f"[verify_clf] {args.path}")
        print(f"  full sha256:   {digest}")
        print(f"  prefix (16):   {digest[:16]}")
        print("  No expected prefix provided — not asserting. Safe to inspect.")
        return 0

    prefix_len = len(args.expected_prefix)
    actual_prefix = digest[:prefix_len]

    if actual_prefix.lower() != args.expected_prefix.lower():
        print(
            f"[verify_clf] FAIL: hash mismatch for {args.path}",
            file=sys.stderr,
        )
        print(f"  expected prefix: {args.expected_prefix}", file=sys.stderr)
        print(f"  observed prefix: {actual_prefix}", file=sys.stderr)
        print(f"  full sha256:     {digest}", file=sys.stderr)
        print(
            "  DO NOT run joblib.load against this file. "
            "Pickle deserialization executes arbitrary code.",
            file=sys.stderr,
        )
        return 1

    print(f"[verify_clf] OK: {args.path}")
    print(f"  sha256 prefix:   {actual_prefix} (matches {args.expected_prefix})")
    print(f"  full sha256:     {digest}")
    print("  Safe to invoke joblib.load on this file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
