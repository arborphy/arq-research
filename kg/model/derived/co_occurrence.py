"""Derived rules for co-occurrence.

1. Observation co-occurrence: two observations co-occur if they share
   the same H3 res-9 cell, same year, and same day of year.

2. Species co-occurrence: two species co-occur if any of their
   observations co-occur.
"""
from relationalai.semantics import define

from kg.model.core.observations import Observation
from kg.model.core.taxonomy import Species
from kg.model.core.h3cell import H3Cell

# -- Observation co-occurrence --
obs1 = Observation.ref()
obs2 = Observation.ref()
cell = H3Cell.ref()

define(Observation.co_occurs_with(obs1, obs2)).where(
    Observation.h3cell(obs1, cell),
    Observation.h3cell(obs2, cell),
    obs1.date == obs2.date,
    obs1 != obs2,
)

# -- Species co-occurrence (derived from observation co-occurrence) --
o1 = Observation.ref()
o2 = Observation.ref()
s1 = Species.ref()
s2 = Species.ref()

define(Species.co_occurs_with(s1, s2)).where(
    o1.co_occurs_with(o2),
    o1.species(s1),
    o2.species(s2),
    s1 != s2,
)
