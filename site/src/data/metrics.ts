// Metric placeholder tokens. Post-build substitution replaces these with
// Real computed values, substituted post-build by scripts/substitute_metrics.py.
// The real generator overwrites these values.

export const METRICS = {
  trackA_iou:        "0.054",
  trackA_precision:  "0.084",
  trackA_recall:     "0.053",
  trackA_f1:         "0.065",
  trackB_f1:         "0.955",
  trackB_precision:  "0.949",
  trackB_recall:     "0.962",
  trackB_threshold:  "0.5",
  clf_sha256:        "b7c702532f92c43f",
  carina_peak_km2:   "184",
  uncharted_count:   "337",
  pop_exposed:       "8,104,380",
} as const;
