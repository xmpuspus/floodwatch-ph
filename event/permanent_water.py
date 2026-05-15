"""Permanent-water mask — the integrity rule (locked decision 2).

A pixel is permanent water if ANY of:
  - JRC Global Surface Water occurrence >= 50%
  - MERIT Hydro flags it as a river/water network cell (`wat` > 0)
The product reports FLOOD, not rivers/lakes/sea. This mask is subtracted from
every flood footprint before it is published, and an independent CI gate
re-checks published GeoJSONs against JRC >=50% occurrence.
"""

from __future__ import annotations

JRC_OCCURRENCE_THRESHOLD = 50


def permanent_water_mask(ee):
    """Return an ee.Image (1 = permanent water, 0 = not)."""
    jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")
    jrc_perm = jrc.gte(JRC_OCCURRENCE_THRESHOLD).unmask(0)
    merit = ee.Image("MERIT/Hydro/v1_0_1").select("wat").gt(0).unmask(0)
    return jrc_perm.Or(merit).rename("permanent_water")


def land_slope_ok(ee, max_deg: float = 5.0):
    """Terrain plausibility: flooding does not pool on steep slopes."""
    dem = ee.Image("MERIT/Hydro/v1_0_1").select("elv")
    slope = ee.Terrain.slope(dem)
    return slope.lt(max_deg).rename("slope_ok")


def flood_plausible_terrain(ee):
    """HAND-style flood-plausible mask. SAR over Philippine rice agriculture
    (esp. Central Luzon in the Oct harvest window) produces large VH drops
    that mimic flooding. The standard refinement is to keep only terrain that
    is hydrologically capable of flooding: near-flat AND either low-lying or
    in a place where surface water has ever historically occurred (JRC GSW
    occurrence >= 1). This is a documented refinement, not a fitted parameter.
    """
    elv = ee.Image("MERIT/Hydro/v1_0_1").select("elv")
    slope = ee.Terrain.slope(elv)
    occ = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0)
    near_flat = slope.lt(3.0)
    lowland_or_waterhistory = elv.lt(30).Or(occ.gte(1))
    return near_flat.And(lowland_or_waterhistory).rename("flood_plausible")
