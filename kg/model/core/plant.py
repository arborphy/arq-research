import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from kg.model.compiler import EntitySpec, Key, Prop, compile_entity


# Sourced from dbt/models/staging/plants.sql



class PlantSpec(EntitySpec):
  """Declarative ground-truth spec for Plant (USDA-style plants table)."""

  __entity__ = "Plant"

  id = Key(label="{Plant} has id {PlantId}", column="ID", id_concept="PlantId", id_extends=rai.Integer)

  # Use the same value concept as Taxon.canonical_name so we can join without
  # cross-type comparisons.
  scientific_name = Prop(
    label="{Plant} has scientific name {CanonicalName}",
    column="SCIENTIFIC_NAME",
    value_concept="CanonicalName",
    create_value_concept=False,
  )

  reference = Prop(
    label="{Plant} has reference {PlantReference}",
    column="REFERENCE",
    value_concept="PlantReference",
    value_extends=rai.String,
  )


def define_plants(m: rai.Model, plants: Table) -> None:
  """Define Plant concepts sourced from the USDA-style plants table."""

  compile_entity(m=m, source=plants, spec=PlantSpec)
