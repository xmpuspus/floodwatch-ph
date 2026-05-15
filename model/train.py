"""Train the FloodWatch.PH recurrence head — Track B.

Deterministic. Reads the COMMITTED embeddings cache (the frozen substrate,
exactly like SolarMap's dataset_v4.npz), trains a LogisticRegression head on
the TRAIN event-disjoint group only, and evaluates on the HOLDOUT group.
No network, no GPU, ~1 s. joblib bytes are bit-exact across Linux/macOS at
the pinned scikit-learn / joblib / numpy versions (see requirements.txt).

Outputs:
  model/recurrence_clf_v1.joblib         base classifier (hash-verified)
  model/recurrence_clf_v1_metrics.json   raw holdout metrics
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

HERE = Path(__file__).resolve().parent


def main() -> int:
    d = np.load(HERE / "embeddings" / "floodwatch_embeddings_v1.npz", allow_pickle=True)
    X, y, group = d["X"].astype(np.float64), d["y"].astype(int), d["group"]
    tr = group == "train"
    ho = group == "holdout"

    clf = LogisticRegression(
        C=1.0, class_weight="balanced", max_iter=2000, random_state=42
    )
    clf.fit(X[tr], y[tr])
    joblib.dump(clf, HERE / "recurrence_clf_v1.joblib")

    raw = clf.decision_function(X[ho])
    pred = (raw > 0).astype(int)
    metrics = {
        "n_train": int(tr.sum()),
        "n_holdout": int(ho.sum()),
        "n_holdout_pos": int(y[ho].sum()),
        "n_holdout_neg": int((y[ho] == 0).sum()),
        "holdout_f1_raw": round(float(f1_score(y[ho], pred)), 4),
        "holdout_precision_raw": round(float(precision_score(y[ho], pred)), 4),
        "holdout_recall_raw": round(float(recall_score(y[ho], pred)), 4),
        "holdout_auc": round(float(roc_auc_score(y[ho], raw)), 4),
        "holdout_ap": round(float(average_precision_score(y[ho], raw)), 4),
        "classifier": "LogisticRegression(C=1.0, class_weight=balanced, "
        "max_iter=2000, random_state=42)",
        "embedding": "AlphaEarth Satellite Embedding V1, 2017, 64-dim, 300 m",
        "split": "event-disjoint (whole GFD typhoon events held out)",
    }
    (HERE / "recurrence_clf_v1_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(
        f"[train] holdout AUC={metrics['holdout_auc']} "
        f"raw F1={metrics['holdout_f1_raw']} "
        f"(n_train={metrics['n_train']}, n_holdout={metrics['n_holdout']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
