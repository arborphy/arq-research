import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table


# Sourced from dbt/models/staging/plants.sql



def define_plants(m: rai.Model, plants: Table):
    """Define Plant concepts sourced from the USDA-style plants table.

    The overall linking pattern we want is:
      Observation -> Taxon (GBIF) -> Plant (USDA plants table) -> Trait

    Where the linkage between GBIF Taxon and Plant is done by matching:
      Taxon.canonical_name == Plant.scientific_name

    Trait definitions and Plant->Trait relationships are defined separately in
    `kg.model.core.trait`.
    """

    # Plant entity
    m.PlantId = m.Concept("PlantId", extends=[rai.Integer])
    m.Plant = m.Concept("Plant", identify_by={"id": m.PlantId})

    m.PlantReference = m.Concept("PlantReference", extends=[rai.String])

    # Use the same value concept as Taxon.canonical_name so we can join without
    # cross-type comparisons.
    m.Plant.scientific_name = m.Relationship("{Plant} has scientific name {CanonicalName}")
    m.Plant.reference = m.Relationship("{Plant} has reference {PlantReference}")

    rai.define(m.Plant.new(id=plants.ID))
    plant = rai.where(m.Plant.id == plants.ID)
    plant.define(m.Plant.scientific_name(plants.SCIENTIFIC_NAME))
    plant.define(m.Plant.reference(plants.REFERENCE))
    # Taxon -> Plant linkage (by canonical name match)
    # Note: this assumes m.Taxon + m.Taxon.canonical_name have already been defined.
    m.Taxon.usda_plant = m.Relationship("{Taxon} matches USDA plant {Plant}")

    p = m.Plant.ref()
    tx = m.Taxon.ref()
    rai.define(
        tx.usda_plant(p)
    ).where(
        tx.canonical_name == p.scientific_name,
    )
