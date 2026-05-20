"""Derive located_in from concept-bound spatial relationships.

Unifies spatial placement across concept types so queries can use the same
predicate regardless of the container type:

    obs = Observation.ref()
    cell = H3Cell.ref()
    where(located_in(obs, cell)).select(obs.inat_id, cell.index).to_df()

Derived rules (concept-bound relationship → located_in):
    Observation → H3Cell          (via Observation.h3cell)
    Observation → Location         (via Observation.located_in)
    H3Cell      → EcoSite         (via EcoSite.h3_cells, reversed)
    H3Cell      → Trail           (via Trail.h3_cells, reversed)

Loaded directly as located_in facts (no derived rule needed):
    H3Cell         → H3Cell          (finer cell located_in coarser cell)
    GeographicArea → GeographicArea  (smaller area located_in larger area)

TODO: derived links (Species via observations)
"""
from relationalai.semantics import define

from kg.model.core.entity import Location
from kg.model.core.observations import Observation
from kg.model.core.h3cell import H3Cell, EcoSite
from kg.model.core.trails import Trail
from kg.model.core.predicates import located_in

obs = Observation.ref()
cell = H3Cell.ref()
area = Location.ref()
ecosite = EcoSite.ref()
trail = Trail.ref()

define(located_in(obs, cell)).where(Observation.h3cell(obs, cell))
define(located_in(obs, area)).where(Observation.located_in(obs, area))
define(located_in(cell, ecosite)).where(EcoSite.h3_cells(ecosite, cell))
define(located_in(cell, trail)).where(Trail.h3_cells(trail, cell))
