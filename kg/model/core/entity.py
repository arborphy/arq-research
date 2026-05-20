from kg.model import m
from relationalai.semantics import String
from .provenance import DataSource

Entity = m.Concept("Entity")
Location = m.Concept("Location", extends=[Entity])

Entity.name = m.Property(f"{Entity} is named {String:name}")
Entity.source = m.Relationship(f"{Entity} from source {DataSource:source}")