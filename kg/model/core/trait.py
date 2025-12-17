import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table


# Sourced from dbt/models/staging/plant_traits.sql


def define_traits(m: rai.Model, plant_traits: Table):
    """Define the Trait concept sourced from the long-form `plant_traits` table.

    Traits are represented as rows in `plant_traits`:
      (plant_id, trait_name, trait_value)

    This definition is intentionally separate from Plants, since we expect the
    Trait concept and its semantics to evolve independently.
    """

    # Trait entity (name + value)
    m.TraitName = m.Concept("TraitName", extends=[rai.String])
    m.TraitValue = m.Concept("TraitValue", extends=[rai.String])
    m.Trait = m.Concept("Trait", identify_by={"name": m.TraitName, "value": m.TraitValue})

    rai.define(m.Trait.new(name=plant_traits.TRAIT_NAME, value=plant_traits.TRAIT_VALUE))

    # Plant -> Trait relationship
    # Note: this assumes Plant has already been defined.
    m.Plant.trait = m.Relationship("{Plant} has trait {Trait}")

    p = m.Plant.ref()
    t = m.Trait.ref()
    rai.define(
        p.trait(t)
    ).where(
        p.id == plant_traits.PLANT_ID,
        t.name == plant_traits.TRAIT_NAME,
        t.value == plant_traits.TRAIT_VALUE,
    )
