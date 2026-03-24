from kg.model import m
from relationalai.semantics import Int64, Integer, String
from .entity import Entity
from .observations import Observation

H3Cell = m.Concept("H3Cell", extends=[Entity])

# Properties
H3Cell.index = m.Property(f"{H3Cell} has index {Int64:index}")
H3Cell.resolution = m.Property(f"{H3Cell} at resolution {Integer:resolution}")

# Relationships
Observation.h3cell = m.Relationship(f"{Observation} falls in {H3Cell:h3cell}")
