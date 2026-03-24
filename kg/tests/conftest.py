"""Shared fixtures for arborphy knowledge graph tests."""

from datetime import date

import pytest
from relationalai.semantics import define

from kg.model.core.taxonomy import (
    Domain, Kingdom, Phylum, Class, Order, Family, Genus, Species, Subspecies, TaxonVariety,
)
from kg.model.core.features import Feature, FeatureValue
from kg.model.core.keys.key import IdentificationKey
from kg.model.core.observations import Observation, GeographicArea
from kg.model.core.environment import EnvironmentDescriptor, EnvironmentValue
from kg.model.core.provenance import DataSource


@pytest.fixture(scope="session")
def blue_aster_hierarchy():
    """Populate the Blue Aster (Symphyotrichum laeve) taxonomy hierarchy.

    Based on the iNaturalist example from docs/DataModel Sketch.md:
    Eukarya -> Plantae -> Tracheophyta -> Magnoliopsida -> Asterales
    -> Asteraceae -> Symphyotrichum -> Symphyotrichum laeve
    """
    define(
        eukarya := Domain.new(name="Eukarya"),
        plantae := Kingdom.new(name="Plantae"),
        tracheophyta := Phylum.new(name="Tracheophyta"),
        magnoliopsida := Class.new(name="Magnoliopsida"),
        asterales := Order.new(name="Asterales"),
        asteraceae := Family.new(name="Asteraceae"),
        symphyotrichum := Genus.new(name="Symphyotrichum"),
        s_laeve := Species.new(
            name="Symphyotrichum laeve",
            inat_link="https://www.inaturalist.org/taxa/129607-Symphyotrichum-laeve",
            inat_taxon_id="129607",
            common_name="smooth blue aster",
            iconic_taxon="Plantae",
        ),
        eukarya.has_part(plantae),
        plantae.has_part(tracheophyta),
        tracheophyta.has_part(magnoliopsida),
        magnoliopsida.has_part(asterales),
        asterales.has_part(asteraceae),
        asteraceae.has_part(symphyotrichum),
        symphyotrichum.has_part(s_laeve),
    )

    return {
        "domain": eukarya,
        "kingdom": plantae,
        "phylum": tracheophyta,
        "class": magnoliopsida,
        "order": asterales,
        "family": asteraceae,
        "genus": symphyotrichum,
        "species": s_laeve,
    }


@pytest.fixture(scope="session")
def newcomb_features():
    """Populate Newcomb's four features and sample values.

    From docs/DataModel Sketch.md:
    - Flower Symmetry
    - Plant Type (with values: Shrubs, Vines, Wildflowers, ...)
    - Leaf Type (with values: No apparent leaves, Leaves entire, ...)
    - Leaf Arrangement
    """
    define(
        flower_symmetry := Feature.new(name="Flower Symmetry"),
        plant_type := Feature.new(name="Plant Type"),
        leaf_type := Feature.new(name="Leaf Type"),
        leaf_arrangement := Feature.new(name="Leaf Arrangement"),
        # Plant Type values
        pt_shrubs := FeatureValue.new(value="Shrubs"),
        pt_vines := FeatureValue.new(value="Vines"),
        pt_wildflowers := FeatureValue.new(value="Wildflowers"),
        pt_shrubs.feature(plant_type),
        pt_vines.feature(plant_type),
        pt_wildflowers.feature(plant_type),
        # Leaf Type values
        lt_none := FeatureValue.new(value="No apparent leaves"),
        lt_entire := FeatureValue.new(value="Leaves entire"),
        lt_toothed := FeatureValue.new(value="Leaves toothed or lobed"),
        lt_divided := FeatureValue.new(value="Leaves divided"),
        lt_none.feature(leaf_type),
        lt_entire.feature(leaf_type),
        lt_toothed.feature(leaf_type),
        lt_divided.feature(leaf_type),
    )

    return {
        "flower_symmetry": flower_symmetry,
        "plant_type": plant_type,
        "leaf_type": leaf_type,
        "leaf_arrangement": leaf_arrangement,
        "plant_type_values": [pt_shrubs, pt_vines, pt_wildflowers],
        "leaf_type_values": [lt_none, lt_entire, lt_toothed, lt_divided],
    }


@pytest.fixture(scope="session")
def inat_source():
    """Create an iNaturalist data source."""
    define(
        source := DataSource.new(
            name="iNaturalist",
            as_of_date="2025-01-15",
        ),
    )
    return source


@pytest.fixture(scope="session")
def newcomb_source():
    """Create a Newcomb Field Guide data source."""
    define(
        source := DataSource.new(
            name="Newcomb's Wildflower Guide",
            as_of_date="1977-01-01",
        ),
    )
    return source


@pytest.fixture(scope="session")
def taxon_variety_fixture(blue_aster_hierarchy):
    """Create a Subspecies and TaxonVariety under Symphyotrichum laeve."""
    define(
        subsp := Subspecies.new(name="Symphyotrichum laeve var. laeve"),
        variety := TaxonVariety.new(name="smooth"),
        blue_aster_hierarchy["species"].has_part(subsp),
        subsp.has_part(variety),
    )
    return {"subspecies": subsp, "variety": variety}
