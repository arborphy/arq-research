from typing import Protocol, cast

import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from kg.model.core.calendar import define_calendar
from kg.model.core.geography import define_geography
from kg.model.core.soleq import define_solstice_equinox
from kg.model.core.taxon import define_taxon
from kg.model.core.observation import ObservationSpec
from kg.model.core.plant import define_plants
from kg.model.core.trait import define_traits
from kg.model.derived.taxonomy import define_taxonomy
from kg.model.derived.species import define_species
from kg.model.derived.observation import define_derived_observation
try:
    from kg.model._generated_protocols import (
        Observation as ObservationGenerated,
        Plant as PlantGenerated,
        Taxon as TaxonGenerated,
        Trait as TraitGenerated,
    )
except Exception:  # pragma: no cover
    # Bootstrap path: allows `kg.model.compiler.generate_protocols` to run even
    # when `_generated_protocols.py` is stale or missing newer entities.
    class TaxonGenerated(Protocol):
        id: rai.Relationship
        scientific_name: rai.Relationship
        canonical_name: rai.Relationship
        rank: rai.Relationship

    class ObservationGenerated(Protocol):
        id: rai.Relationship

    class PlantGenerated(Protocol):
        id: rai.Relationship
        scientific_name: rai.Relationship
        reference: rai.Relationship

    class TraitGenerated(Protocol):
        name: rai.Relationship
        value: rai.Relationship
from kg.model.plan import ModelPlan, NoSourceStep, TableStep, EntitySpecStep


# Protocol definitions for the attributes dynamically assigned to the model
# Not strictly required, but enables nice autocomplete in the editor
# Claude is good at updating these based on the model files

class TaxonExtras(Protocol):
    parent: rai.Relationship
    genus: rai.Relationship
    family: rai.Relationship
    order: rai.Relationship
    class_: rai.Relationship
    phylum: rai.Relationship
    kingdom: rai.Relationship
    species: rai.Relationship


class Taxon(TaxonGenerated, TaxonExtras, Protocol):
    pass


class ObservationExtras(Protocol):
    """Non-source-backed observation relationships.

    These are defined in derived modules (not from the ObservationSpec binding).
    """

    hemisphere: rai.Relationship
    visible_trait: rai.Relationship
    species: rai.Relationship


class Observation(ObservationGenerated, ObservationExtras, Protocol):
    pass


class PlantExtras(Protocol):
    trait: rai.Relationship
    species: rai.Relationship


class Plant(PlantGenerated, PlantExtras, Protocol):
    pass


class Trait(TraitGenerated, Protocol):
    pass


class Species(Protocol):
    name: rai.Relationship
    taxon: rai.Relationship
    plant: rai.Relationship
    trait: rai.Relationship
    genus: rai.Relationship
    family: rai.Relationship
    order: rai.Relationship
    class_: rai.Relationship
    phylum: rai.Relationship
    kingdom: rai.Relationship


class Hemisphere(Protocol):
    id: rai.Relationship


class Latitude(Protocol):
    hemisphere: rai.Relationship


class Longitude(Protocol):
    hemisphere: rai.Relationship


class CalendarEvent(Protocol):
    datetime: rai.Relationship
    year: rai.Relationship
    day_of_year: rai.Relationship


class Solstice(Protocol):
    year: rai.Relationship
    datetime: rai.Relationship
    summer: rai.Relationship
    winter: rai.Relationship


class Equinox(Protocol):
    year: rai.Relationship
    datetime: rai.Relationship
    spring: rai.Relationship
    fall: rai.Relationship


class TaxonSpecies(Taxon, Protocol):
    pass


class TaxonGenus(Taxon, Protocol):
    pass


class TaxonFamily(Taxon, Protocol):
    pass


class TaxonOrder(Taxon, Protocol):
    pass


class TaxonClass(Taxon, Protocol):
    pass


class TaxonPhylum(Taxon, Protocol):
    pass


class TaxonKingdom(Taxon, Protocol):
    pass


class ARQModel(Protocol):
    # Value concepts - Taxon
    TaxonId: rai.Concept
    ScientificName: rai.Concept
    CanonicalName: rai.Concept
    TaxonRank: rai.Concept

    # Value concepts - Observation
    ObservationId: rai.Concept
    EventDateTime: rai.Concept
    DayOfYear: rai.Concept
    Year: rai.Concept
    BasisOfRecord: rai.Concept
    CountryCode: rai.Concept
    StateProvince: rai.Concept
    Latitude: Latitude
    Longitude: Longitude
    H3Cell: rai.Concept

    # Hemisphere instances
    HemisphereNorth: Hemisphere
    HemisphereSouth: Hemisphere
    HemisphereEast: Hemisphere
    HemisphereWest: Hemisphere

    # Entity concepts
    Taxon: Taxon
    Observation: Observation

    PlantId: rai.Concept
    PlantReference: rai.Concept
    TraitName: rai.Concept
    TraitValue: rai.Concept

    Plant: Plant
    Trait: Trait

    Species: Species

    Hemisphere: Hemisphere
    CalendarEvent: CalendarEvent
    Solstice: Solstice
    Equinox: Equinox

    # Taxonomic hierarchy concepts (rank-views over Taxon)
    TaxonSpecies: TaxonSpecies
    TaxonGenus: TaxonGenus
    TaxonFamily: TaxonFamily
    TaxonOrder: TaxonOrder
    TaxonClass: TaxonClass
    TaxonPhylum: TaxonPhylum
    TaxonKingdom: TaxonKingdom


ARQ_PLAN = ModelPlan(
    steps=(
        NoSourceStep(name="calendar", fn=define_calendar),
        NoSourceStep(name="geography", fn=define_geography),

        TableStep(name="taxon", fn=define_taxon, table="TAXON"),
        EntitySpecStep(name="observation", spec=ObservationSpec, table="OBSERVATION_10k"),
        TableStep(name="plants", fn=define_plants, table="PLANTS"),
        TableStep(name="traits", fn=define_traits, table="PLANT_TRAITS"),

        NoSourceStep(name="species", fn=define_species),
        TableStep(name="soleq", fn=define_solstice_equinox, table="ASTROPIXELS_SOLEQ"),

        NoSourceStep(name="taxonomy", fn=define_taxonomy),
        NoSourceStep(name="derived_observation", fn=define_derived_observation),
    )
)


def define_arq(m: rai.Model, db: str = "TEAM_ARQ", schema: str = "PUBLIC") -> ARQModel:
    """Define the ARQ knowledge graph model.

    Args:
        m: The RAI model to define concepts on
        db: The database name containing source tables
        schema: The schema name containing source tables

    Returns:
        The typed ARQ model
    """
    ARQ_PLAN.apply(m, db=db, schema=schema)

    return cast(ARQModel, m)
