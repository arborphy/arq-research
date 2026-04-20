from kg.model import m
from relationalai.semantics import String
from .provenance import DataSource

Entity = m.Concept("Entity")

Entity.name = m.Property(f"{Entity} is named {String:name}")
Entity.part_of = m.Relationship(f"{Entity} part of {Entity:part_of}")
Entity.has_part = m.Relationship(f"{Entity} has part {Entity:has_part}")
Entity.source = m.Relationship(f"{Entity} from source {DataSource:source}")