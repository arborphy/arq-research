from kg.model import m
from relationalai.semantics import String
from kg.model.core.entity import Entity
from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, FeatureValue
from kg.model.core.provenance import DataSource

IdentificationKey = m.Concept("IdentificationKey", extends=[Entity])

# Properties
IdentificationKey.value = m.Property(f"{IdentificationKey} has value {String:value}")

# Relationships
IdentificationKey.species = m.Relationship(f"{IdentificationKey} identifies {Species:species}")
IdentificationKey.feature = m.Relationship(f"{IdentificationKey} has feature {Feature:feature}")
IdentificationKey.feature_value = m.Relationship(f"{IdentificationKey} has feature value {FeatureValue:feature_value}")
IdentificationKey.source = m.Relationship(f"{IdentificationKey} from source {DataSource:source}")
