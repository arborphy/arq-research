from typing import Protocol

import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from kg.model.core.calendar import define_calendar
from kg.model.core.geography import define_geography
from kg.model.core.soleq import define_solstice_equinox
from kg.model.core.taxon import define_taxon
from kg.model.core.observation import define_observation
from kg.model.derived.taxonomy import define_taxonomy
from kg.model.derived.observation import define_derived_observation


# Protocol definitions for the attributes dynamically assigned to the model
# Not strictly required, but enables nice autocomplete in the editor
# Claude is good at updating these based on the model files

class Taxon(Protocol):
    id: rai.Relationship
    scientific_name: rai.Relationship
    canonical_name: rai.Relationship
    rank: rai.Relationship
    parent: rai.Relationship
    genus: rai.Relationship
    family: rai.Relationship
    order: rai.Relationship
    class_: rai.Relationship
    phylum: rai.Relationship
    kingdom: rai.Relationship


class Observation(Protocol):
    id: rai.Relationship
    event_datetime: rai.Relationship
    day_of_year: rai.Relationship
    year: rai.Relationship
    basis_of_record: rai.Relationship
    country_code: rai.Relationship
    state_province: rai.Relationship
    latitude: rai.Relationship
    longitude: rai.Relationship
    h3_cell_6: rai.Relationship
    h3_cell_7: rai.Relationship
    h3_cell_8: rai.Relationship
    h3_cell_9: rai.Relationship
    h3_cell_10: rai.Relationship
    classification: rai.Relationship
    hemisphere: rai.Relationship


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


class Species(Taxon, Protocol):
    pass


class Genus(Taxon, Protocol):
    pass


class Family(Taxon, Protocol):
    pass


class Order(Taxon, Protocol):
    pass


class Class(Taxon, Protocol):
    pass


class Phylum(Taxon, Protocol):
    pass


class Kingdom(Taxon, Protocol):
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
    Hemisphere: Hemisphere
    CalendarEvent: CalendarEvent
    Solstice: Solstice
    Equinox: Equinox

    # Taxonomic hierarchy concepts
    Species: Species
    Genus: Genus
    Family: Family
    Order: Order
    Class: Class
    Phylum: Phylum
    Kingdom: Kingdom


def define_arq(m: rai.Model, db: str = "TEAM_ARQ", schema: str = "PUBLIC") -> ARQModel:
    """Define the ARQ knowledge graph model.

    Args:
        m: The RAI model to define concepts on
        db: The database name containing source tables
        schema: The schema name containing source tables

    Returns:
        The typed ARQ model
    """
    # Define source table binding helper
    source = lambda t: Table(f"{db}.{schema}.{t}")

    # Define foundational concepts first (used by other modules)
    define_calendar(m)
    define_geography(m)

    # Define core model and bindings
    define_taxon(m, source("TAXON"))
    define_observation(m, source("OBSERVATION_10k"))
    define_solstice_equinox(m, source("ASTROPIXELS_SOLEQ"))

    # Define derived concepts
    define_taxonomy(m)
    define_derived_observation(m)

    return m
