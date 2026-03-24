from kg.model import m
from relationalai.semantics import String
from .entity import Entity
from .provenance import DataSource

Domain = m.Concept("Domain", extends=[Entity])
Kingdom = m.Concept("Kingdom", extends=[Entity])
Phylum = m.Concept("Phylum", extends=[Entity])
Class = m.Concept("Class", extends=[Entity])
Order = m.Concept("Order", extends=[Entity])
Family = m.Concept("Family", extends=[Entity])
Genus = m.Concept("Genus", extends=[Entity])
Species = m.Concept("Species", extends=[Entity])
Subspecies = m.Concept("Subspecies", extends=[Entity])
TaxonVariety = m.Concept("TaxonVariety", extends=[Entity])

# Species-specific properties
Species.inat_link = m.Property(f"{Species} has iNaturalist link {String:inat_link}")
Species.inat_taxon_id = m.Property(f"{Species} has iNaturalist taxon id {String:inat_taxon_id}")
Species.common_name = m.Property(f"{Species} has common name {String:common_name}")
Species.iconic_taxon = m.Property(f"{Species} belongs to iconic taxon {String:iconic_taxon}")

Species.source = m.Relationship(f"{Species} from source {DataSource:source}")
Species.co_occurs_with = m.Relationship(f"{Species} co-occurs with {Species:co_occurs_with}")
