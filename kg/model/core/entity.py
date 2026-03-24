from kg.model import m
from relationalai.semantics import String

Entity = m.Concept("Entity")

Entity.name = m.Property(f"{Entity} is named {String:name}")
Entity.part_of = m.Relationship(f"{Entity} part of {Entity:part_of}")
Entity.has_part = m.Relationship(f"{Entity} has part {Entity:has_part}")