from kg.model import m
from relationalai.semantics import String
from .entity import Entity

Feature = m.Concept("Feature", extends=[Entity])
FeatureValue = m.Concept("FeatureValue", extends=[Entity])

# Properties
FeatureValue.value = m.Property(f"{FeatureValue} has value {String:value}")

# Relationships
FeatureValue.feature = m.Relationship(f"{FeatureValue} belongs to {Feature:feature}")
