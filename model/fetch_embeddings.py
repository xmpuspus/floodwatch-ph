"""Sample frozen AlphaEarth (2017, 64-dim) embeddings at GFD flood-recurrence
labelled points and write the committed model cache.

EVENT-DISJOINT BY CONSTRUCTION (locked decision 1). Three server-side reduced
masks, three sampled point sets — no per-pixel split, no straddle:

  train_sum = sum over TRAIN GFD events of (flooded AND NOT perm-water)
  hold_sum  = sum over HOLDOUT GFD events of (flooded AND NOT perm-water)

  positive (train)  = train_sum >= 1 AND hold_sum == 0
  positive (holdout)= hold_sum  >= 1 AND train_sum == 0
  negative          = land AND never flooded across ALL events

Points flooded in BOTH a train and a holdout event are dropped (ambiguous) so
no point can leak across the boundary. Permanent water is removed from every
event footprint first (locked decision 2 — report flood, not rivers).

Recurrence is an AREA property; AlphaEarth is sampled at 300 m (the embedding
is mean-aggregated over the cell) which is appropriate for a flood-prone
classifier and keeps the pull fast and reproducible. This is stated in the
model card.

Output: model/embeddings/floodwatch_embeddings_v1.npz
  X (n,64) float32  y (n,) int8  group (n,) <U7  lon/lat (n,) float64
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from floodwatch_ph.eeauth import PH_BBOX, init_ee  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "embeddings" / "floodwatch_embeddings_v1.npz"
EMB_YEAR = 2017
SCALE = 300  # m — flood-recurrence is an area property; fast + reproducible
N_POS_TRAIN = 4500
N_POS_HOLD = 2200
N_NEG = 4500  # each call stays under EE's 5000-element getInfo abort
BANDS = [f"A{i:02d}" for i in range(64)]


def _recur_sum(ee, gfd, ids):
    col = gfd.filter(ee.Filter.inList("id", ids))
    return (
        col.map(
            lambda im: im.select("flooded").eq(1).And(im.select("jrc_perm_water").eq(0))
        )
        .sum()
        .unmask(0)
    )


def _sample(ee, ae, mask, region, n, seed):
    cls = mask.rename("cls")
    fc = (
        ae.addBands(cls)
        .stratifiedSample(
            numPoints=0,
            classBand="cls",
            region=region,
            scale=SCALE,
            seed=seed,
            classValues=[1],
            classPoints=[n],
            dropNulls=True,
            tileScale=8,
            geometries=True,
        )
        .getInfo()
    )
    rows = []
    for ft in fc["features"]:
        pr = ft["properties"]
        vec = [pr.get(b) for b in BANDS]
        if any(v is None for v in vec):
            continue
        lon, lat = ft["geometry"]["coordinates"]
        rows.append((vec, lon, lat))
    return rows


def main() -> int:
    ee = init_ee()
    split = json.loads((HERE / "holdout_events.json").read_text())
    region = ee.Geometry.Rectangle(PH_BBOX)

    ae = (
        ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
        .filterBounds(region)
        .filterDate(f"{EMB_YEAR}-01-01", f"{EMB_YEAR + 1}-01-01")
        .mosaic()
        .select(BANDS)
    )
    gfd = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1").filterBounds(region)

    train_sum = _recur_sum(ee, gfd, split["train_ids"])
    hold_sum = _recur_sum(ee, gfd, split["holdout_ids"])
    ever = gfd.select("flooded").max().unmask(0)
    land = ae.select("A00").mask()

    pos_train_mask = train_sum.gte(1).And(hold_sum.eq(0))
    pos_hold_mask = hold_sum.gte(1).And(train_sum.eq(0))
    neg_mask = land.And(ever.eq(0))

    X, y, group, lon, lat = [], [], [], [], []

    def add(rows, label, grp):
        for vec, lo, la in rows:
            X.append(vec); y.append(label); group.append(grp)
            lon.append(lo); lat.append(la)

    print("[fetch] sampling train positives ...")
    add(_sample(ee, ae, pos_train_mask, region, N_POS_TRAIN, 1), 1, "train")
    print(f"[fetch]   train pos: {sum(1 for g in group if g == 'train' and 1)}")
    print("[fetch] sampling holdout positives ...")
    add(_sample(ee, ae, pos_hold_mask, region, N_POS_HOLD, 2), 1, "holdout")
    print("[fetch] sampling negatives ...")
    neg = _sample(ee, ae, neg_mask, region, N_NEG, 3)
    import random

    rng = random.Random(split["seed"])
    for vec, lo, la in neg:
        grp = "holdout" if rng.random() < split["holdout_fraction"] else "train"
        X.append(vec); y.append(0); group.append(grp)
        lon.append(lo); lat.append(la)

    X = np.asarray(X, np.float32)
    y = np.asarray(y, np.int8)
    group = np.asarray(group)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT, X=X, y=y, group=group,
        lon=np.asarray(lon, np.float64), lat=np.asarray(lat, np.float64),
    )
    n_pos = int((y == 1).sum())
    n_hold = int((group == "holdout").sum())
    print(
        f"[fetch] wrote {OUT.name}: {X.shape} "
        f"({n_pos} pos / {len(y) - n_pos} neg; {n_hold} holdout rows) "
        f"{OUT.stat().st_size / 1e6:.1f} MB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
