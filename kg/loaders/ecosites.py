"""Load EcoSites and their res-13 H3 cells from stg_ecosites."""
from relationalai.semantics import Int128, String, define, where

from kg.model import m
from kg.model.core.h3cell import EcoSite, H3Cell

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

ecosites_table = m.Table(f"{DB}.{SCHEMA}.stg_ecosites_compacted", schema={
    "ECOSITE_ID": String,
    "H3_CELL": Int128,
})

# -- EcoSites (create) --
define(EcoSite.new(ecosite_id=ecosites_table.ECOSITE_ID))

# -- H3 Cells at res 9 (create) --
define(H3Cell.new(index=ecosites_table.H3_CELL))

# -- EcoSite.h3_cells relationship --
where(
    ecosite := EcoSite.filter_by(ecosite_id=ecosites_table.ECOSITE_ID),
    cell := H3Cell.filter_by(index=ecosites_table.H3_CELL),
).define(
    EcoSite.h3_cells(ecosite, cell),
)
