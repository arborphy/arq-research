"""Derived name for Observation.

Derives Entity.name by combining species_guess and inat_id, making
Observation compatible with any Entity.name-based query (e.g. terminal_node).

Result: "<species_guess> (#<inat_id>)"  e.g. "mapleleaf viburnum (#100857298)"
"""
from relationalai.semantics import define, std

from kg.model.core.entity import Entity
from kg.model.core.observations import Observation

obs_name = std.strings.concat(
    Observation.species_guess, " (#", Observation.inat_id, ")"
)

define(Entity.name(Observation, obs_name))
