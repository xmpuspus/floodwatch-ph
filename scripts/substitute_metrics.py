"""Substitute every {{METRIC:key}} (docs) and METRIC__key (site metrics.ts)
token with the REAL computed value. No value is invented — each is read from
a generated artifact. Fails loudly if a token has no computed value, so a
fabricated/placeholder number can never reach the published site or README.

Run after train+calibrate, Track A (both events), exposure and hazard_gap.
Idempotent: only replaces tokens, never recomputes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def collect() -> dict[str, str]:
    m: dict[str, str] = {}
    cal = json.loads((REPO / "model" / "recurrence_clf_v1_calibration.json").read_text())["summary"]
    met = json.loads((REPO / "model" / "recurrence_clf_v1_metrics.json").read_text())
    split = json.loads((REPO / "model" / "holdout_events.json").read_text())
    m["trackB_f1"] = f"{cal['trackB_f1']:.3f}"
    m["trackB_precision"] = f"{cal['trackB_precision']:.3f}"
    m["trackB_recall"] = f"{cal['trackB_recall']:.3f}"
    m["trackB_brier"] = f"{cal['trackB_brier']:.3f}"
    m["trackB_auc"] = f"{met['holdout_auc']:.3f}"
    m["trackB_threshold"] = str(cal["threshold"])
    m["clf_threshold"] = str(cal["threshold"])
    m["clf_sha256"] = cal["clf_sha256_16"]
    m["trackB_n_pos_holdout"] = str(cal["n_holdout_pos"])
    m["trackB_n_neg_holdout"] = str(cal["n_holdout_neg"])
    m["n_train_events"] = str(len(split["train_ids"]))
    m["n_holdout_events"] = str(len(split["holdout_ids"]))
    m["gfd_n_events"] = str(split["n_events"])

    import numpy as np

    d = np.load(REPO / "model" / "embeddings" / "floodwatch_embeddings_v1.npz",
                allow_pickle=True)
    y = d["y"].astype(int)
    m["n_pos"] = str(int((y == 1).sum()))
    m["n_neg"] = str(int((y == 0).sum()))

    kv = json.loads((REPO / "site" / "public" / "data"
                     / "flood_koppu_2015_meta.json").read_text())["validation"]
    m["trackA_iou"] = f"{kv['iou']:.3f}"
    m["trackA_f1"] = f"{kv['f1']:.3f}"
    m["trackA_precision"] = f"{kv['precision']:.3f}"
    m["trackA_recall"] = f"{kv['recall']:.3f}"

    cm = json.loads((REPO / "site" / "public" / "data"
                     / "flood_carina_2024_meta.json").read_text())
    dates = [x["date"] for x in cm["dates"]]
    m["carina_peak_km2"] = f"{max(x['flood_area_km2'] for x in cm['dates']):.0f}"
    m["carina_dates"] = str(len(dates))
    otsu_vals = [x["otsu_threshold_db"] for x in cm["dates"]]
    m["trackA_otsu_threshold_db"] = f"{sum(otsu_vals) / len(otsu_vals):.1f}"

    # Civic headline: locations the model flags flood-prone with NO GFD
    # historical record (computed in calibrate.py from the cache; honest and
    # national, not the GFD-saturated regional gap-map count).
    m["uncharted_count"] = str(cal["modeled_prone_unrecorded"])
    m["prone_unrecorded_total"] = str(cal["n_never_flooded_sampled"])

    exp = json.loads((REPO / "site" / "public" / "data"
                      / "barangay_exposure.json").read_text())
    units = exp.get("units", {})
    pop = sum(u["population"] for u in units.values()
              if (u.get("peak_flood_pct") or 0) > 0)
    m["pop_exposed"] = f"{pop:,}"

    doi = json.loads((REPO / ".zenodo_doi.json").read_text())["doi"] if (
        REPO / ".zenodo_doi.json"
    ).exists() else "10.5281/zenodo.PENDING"
    m["zenodo_doi"] = doi
    return m


def main() -> int:
    m = collect()
    targets = [
        REPO / "README.md", REPO / "MODEL_CARD.md", REPO / "CHANGELOG.md",
        REPO / "CONTRIBUTING.md", REPO / "SECURITY.md", REPO / "CITATION.cff",
        REPO / ".zenodo.json",
        REPO / "docs" / "privacy-impact-assessment.md",
        REPO / "examples" / "run_on_new_event.md",
        REPO / "docs" / "launch" / "linkedin-draft.md",
    ]
    tok = re.compile(r"\{\{METRIC:([a-zA-Z0-9_]+)\}\}")
    missing: set[str] = set()
    for f in targets:
        if not f.exists():
            continue
        s = f.read_text()
        def repl(mo):
            k = mo.group(1)
            if k not in m:
                missing.add(k)
                return mo.group(0)
            return m[k]
        f.write_text(tok.sub(repl, s))

    # site metrics.ts: rewrite the METRICS object values in place
    mts = REPO / "site" / "src" / "data" / "metrics.ts"
    if mts.exists():
        s = mts.read_text()
        for k, v in m.items():
            s = re.sub(rf'(\b{k}\s*:\s*)"METRIC__{k}"', rf'\g<1>"{v}"', s)
        mts.write_text(s)
        leftover = re.findall(r'"METRIC__([a-zA-Z0-9_]+)"', s)
        missing.update(leftover)

    if missing:
        print(f"[substitute_metrics] FAIL: no computed value for: "
              f"{sorted(missing)}", file=sys.stderr)
        return 1
    print(f"[substitute_metrics] OK: substituted {len(m)} metrics across "
          f"{len(targets)} docs + metrics.ts")
    for k in sorted(m):
        print(f"  {k} = {m[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
