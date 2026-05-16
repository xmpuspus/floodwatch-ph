"""Auto-detect the most recent usable Sentinel-1 acquisition over the
Greater Metro Manila + Central Luzon corridor.

This is the acquisition-discovery probe for the near-real-time layer. It does
NOT compute flood — flood_latest.py does, importing this. Sentinel-1 revisit
over the Philippines is ~6–12 days, so the "latest pass" is the most recent
*observed* satellite acquisition, never a forecast and never live.

Coverage logic: S1 acquires in repeat orbital tracks. To keep the event scene
spatially consistent with its dry baseline we pick the single most recent
acquisition DATE, then keep only the dominant relative-orbit/pass-direction on
that date with adequate AOI footprint coverage.
"""

from __future__ import annotations

import datetime as _dt

# Greater Metro Manila + Central Luzon — the SLEX/NLEX corridor band:
# NCR + Bulacan + Pampanga + Rizal + Laguna + Cavite + Bataan.
# [west, south, east, north] in lon/lat.
AOI_BBOX = [120.40, 14.00, 121.55, 15.40]
AOI_NAME = (
    "Greater Metro Manila + Central Luzon (NCR, Bulacan, Pampanga, Rizal, "
    "Laguna, Cavite, Bataan — SLEX/NLEX corridor)"
)

# Lookback window for the latest event pass. S1 revisit is ~6–12 d over PH;
# 14 d guarantees at least one acquisition under nominal tasking.
DEFAULT_LOOKBACK_DAYS = 14
# Dry-baseline window length (days) ending just before the event pass.
BASELINE_DAYS = 60
# Minimum fraction of the AOI a candidate date's footprint must cover to be
# accepted as "adequate coverage" (a partial swath edge is not usable).
MIN_AOI_COVERAGE = 0.55


def aoi_geometry(ee):
    return ee.Geometry.Rectangle(AOI_BBOX)


def _s1_base(ee, aoi, d0, d1):
    """Same collection conventions as event/flood_extent.py::_s1_vh_vv:
    COPERNICUS/S1_GRD, IW mode, VV+VH polarisation."""
    return (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(aoi)
        .filterDate(d0, d1)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    )


def detect_latest_pass(ee, aoi, get_info, lookback_days=DEFAULT_LOOKBACK_DAYS):
    """Return a dict describing the most recent usable acquisition, or a dict
    with status='no_usable_pass' if nothing adequate exists in the window.

    `get_info` is a callable (ee_object, label) -> payload (the retry wrapper),
    so every network read here is bounded/retried.

    Returned on success:
      {status: "ok", as_of: "YYYY-MM-DD", orbit_pass: "ASCENDING|DESCENDING",
       rel_orbit: int, scene_ids: [...], coverage: float, lookback_days: int}
    """
    now = _dt.datetime.now(_dt.timezone.utc)
    start = (now - _dt.timedelta(days=lookback_days)).date().isoformat()
    end = (now + _dt.timedelta(days=1)).date().isoformat()  # inclusive of today

    coll = _s1_base(ee, aoi, start, end)

    props = get_info(
        coll.toList(coll.size()).map(
            lambda i: ee.Image(i).toDictionary(
                [
                    "system:time_start",
                    "system:index",
                    "orbitProperties_pass",
                    "relativeOrbitNumber_start",
                ]
            )
        ),
        "latest_pass_props",
    )
    if not props:
        return {
            "status": "no_usable_pass",
            "lookback_days": lookback_days,
            "scene_ids": [],
        }

    # Group by acquisition date; newest date first.
    by_date: dict[str, list[dict]] = {}
    for p in props:
        ts = p.get("system:time_start")
        if ts is None:
            continue
        d = (
            _dt.datetime.fromtimestamp(ts / 1000, _dt.timezone.utc)
            .date()
            .isoformat()
        )
        by_date.setdefault(d, []).append(p)

    for date in sorted(by_date, reverse=True):
        scenes = by_date[date]
        # Pick the dominant (orbit-pass, relative-orbit) on that date so the
        # event scene is one consistent track, matching its baseline.
        groups: dict[tuple, list[dict]] = {}
        for s in scenes:
            key = (
                s.get("orbitProperties_pass", "UNKNOWN"),
                int(s.get("relativeOrbitNumber_start", -1)),
            )
            groups.setdefault(key, []).append(s)
        (orbit_pass, rel_orbit), grp = max(
            groups.items(), key=lambda kv: len(kv[1])
        )

        scene_ids = [
            s.get("system:index") for s in grp if s.get("system:index")
        ]
        date_d0 = date
        date_d1 = (
            _dt.date.fromisoformat(date) + _dt.timedelta(days=1)
        ).isoformat()
        scene_coll = (
            _s1_base(ee, aoi, date_d0, date_d1)
            .filter(ee.Filter.eq("orbitProperties_pass", orbit_pass))
            .filter(
                ee.Filter.eq("relativeOrbitNumber_start", rel_orbit)
            )
        )
        # Coverage = footprint area of the mosaic ∩ AOI over AOI area.
        cov = get_info(
            ee.Number(
                scene_coll.select("VH")
                .mosaic()
                .mask()
                .multiply(ee.Image.pixelArea())
                .reduceRegion(
                    ee.Reducer.sum(), aoi, 200, maxPixels=1e9, bestEffort=True
                )
                .get("VH")
            ).divide(aoi.area(50)),
            "latest_pass_coverage",
        )
        cov = float(cov or 0.0)
        if cov >= MIN_AOI_COVERAGE:
            return {
                "status": "ok",
                "as_of": date,
                "orbit_pass": orbit_pass,
                "rel_orbit": rel_orbit,
                "scene_ids": scene_ids,
                "coverage": round(cov, 4),
                "lookback_days": lookback_days,
            }

    return {
        "status": "no_usable_pass",
        "lookback_days": lookback_days,
        "scene_ids": [],
    }
