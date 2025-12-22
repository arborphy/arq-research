import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from kg.model.compiler import EntitySpec, Key, Prop, compile_entity


# Sourced from dbt/models/staging/taxon.sql


class TaxonSpec(EntitySpec):
    """Declarative ground-truth spec for Taxon (core source bindings only).

    The common-case bindings live here. More nuanced graph logic stays explicit
    in `define_taxon` (e.g., parent-edge filtering and rank-derived concepts).
    """

    __entity__ = "Taxon"

    id = Key(label="{Taxon} has id {TaxonId}", column="TAXONID", id_concept="TaxonId", id_extends=rai.Integer)

    scientific_name = Prop(
        label="{Taxon} has scientific name {ScientificName}",
        column="SCIENTIFICNAME",
        value_concept="ScientificName",
        value_extends=rai.String,
    )

    canonical_name = Prop(
        label="{Taxon} has canonical name {CanonicalName}",
        column="CANONICALNAME",
        value_concept="CanonicalName",
        value_extends=rai.String,
    )

    rank = Prop(
        label="{Taxon} has taxonomic rank {TaxonRank}",
        column="TAXONRANK",
        value_concept="TaxonRank",
        value_extends=rai.String,
    )


def define_taxon(m: rai.Model, source: Table) -> None:
    """Define the Taxon concept representing elements of the GBIF taxonomy."""

    # 1) Core schema + bindings
    compile_entity(m=m, source=source, spec=TaxonSpec)

    # 2) Parent edge (kept explicit to avoid accidental self-loops)
    m.Taxon.parent = m.Property("{Taxon} has parent taxon {Taxon}")

    t1 = m.Taxon.ref()
    t2 = m.Taxon.ref()
    rai.define(t1.parent(t2)).where(
        t1 != t2,
        t1.id == source.TAXONID,
        t2.id == source.PARENTNAMEUSAGEID,
    )

    # 3) Rank-derived taxonomy concepts
    # NOTE: these are “taxonomy-rank views” over Taxon. The user-facing species
    # abstraction is defined separately as `Species` (name-identified) in
    # `kg.model.derived.species`.
    m.TaxonSpecies = m.Concept("TaxonSpecies", extends=[m.Taxon])
    rai.define(m.TaxonSpecies.new(id=source.TAXONID)).where(source.TAXONRANK == "species")

    m.TaxonGenus = m.Concept("TaxonGenus", extends=[m.Taxon])
    rai.define(m.TaxonGenus.new(id=source.TAXONID)).where(source.TAXONRANK == "genus")

    m.TaxonFamily = m.Concept("TaxonFamily", extends=[m.Taxon])
    rai.define(m.TaxonFamily.new(id=source.TAXONID)).where(source.TAXONRANK == "family")

    m.TaxonOrder = m.Concept("TaxonOrder", extends=[m.Taxon])
    rai.define(m.TaxonOrder.new(id=source.TAXONID)).where(source.TAXONRANK == "order")

    m.TaxonClass = m.Concept("TaxonClass", extends=[m.Taxon])
    rai.define(m.TaxonClass.new(id=source.TAXONID)).where(source.TAXONRANK == "class")

    m.TaxonPhylum = m.Concept("TaxonPhylum", extends=[m.Taxon])
    rai.define(m.TaxonPhylum.new(id=source.TAXONID)).where(source.TAXONRANK == "phylum")

    m.TaxonKingdom = m.Concept("TaxonKingdom", extends=[m.Taxon])
    rai.define(m.TaxonKingdom.new(id=source.TAXONID)).where(source.TAXONRANK == "kingdom")


