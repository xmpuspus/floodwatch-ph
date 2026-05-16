"""GPM IMERG rolling rainfall accumulation over the FloodWatch AOI.

Collection: NASA/GPM_L3/IMERG_V07 (~30-min cadence, V07 band is
``precipitation`` in mm/hr; the older ``precipitationCal`` name is V06 only).
Accumulation over a window = sum(precipitation mm/hr) * 0.5 h per 30-min slice.

Nothing here is a forecast. It reports rainfall that has already fallen, as of
the latest available IMERG timestamp (IMERG late/final runs lag ~a few hours
to ~1 day).
"""

from __future__ import annotations

import datetime as _dt

# Greater Metro Manila + Central Luzon, the SLEX/NLEX expressway corridor band:
# NCR, Bulacan, Pampanga, Rizal, Laguna, Cavite, Bataan.
# [west_lon, south_lat, east_lon, north_lat]
AOI_BBOX = [119.7, 13.9, 121.6, 15.6]

IMERG_COLLECTION = "NASA/GPM_L3/IMERG_V07"
IMERG_BAND = "precipitation"  # mm/hr (V07)
IMERG_SLICE_HOURS = 0.5  # 30-minute cadence


def aoi_geometry(ee):
    """ee.Geometry rectangle for the expressway-corridor AOI."""
    return ee.Geometry.Rectangle(AOI_BBOX)


def latest_imerg_time(ee, aoi):
    """Return (datetime UTC, epoch_ms) of the most recent IMERG image over AOI.

    Raises LookupError if the collection is empty over the AOI.
    """
    col = (
        ee.ImageCollection(IMERG_COLLECTION)
        .filterBounds(aoi)
        .sort("system:time_start", False)
    )
    n = col.size().getInfo()
    if not n:
        raise LookupError("IMERG_V07 returned no images over AOI")
    ms = col.first().get("system:time_start").getInfo()
    return _dt.datetime.fromtimestamp(ms / 1000, tz=_dt.timezone.utc), ms


def accumulation_image(ee, aoi, end_dt, hours):
    """Accumulated rainfall (mm) image over a window ending at end_dt.

    Returns (ee.Image single-band 'mm', n_images:int). Image may have 0 bands /
    be empty if no IMERG slices fall in the window; callers must guard.
    """
    start_dt = end_dt - _dt.timedelta(hours=hours)
    # +1 min so the end-inclusive slice is captured.
    col = (
        ee.ImageCollection(IMERG_COLLECTION)
        .filterBounds(aoi)
        .filterDate(
            start_dt.isoformat(),
            (end_dt + _dt.timedelta(minutes=1)).isoformat(),
        )
        .select(IMERG_BAND)
    )
    n = col.size().getInfo()
    acc = col.sum().multiply(IMERG_SLICE_HOURS).rename("mm").clip(aoi)
    return acc, n
