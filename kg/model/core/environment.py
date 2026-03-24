from kg.model import m
from relationalai.semantics import String
from .entity import Entity

EnvironmentDescriptor = m.Concept("EnvironmentDescriptor", extends=[Entity])
EnvironmentValue = m.Concept("EnvironmentValue", extends=[Entity])

# Properties
EnvironmentValue.value = m.Property(f"{EnvironmentValue} has value {String:value}")

# Relationships
EnvironmentValue.descriptor = m.Relationship(f"{EnvironmentValue} belongs to {EnvironmentDescriptor:descriptor}")
