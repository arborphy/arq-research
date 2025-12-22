import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from kg.model.compiler import EntitySpec, Prop, compile_entity


# Sourced from dbt/models/staging/plant_traits.sql


class TraitSpec(EntitySpec):
    """Declarative ground-truth spec for Trait.

    Trait is identified by (name, value). The compiler binds the entity itself.
    The Plant->Trait relationship is still defined explicitly in `define_traits`
    because it is a multi-column join (plant_id + trait name + trait value).
    """

    __entity__ = "Trait"

    __identify_by__ = {
        "name": "TraitName",
        "value": "TraitValue",
    }

    name = Prop(
        label="{Trait} has trait name {TraitName}",
        column="TRAIT_NAME",
        value_concept="TraitName",
        value_extends=rai.String,
    )

    value = Prop(
        label="{Trait} has trait value {TraitValue}",
        column="TRAIT_VALUE",
        value_concept="TraitValue",
        value_extends=rai.String,
    )


def define_traits(m: rai.Model, plant_traits: Table):
    """Define the Trait concept sourced from the long-form `plant_traits` table.

    Traits are represented as rows in `plant_traits`:
      (plant_id, trait_name, trait_value)

    This definition is intentionally separate from Plants, since we expect the
    Trait concept and its semantics to evolve independently.
    """

    # Trait entity (name + value)
    compile_entity(m=m, source=plant_traits, spec=TraitSpec)

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
