import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from kg.model.compiler import EntitySpec, Key, Prop, Ref, compile_entity


# Sourced from dbt/models/staging/observation.sql


class ObservationSpec(EntitySpec):
    """Declarative ground-truth spec for Observation.

    This spec is meant to be the single place you edit for the common case.
    The compiler generates:
    - Concepts/Properties on the RAI model
    - Source bindings from a `Table`

    Overrides (column names, target keys) are explicit here.
    """

    __entity__ = "Observation"

    id = Key(label="{Observation} has id {ObservationId}", column="GBIFID", id_concept="ObservationId", id_extends=rai.Integer)

    event_datetime = Prop(
        label="{Observation} occurred on {EventDateTime}",
        column="EVENTDATE",
        value_concept="EventDateTime",
        value_extends=rai.DateTime,
    )

    # These value concepts come from foundational modules (calendar/geography)
    day_of_year = Prop(
        label="{Observation} occurred on day {DayOfYear}",
        column="DAYOFYEAR",
        value_concept="DayOfYear",
        create_value_concept=False,
    )

    year = Prop(
        label="{Observation} occurred in year {Year}",
        column="YEAR",
        value_concept="Year",
        create_value_concept=False,
    )

    basis_of_record = Prop(
        label="{Observation} has basis of record {BasisOfRecord}",
        column="BASISOFRECORD",
        value_concept="BasisOfRecord",
        value_extends=rai.String,
    )

    country_code = Prop(
        label="{Observation} was recorded in country {CountryCode}",
        column="COUNTRYCODE",
        value_concept="CountryCode",
        value_extends=rai.String,
    )

    state_province = Prop(
        label="{Observation} was recorded in state/province {StateProvince}",
        column="STATEPROVINCE",
        value_concept="StateProvince",
        value_extends=rai.String,
    )

    latitude = Prop(
        label="{Observation} has latitude {Latitude}",
        column="LAT",
        value_concept="Latitude",
        create_value_concept=False,
    )

    longitude = Prop(
        label="{Observation} has longitude {Longitude}",
        column="LON",
        value_concept="Longitude",
        create_value_concept=False,
    )

    h3_cell_6 = Prop(
        label="{Observation} is in H3 cell (~36km^2) {H3Cell}",
        column="H3_CELL_6",
        value_concept="H3Cell",
        create_value_concept=False,
    )
    h3_cell_7 = Prop(
        label="{Observation} is in H3 cell (~5km^2) {H3Cell}",
        column="H3_CELL_7",
        value_concept="H3Cell",
        create_value_concept=False,
    )
    h3_cell_8 = Prop(
        label="{Observation} is in H3 cell (~0.7km^2) {H3Cell}",
        column="H3_CELL_8",
        value_concept="H3Cell",
        create_value_concept=False,
    )
    h3_cell_9 = Prop(
        label="{Observation} is in H3 cell (~0.1km^2) {H3Cell}",
        column="H3_CELL_9",
        value_concept="H3Cell",
        create_value_concept=False,
    )
    h3_cell_10 = Prop(
        label="{Observation} is in H3 cell (~0.01km^2) {H3Cell}",
        column="H3_CELL_10",
        value_concept="H3Cell",
        create_value_concept=False,
    )

    classification = Ref(
        label="{Observation} is classified as {Taxon}",
        column="TAXONKEY",
        target="Taxon",
        target_key="id",
    )


def define_observation(m: rai.Model, source: Table) -> None:
    """Define + bind Observation using the declarative compiler.

    Common-case edits should happen in `ObservationSpec`.
    """

    compile_entity(m=m, source=source, spec=ObservationSpec)
