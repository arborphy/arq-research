"""Transitive spatial closure over located_in.

`within` is the transitive version of `located_in`: an entity is within a place
if it is located_in that place directly, or located_in something that is itself
within that place.

    # Is this observation anywhere inside Vermont (at any H3 resolution)?
    obs = Observation.ref()
    area = GeographicArea.ref()
    where(obs.inat_id == "123", within(obs, area), area.name == "Vermont")

Rules:
    within(x, place)    :- located_in(x, place)
    within(x, ancestor) :- within(x, place), located_in(place, ancestor)
"""
from relationalai.semantics import define

from kg.model.core.entity import Entity, Location
from kg.model.core.predicates import located_in, within

x = Entity.ref()
place = Location.ref()
ancestor = Location.ref()

# Base: any direct located_in is also within
define(within(x, place)).where(
    located_in(x, place),
)

# Recursive: propagate through located_in chains
define(within(x, ancestor)).where(
    within(x, place),
    located_in(place, ancestor),
)
# ∃ place: within(x, place) & located_in(place, ancestor)