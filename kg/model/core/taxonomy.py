from kg.model import m
from relationalai.semantics import String
from .entity import Entity

Domain = m.Concept("Domain", extends=[Entity])
Kingdom = m.Concept("Kingdom", extends=[Domain])
Phylum = m.Concept("Phylum", extends=[Kingdom])
Class = m.Concept("Class", extends=[Phylum])
Order = m.Concept("Order", extends=[Class])
Family = m.Concept("Family", extends=[Order])
Genus = m.Concept("Genus", extends=[Family])
Species = m.Concept("Species", extends=[Genus])
Subspecies = m.Concept("Subspecies", extends=[Species])
TaxonVariety = m.Concept("TaxonVariety", extends=[Species])

# Species-specific properties
Species.inat_link = m.Property(f"{Species} has iNaturalist link {String:inat_link}")
Species.inat_taxon_id = m.Property(f"{Species} has iNaturalist taxon id {String:inat_taxon_id}")
Species.common_name = m.Property(f"{Species} has common name {String:common_name}")
Species.iconic_taxon = m.Property(f"{Species} belongs to iconic taxon {String:iconic_taxon}")

Species.co_occurs_with = m.Relationship(f"{Species} co-occurs with {Species:co_occurs_with}")
