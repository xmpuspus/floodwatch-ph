"""FloodWatch.PH near-real-time rainfall CONTEXT layer.

This is NOT a flood forecast and NOT a flood score. It is a labeled context
flag: GPM IMERG rainfall accumulation over the EXISTING modeled flood-prone
areas (Track B), as of the latest available IMERG timestamp. It bridges the
Sentinel-1 revisit gap (6-12 day SAR cadence) by reporting how much rain has
fallen over already-known prone areas since the last possible SAR pass.

For flood/typhoon warnings always use PAGASA.
"""

from __future__ import annotations

__all__ = ["ee_retry", "fetch_gpm", "current_risk"]
