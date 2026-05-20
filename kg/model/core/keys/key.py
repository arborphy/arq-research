"""Source descriptions linking taxa to feature-value pairs with provenance."""
from relationalai.semantics import String

from kg.model import m
from kg.model.core.entity import Entity
from kg.model.core.taxonomy import Taxon
from kg.model.core.features import Feature, Category, Measurement

# Description: a versioned source record describing a taxon.
# Identity: (name, version) — e.g. ("newcomb:Trillium grandiflorum", "1977")
Description = m.Concept("Description", extends=[Entity])
Description.version = m.Property(f"{Description} has version {String:version}")
Description.describes = m.Relationship(f"{Description} describes {Taxon:describes}")
Description.feature = m.Relationship(f"{Description} has feature {Feature:feature}")
Description.category = m.Relationship(f"{Description} has category {Category:category}")
Description.measurement = m.Relationship(f"{Description} has measurement {Measurement:measurement}")