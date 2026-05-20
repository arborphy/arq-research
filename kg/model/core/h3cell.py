from kg.model import m
from relationalai.semantics import Int128, Integer, String

from kg.model.core.location import Coordinate
from .entity import Location
from .observations import Observation

H3Cell = m.Concept("H3Cell", extends=[Location])

# Properties
H3Cell.index = m.Property(f"{H3Cell} has index {Int128:index}")
H3Cell.resolution = m.Property(f"{H3Cell} at resolution {Integer:resolution}")
# NOTE: m.define(H3Cell.resolution((H3Cell.index // 2**52) % 16)) triggers a RAI SDK
# IR serialization bug (Field not handled in value_to_string). Set resolution explicitly in loaders.

# Relationships
Observation.h3cell = m.Relationship(f"{Observation} falls in {H3Cell:h3cell}")
Observation.coordinate = m.Relationship(f"{Observation} has coordinates {Coordinate}")    

Coordinate.h3cell = m.Relationship(f"{Coordinate} in {H3Cell:h3cell}")

# -- EcoSite --
EcoSite = m.Concept("EcoSite", extends=[Location])

EcoSite.ecosite_id = m.Property(f"{EcoSite} has ecosite id {String:ecosite_id}")
EcoSite.h3_cells = m.Relationship(f"{EcoSite} covers {H3Cell:h3_cells}")
EcoSite.compacted_h3_cells = m.Relationship(f"{EcoSite} has compacted coverage {H3Cell:compacted_h3_cells}")
