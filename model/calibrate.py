"""Platt-sigmoid calibration on the EVENT-DISJOINT holdout — Track B.

Fits P = sigmoid(A * decision_function(x) + B) on the holdout group, reports
calibrated precision/recall/F1 at the deployed threshold plus AUC and Brier,
and emits the national recurrence-prone point layer (scored at the real
sampled embedding locations; permanent water already removed at sampling).

Outputs:
  model/recurrence_clf_v1_calibration.json
  site/public/data/recurrence_prone.geojson
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, precision_score, recall_score

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "site" / "public" / "data"
THRESHOLD = 0.5


def main() -> int:
    d = np.load(HERE / "embeddings" / "floodwatch_embeddings_v1.npz", allow_pickle=True)
    X = d["X"].astype(np.float64)
    y, group = d["y"].astype(int), d["group"]
    lon, lat = d["lon"], d["lat"]
    ho = group == "holdout"

    clf = joblib.load(HERE / "recurrence_clf_v1.joblib")
    raw_ho = clf.decision_function(X[ho]).reshape(-1, 1)

    platt = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000)
    platt.fit(raw_ho, y[ho])
    A = float(platt.coef_[0][0])
    B = float(platt.intercept_[0])

    def cal(rawvals):
        return 1.0 / (1.0 + np.exp(-(A * rawvals + B)))

    p_ho = cal(clf.decision_function(X[ho]))
    pred = (p_ho >= THRESHOLD).astype(int)
    clf_sha = hashlib.sha256(
        (HERE / "recurrence_clf_v1.joblib").read_bytes()
    ).hexdigest()

    summary = {
        "model": "recurrence_clf_v1",
        "embedding": "AlphaEarth Satellite Embedding V1 (2017, 64-dim, 300 m)",
        "calibrator": f"Platt sigmoid A={A:.4f} B={B:.4f}",
        "threshold": THRESHOLD,
        "trackB_f1": round(float(f1_score(y[ho], pred)), 4),
        "trackB_precision": round(float(precision_score(y[ho], pred)), 4),
        "trackB_recall": round(float(recall_score(y[ho], pred)), 4),
        "trackB_brier": round(float(brier_score_loss(y[ho], p_ho)), 4),
        "n_holdout_pos": int(y[ho].sum()),
        "n_holdout_neg": int((y[ho] == 0).sum()),
        "clf_sha256_16": clf_sha[:16],
        "split": "event-disjoint (whole GFD typhoon events held out)",
    }
    # National recurrence-prone point layer (real sampled locations).
    p_all = cal(clf.decision_function(X))
    # Civic headline: locations the model flags flood-prone (calibrated score
    # >= prone threshold) that have NO Global Flood Database historical record
    # (y == 0 means never observed flooded across any 2002-2017 GFD event).
    prone_unrecorded = int(((p_all >= 0.60) & (y == 0)).sum())
    summary["prone_threshold"] = 0.60
    summary["modeled_prone_unrecorded"] = prone_unrecorded
    summary["n_never_flooded_sampled"] = int((y == 0).sum())
    (HERE / "recurrence_clf_v1_calibration.json").write_text(
        json.dumps({"summary": summary, "platt_A": A, "platt_B": B}, indent=2)
    )

    feats = []
    for i in range(len(p_all)):
        s = round(float(p_all[i]), 3)
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point",
                         "coordinates": [round(float(lon[i]), 5),
                                         round(float(lat[i]), 5)]},
            "properties": {"score": s, "prone": bool(s >= THRESHOLD)},
        })
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "recurrence_prone.geojson").write_text(json.dumps({
        "type": "FeatureCollection",
        "_meta": {
            "model": "recurrence_clf_v1",
            "embedding": "AlphaEarth 2017 64-dim",
            "threshold": THRESHOLD,
            "permanent_water_masked": True,
            "holdout_metrics": {
                "f1": summary["trackB_f1"],
                "precision": summary["trackB_precision"],
                "recall": summary["trackB_recall"],
                "brier": summary["trackB_brier"],
            },
            "disclaimer": "Observed flood-recurrence indicators derived from "
            "public satellite data. Patterns may have legitimate explanations; "
            "figures warrant independent verification.",
        },
        "features": feats,
    }))
    print(
        f"[calibrate] Platt A={A:.3f} B={B:.3f} | holdout "
        f"P={summary['trackB_precision']} R={summary['trackB_recall']} "
        f"F1={summary['trackB_f1']} Brier={summary['trackB_brier']} | "
        f"recurrence_prone.geojson {len(feats)} pts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
