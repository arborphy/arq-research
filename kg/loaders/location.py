"""Hardcoded location hierarchy for the current observation dataset.

All iNaturalist observations in this dataset are from Ward Pound Ridge Reservation
in Westchester County, NY.  We assert:

    Ward Pound Ridge Reservation (Park)
        located_in Westchester County (City)
            located_in New York (State)
                located_in United States (Country)

Observations are linked to the park via Observation.located_in.
"""
from relationalai.semantics import define, where

import kg.loaders.observations  # noqa: F401  (needed for Observation facts)
from kg.model.core.location import Park, City, State, Country
from kg.model.core.observations import Observation
from kg.model.core.predicates import located_in

# -- Instances --
define(Park.new(name="Ward Pound Ridge Reservation"))
define(City.new(name="Westchester County"))
define(State.new(name="New York"))
define(Country.new(name="United States"))

# -- Geographic containment --
where(
    park  := Park.filter_by(name="Ward Pound Ridge Reservation"),
    city  := City.filter_by(name="Westchester County"),
).define(located_in(park, city))

where(
    city  := City.filter_by(name="Westchester County"),
    state := State.filter_by(name="New York"),
).define(located_in(city, state))

where(
    state   := State.filter_by(name="New York"),
    country := Country.filter_by(name="United States"),
).define(located_in(state, country))

# -- Link all observations to the park (all observations are from Ward Pound Ridge) --
where(
    obs  := Observation,
    park := Park.filter_by(name="Ward Pound Ridge Reservation"),
).define(Observation.located_in(obs, park))
