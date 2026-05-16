"""EE reliability helper: retry with exponential backoff + jitter.

Wraps both EE init and any client-materialization call (.getInfo()). On
auth-class errors it re-initializes the EE session before the next try.
Audit-mandated: max ~4 tries, backoff + jitter, auth refresh on auth errors.
"""

from __future__ import annotations

import random
import sys
import time
from typing import Callable, TypeVar

T = TypeVar("T")

_AUTH_MARKERS = (
    "authoriz",
    "credential",
    "unauthenticated",
    "permission",
    "invalid_grant",
    "token",
    "401",
    "403",
)


def _is_auth_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _AUTH_MARKERS)


def init_ee_retry(max_tries: int = 4, base: float = 2.0):
    """Initialize Earth Engine with retry/backoff. Returns the ee module."""
    sys.path.insert(0, ".")
    from floodwatch_ph.eeauth import init_ee

    last: Exception | None = None
    for attempt in range(1, max_tries + 1):
        try:
            return init_ee()
        except Exception as exc:  # noqa: BLE001 — surface after retries
            last = exc
            if attempt == max_tries:
                break
            sleep = base ** attempt + random.uniform(0, 1.0)
            print(
                f"[ee_retry] init attempt {attempt}/{max_tries} failed: {exc!r}; "
                f"retrying in {sleep:.1f}s",
                file=sys.stderr,
            )
            time.sleep(sleep)
    raise RuntimeError(f"EE init failed after {max_tries} tries: {last!r}")


def get_info(thunk: Callable[[], T], max_tries: int = 4, base: float = 2.0) -> T:
    """Run a .getInfo()-style thunk with retry/backoff + jitter.

    `thunk` is a zero-arg callable that performs the EE client materialization
    (e.g. ``lambda: img.reduceRegion(...).getInfo()``). On auth-class failures
    the EE session is re-initialized before the next attempt.
    """
    last: Exception | None = None
    for attempt in range(1, max_tries + 1):
        try:
            return thunk()
        except Exception as exc:  # noqa: BLE001 — surface after retries
            last = exc
            if attempt == max_tries:
                break
            if _is_auth_error(exc):
                print(
                    f"[ee_retry] auth-class error on attempt {attempt}; "
                    "refreshing EE session",
                    file=sys.stderr,
                )
                try:
                    init_ee_retry(max_tries=2)
                except Exception as reinit:  # noqa: BLE001
                    print(f"[ee_retry] re-init failed: {reinit!r}", file=sys.stderr)
            sleep = base ** attempt + random.uniform(0, 1.0)
            print(
                f"[ee_retry] getInfo attempt {attempt}/{max_tries} failed: "
                f"{exc!r}; retrying in {sleep:.1f}s",
                file=sys.stderr,
            )
            time.sleep(sleep)
    raise RuntimeError(f"EE getInfo failed after {max_tries} tries: {last!r}")
