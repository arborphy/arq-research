"""Load WPR trail segments and their res-13 H3 cells from stg_trail_cells."""
from relationalai.semantics import Int128, String, define, where

from kg.model import m
from kg.model.core.h3cell import H3Cell
from kg.model.core.trails import Trail

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

trails_table = m.Table(f"{DB}.{SCHEMA}.stg_trail_cells", schema={
    "OSM_ID": String,
    "NAME": String,
    "HIGHWAY": String,
    "SURFACE": String,
    "H3_RES13": Int128,
})

# -- Trails (create) --
define(Trail.new(osm_id=trails_table.OSM_ID))

# -- Trail properties --
where(trail := Trail.filter_by(osm_id=trails_table.OSM_ID)).define(
    trail.name(trails_table.NAME),
    trail.highway(trails_table.HIGHWAY),
    trail.surface(trails_table.SURFACE),
)

# -- H3 Cells (create) --
define(H3Cell.new(index=trails_table.H3_RES13))

# -- Trail.h3_cells relationship --
where(
    trail := Trail.filter_by(osm_id=trails_table.OSM_ID),
    cell := H3Cell.filter_by(index=trails_table.H3_RES13),
).define(
    Trail.h3_cells(trail, cell),
)
