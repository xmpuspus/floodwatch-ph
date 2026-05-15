"""Pure-numpy Otsu threshold tests — no earthengine import.

event/flood_extent.py uses Earth Engine server-side Otsu, so we cannot import
it in CI (no EE credentials). Instead this module:

  1. Implements a minimal pure-numpy Otsu reference.
  2. Tests it against synthetic bimodal histograms where the valley location
     is known analytically.

This validates the algorithm in isolation without touching any EE code path.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Minimal pure-numpy Otsu implementation (reference, not the EE version)
# ---------------------------------------------------------------------------

def otsu_threshold(values: np.ndarray) -> float:
    """Return the Otsu threshold for a 1-D array of float values.

    Uses the standard between-class variance maximisation over a fixed
    256-bin histogram. Works on any finite float array.
    """
    if len(values) == 0:
        raise ValueError("otsu_threshold: empty input array")

    vmin, vmax = float(values.min()), float(values.max())
    if vmin == vmax:
        return vmin

    counts, bin_edges = np.histogram(values, bins=256)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    total = counts.sum()
    if total == 0:
        return float(bin_centers[0])

    probs = counts / total
    cumsum_probs = np.cumsum(probs)
    cumsum_means = np.cumsum(probs * bin_centers)

    global_mean = cumsum_means[-1]
    w0 = cumsum_probs
    w1 = 1.0 - cumsum_probs

    mu0 = np.where(w0 > 0, cumsum_means / np.where(w0 > 0, w0, 1), 0.0)
    mu1 = np.where(w1 > 0, (global_mean - cumsum_means) / np.where(w1 > 0, w1, 1), 0.0)

    between_var = w0 * w1 * (mu0 - mu1) ** 2

    best_idx = int(np.argmax(between_var))
    return float(bin_centers[best_idx])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _bimodal(n: int, mu1: float, mu2: float, sigma: float = 1.0, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    half = n // 2
    a = rng.normal(mu1, sigma, half)
    b = rng.normal(mu2, sigma, n - half)
    return np.concatenate([a, b])


def test_otsu_bimodal_valley_between_modes():
    """Threshold must fall between the two mode centres."""
    mu1, mu2 = -5.0, 5.0
    data = _bimodal(10_000, mu1, mu2, sigma=1.0)
    t = otsu_threshold(data)
    assert mu1 < t < mu2, f"threshold {t:.3f} is not between the two modes {mu1} and {mu2}"


def test_otsu_threshold_near_midpoint():
    """For a balanced bimodal with equal variance the threshold should be near the midpoint."""
    mu1, mu2 = -3.0, 3.0
    midpoint = (mu1 + mu2) / 2.0  # 0.0
    data = _bimodal(20_000, mu1, mu2, sigma=0.8)
    t = otsu_threshold(data)
    assert abs(t - midpoint) < 1.0, (
        f"threshold {t:.3f} is too far from midpoint {midpoint:.3f}"
    )


def test_otsu_asymmetric_bimodal():
    """Works on an asymmetric bimodal (different heights do not trip the algorithm)."""
    rng = np.random.default_rng(7)
    low_class = rng.normal(-10, 1.5, 3000)   # smaller cluster
    high_class = rng.normal(10, 2.0, 9000)   # larger cluster
    data = np.concatenate([low_class, high_class])
    t = otsu_threshold(data)
    assert -10 < t < 10, f"threshold {t:.3f} not between -10 and 10"


def test_otsu_single_value_array():
    """A constant array returns that constant without crashing."""
    data = np.full(100, 3.14)
    t = otsu_threshold(data)
    assert t == 3.14


def test_otsu_output_is_float():
    data = _bimodal(1000, 0.0, 10.0)
    t = otsu_threshold(data)
    assert isinstance(t, float)


def test_otsu_separates_classes():
    """Applying the threshold to the bimodal data should classify > 90% correctly."""
    mu1, mu2 = -4.0, 4.0
    data = _bimodal(10_000, mu1, mu2, sigma=0.9, seed=42)
    labels_true = np.array([0] * 5000 + [1] * 5000)
    t = otsu_threshold(data)
    predicted = (data >= t).astype(int)
    acc = float(np.mean(predicted == labels_true))
    assert acc > 0.90, f"classification accuracy {acc:.3f} < 0.90"
