import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table


# Sourced from dbt/models/staging/plants.sql
# and dbt/models/staging/plant_traits.sql


def define_plants(m: rai.Model, plants: Table, plant_traits: Table):
    """Define Plant and Trait concepts sourced from the USDA-style plants tables.

    The overall linking pattern we want is:
      Observation -> Taxon (GBIF) -> Plant (USDA plants table) -> Trait

    Where the linkage between GBIF Taxon and Plant is done by matching:
      Taxon.canonical_name == Plant.scientific_name

    And traits are represented as rows in the `plant_traits` table:
      (plant_id, trait_name, trait_value)
    """

    # Plant entity
    m.PlantId = m.Concept("PlantId", extends=[rai.Integer])
    m.Plant = m.Concept("Plant", identify_by={"id": m.PlantId})

    m.PlantScientificName = m.Concept("PlantScientificName", extends=[rai.String])
    m.PlantReference = m.Concept("PlantReference", extends=[rai.String])

    m.Plant.scientific_name = m.Property("{Plant} has scientific name {PlantScientificName}")
    m.Plant.reference = m.Property("{Plant} has reference {PlantReference}")

    rai.define(m.Plant.new(id=plants.ID))
    plant = rai.where(m.Plant.id == plants.ID)
    plant.define(m.Plant.scientific_name(plants.SCIENTIFIC_NAME))
    plant.define(m.Plant.reference(plants.REFERENCE))

    # Trait entity (name + value)
    m.TraitName = m.Concept("TraitName", extends=[rai.String])
    m.TraitValue = m.Concept("TraitValue", extends=[rai.String])
    m.Trait = m.Concept("Trait", identify_by={"name": m.TraitName, "value": m.TraitValue})

    rai.define(m.Trait.new(name=plant_traits.TRAIT_NAME, value=plant_traits.TRAIT_VALUE))

    # Plant -> Trait relationship
    m.Plant.trait = m.Property("{Plant} has trait {Trait}")

    p = m.Plant.ref()
    t = m.Trait.ref()
    rai.define(
        p.trait(t)
    ).where(
        p.id == plant_traits.PLANT_ID,
        t.name == plant_traits.TRAIT_NAME,
        t.value == plant_traits.TRAIT_VALUE,
    )

    # Taxon -> Plant linkage (by canonical name match)
    # Note: this assumes m.Taxon + m.Taxon.canonical_name have already been defined.
    m.Taxon.usda_plant = m.Property("{Taxon} matches USDA plant {Plant}")

    tx = m.Taxon.ref()
    rai.define(
        tx.usda_plant(p)
    ).where(
        tx.canonical_name == p.scientific_name,
    )
