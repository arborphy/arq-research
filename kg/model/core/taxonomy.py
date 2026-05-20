from kg.model import m
from relationalai.semantics import String
from .entity import Entity

Taxon = m.Concept("Taxon", extends=[Entity])

Domain = m.Concept("Domain", extends=[Taxon])
Kingdom = m.Concept("Kingdom", extends=[Taxon])
Phylum = m.Concept("Phylum", extends=[Taxon])
Class = m.Concept("Class", extends=[Taxon])
Order = m.Concept("Order", extends=[Taxon])
Family = m.Concept("Family", extends=[Taxon])
Genus = m.Concept("Genus", extends=[Taxon])
Species = m.Concept("Species", extends=[Taxon])
Subspecies = m.Concept("Subspecies", extends=[Taxon])
TaxonVariety = m.Concept("TaxonVariety", extends=[Taxon])

# Species-specific properties
Species.inat_link = m.Property(f"{Species} has iNaturalist link {String:inat_link}")
Species.inat_taxon_id = m.Property(f"{Species} has iNaturalist taxon id {String:inat_taxon_id}")
Species.common_name = m.Property(f"{Species} has common name {String:common_name}")
Species.iconic_taxon = m.Property(f"{Species} belongs to iconic taxon {String:iconic_taxon}")

Species.co_occurs_with = m.Relationship(f"{Species} co-occurs with {Species:co_occurs_with}")
