"""FloodWatch.PH — open flood-extent measurement + recurrence-prone classifier.

Two tracks (see docs/research/floodwatch-spec.md):
  - Track A (event): Sentinel-1 SAR change-detection flood extent.
  - Track B (model): frozen AlphaEarth embeddings + calibrated sklearn head.
"""

__version__ = "1.0.0"
