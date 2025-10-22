import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

# Sourced from dbt/models/staging/taxon.sql

def define_taxon(m: rai.Model, source: Table):
    """Define the Taxon concept representing elements of the GBIF taxonomy.

    A Taxon represents a taxonomic unit (species, genus, family, etc.) in the
    GBIF taxonomic backbone. It includes the scientific nomenclature, taxonomic
    hierarchy, and relationships to parent taxa.
    """

    # Define ID and main concept
    m.TaxonId = m.Concept("TaxonId", extends=[rai.Integer])
    m.Taxon = m.Concept("Taxon", identify_by={"id": m.TaxonId})

    # Define value concepts for taxon attributes
    m.ScientificName = m.Concept("ScientificName", extends=[rai.String])
    m.CanonicalName = m.Concept("CanonicalName", extends=[rai.String])
    m.TaxonRank = m.Concept("TaxonRank", extends=[rai.String])
    
    # Define properties/relationships
    m.Taxon.scientific_name = m.Property("{Taxon} has scientific name {ScientificName}")
    m.Taxon.canonical_name = m.Property("{Taxon} has canonical name {CanonicalName}")
    m.Taxon.rank = m.Property("{Taxon} has taxonomic rank {TaxonRank}")
    m.Taxon.parent = m.Property("{Taxon} has parent taxon {Taxon}")

    # Bind source data to concepts
    rai.define(m.Taxon.new(id=source.TAXONID))
    taxon = rai.where(m.Taxon.id == source.TAXONID)
    taxon.define(m.Taxon.scientific_name(source.SCIENTIFICNAME))
    taxon.define(m.Taxon.canonical_name(source.CANONICALNAME))
    taxon.define(m.Taxon.rank(source.TAXONRANK))

    t1 = m.Taxon.ref()
    t2 = m.Taxon.ref()
    rai.define(
        t1.parent(t2)
    ).where(
        t1 != t2,
        t1.id == source.TAXONID,
        t2.id == source.PARENTNAMEUSAGEID,
    )

    # Define taxonomic rank concepts
    m.Species = m.Concept("Species", extends=[m.Taxon])
    rai.define(m.Species.new(id=source.TAXONID)).where(source.TAXONRANK == "species")

    m.Genus = m.Concept("Genus", extends=[m.Taxon])
    rai.define(m.Genus.new(id=source.TAXONID)).where(source.TAXONRANK == "genus")

    m.Family = m.Concept("Family", extends=[m.Taxon])
    rai.define(m.Family.new(id=source.TAXONID)).where(source.TAXONRANK == "family")

    m.Order = m.Concept("Order", extends=[m.Taxon])
    rai.define(m.Order.new(id=source.TAXONID)).where(source.TAXONRANK == "order")

    m.Class = m.Concept("Class", extends=[m.Taxon])
    rai.define(m.Class.new(id=source.TAXONID)).where(source.TAXONRANK == "class")

    m.Phylum = m.Concept("Phylum", extends=[m.Taxon])
    rai.define(m.Phylum.new(id=source.TAXONID)).where(source.TAXONRANK == "phylum")

    m.Kingdom = m.Concept("Kingdom", extends=[m.Taxon])
    rai.define(m.Kingdom.new(id=source.TAXONID)).where(source.TAXONRANK == "kingdom")


