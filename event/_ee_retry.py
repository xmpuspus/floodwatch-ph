"""Earth Engine reliability helpers (audit-mandated).

The current pipeline silently ships empty data when EE init or a getInfo call
fails transiently. These wrappers add bounded exponential backoff + jitter and
re-auth on auth-type errors so a single flaky network call cannot turn into a
blank-map lie. Used only by the near-real-time `flood_latest` path; the locked
event/flood_extent.py path is untouched.
"""

from __future__ import annotations

import random
import time

# Substrings that mean "the credentials went bad", not "the network blipped".
# On these we re-init EE before retrying rather than just sleeping.
_AUTH_MARKERS = (
    "credential",
    "unauthorized",
    "permission",
    "401",
    "403",
    "invalid_grant",
    "token",
    "authenticate",
)

MAX_TRIES = 4
BASE_DELAY = 2.0   # seconds; delay = BASE_DELAY * 2**attempt + jitter
MAX_DELAY = 30.0


def _is_auth_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _AUTH_MARKERS)


def ee_init_retry(init_fn):
    """Call init_fn() (returns the ee module) with retry/backoff.

    init_fn is floodwatch_ph.eeauth.init_ee. Raised only if all tries fail.
    """
    last = None
    for attempt in range(MAX_TRIES):
        try:
            return init_fn()
        except Exception as exc:  # noqa: BLE001 — bounded retry is the point
            last = exc
            if attempt == MAX_TRIES - 1:
                break
            delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY) + random.uniform(
                0, 1.0
            )
            print(
                f"[ee_retry] init failed (try {attempt + 1}/{MAX_TRIES}): "
                f"{exc!r}; retrying in {delay:.1f}s"
            )
            time.sleep(delay)
    raise RuntimeError(f"EE init failed after {MAX_TRIES} tries: {last!r}")


def get_info_retry(ee_object, init_fn=None, label: str = "getInfo"):
    """`.getInfo()` with bounded exponential backoff + jitter.

    On an auth-type error and if init_fn is given, re-init EE (refreshes the
    service-account token) before the next try. Returns the getInfo payload or
    raises RuntimeError after MAX_TRIES.
    """
    last = None
    for attempt in range(MAX_TRIES):
        try:
            return ee_object.getInfo()
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt == MAX_TRIES - 1:
                break
            if _is_auth_error(exc) and init_fn is not None:
                try:
                    init_fn()
                    print(f"[ee_retry] {label}: re-authenticated after auth error")
                except Exception as reinit:  # noqa: BLE001
                    print(f"[ee_retry] {label}: re-auth failed: {reinit!r}")
            delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY) + random.uniform(
                0, 1.0
            )
            print(
                f"[ee_retry] {label} failed (try {attempt + 1}/{MAX_TRIES}): "
                f"{exc!r}; retrying in {delay:.1f}s"
            )
            time.sleep(delay)
    raise RuntimeError(f"{label} failed after {MAX_TRIES} tries: {last!r}")
