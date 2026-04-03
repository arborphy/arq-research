"""Load compacted EcoSite H3 cells from stg_ecosites_compacted."""
from relationalai.semantics import Int128, String, define, where

from kg.model import m
from kg.model.core.h3cell import EcoSite, H3Cell

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

compacted_table = m.Table(f"{DB}.{SCHEMA}.stg_ecosites_compacted", schema={
    "ECOSITE_ID": String,
    "H3_CELL": Int128,
})

# -- H3 Cells (create) --
define(H3Cell.new(index=compacted_table.H3_CELL))

# -- EcoSite.compacted_h3_cells relationship --
where(
    ecosite := EcoSite.filter_by(ecosite_id=compacted_table.ECOSITE_ID),
    cell := H3Cell.filter_by(index=compacted_table.H3_CELL),
).define(
    EcoSite.compacted_h3_cells(ecosite, cell),
)
