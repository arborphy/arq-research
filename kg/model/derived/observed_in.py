"""Derived rules: ``observed_in`` global predicate.

``observed_in(taxon, location)`` — a taxon has been observed inside location.

Spatial chain: ``located_in.py`` seeds ``located_in`` facts for each Observation
(h3cell, area). ``within`` (transitive closure of ``located_in``) then links each
Observation to every enclosing Location.

  - observed_in(Species, loc)  — at least one of the species' observations is within loc.
  - observed_in(Genus, loc)    — at least one species in the genus does.
  - observed_in(Family, loc)   — and so on, up the taxonomy via within_clade.
"""
from relationalai.semantics import define

from kg.model.core.entity import Location
from kg.model.core.observations import Observation
from kg.model.core.taxonomy import Species, Taxon
from kg.model.core.predicates import observed_in, within, within_clade

obs = Observation.ref()

# Species: observed_in a Location if any of its observations is within that Location.
# (within = transitive closure of located_in, seeded by located_in.py)
define(observed_in(Species, Location)).where(
    Observation.species(obs, Species),
    within(obs, Location),
)

# Taxon hierarchy: propagate up the clade tree (Genus, Family, …).
taxon = Taxon.ref()
define(observed_in(taxon, Location)).where(
    within_clade(Species, taxon),
    observed_in(Species, Location),
)
