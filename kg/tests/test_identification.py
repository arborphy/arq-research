"""Tests for identification key use cases.

Verifies that identification keys link species to feature-value pairs
with data source provenance, as described in docs/DataModel Sketch.md.
"""

import pytest
from relationalai.semantics import define, select, where

from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, FeatureValue
from kg.model.core.keys.key import IdentificationKey
from kg.model.core.provenance import DataSource


@pytest.fixture
def blue_aster_id_key(blue_aster_hierarchy, newcomb_features, newcomb_source):
    """Create an identification key for Blue Aster with Newcomb features."""
    define(
        key := IdentificationKey.new(
            name="Newcomb Key: Blue Aster",
            value="Group 5",
        ),
        key.species(blue_aster_hierarchy["species"]),
        key.feature(newcomb_features["plant_type"]),
        key.feature_value(newcomb_features["plant_type_values"][2]),  # Wildflowers
        key.source(newcomb_source),
    )
    return key


class TestIdentificationKeys:
    """Verify identification key creation and querying."""

    def test_key_exists(self, blue_aster_id_key):
        """Query that the identification key was created."""
        df = where(
            IdentificationKey.name == "Newcomb Key: Blue Aster"
        ).select(IdentificationKey.name, IdentificationKey.value).to_df()
        assert len(df) == 1
        assert df.iloc[0]["value"] == "Group 5"

    def test_key_identifies_species(self, blue_aster_id_key):
        """Key should link to Symphyotrichum laeve."""
        key_species = IdentificationKey.species
        df = where(
            IdentificationKey.name == "Newcomb Key: Blue Aster",
        ).select(key_species.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Symphyotrichum laeve"

    def test_key_has_feature(self, blue_aster_id_key):
        """Key should link to Plant Type feature."""
        key_feature = IdentificationKey.feature
        df = where(
            IdentificationKey.name == "Newcomb Key: Blue Aster",
        ).select(key_feature.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Plant Type"

    def test_key_has_feature_value(self, blue_aster_id_key):
        """Key should link to Wildflowers feature value."""
        key_fv = IdentificationKey.feature_value
        df = where(
            IdentificationKey.name == "Newcomb Key: Blue Aster",
        ).select(key_fv.value).to_df()
        assert len(df) == 1
        assert df.iloc[0]["value"] == "Wildflowers"

    def test_key_from_source(self, blue_aster_id_key):
        """Key should trace back to Newcomb's Wildflower Guide."""
        key_source = IdentificationKey.source
        df = where(
            IdentificationKey.name == "Newcomb Key: Blue Aster",
        ).select(key_source.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Newcomb's Wildflower Guide"


class TestSpeciesLookupByFeatures:
    """Verify species lookup via identification keys and features."""

    def test_find_species_by_feature_value(self, blue_aster_id_key):
        """Find species identified by a Wildflowers plant type key."""
        key_species = IdentificationKey.species
        key_fv = IdentificationKey.feature_value
        df = where(
            key_fv.value == "Wildflowers",
        ).select(key_species.name).to_df()
        names = df["name"].tolist()
        assert "Symphyotrichum laeve" in names

    def test_find_species_by_feature_and_source(self, blue_aster_id_key):
        """Find species from Newcomb guide with Wildflowers plant type."""
        key_species = IdentificationKey.species
        key_fv = IdentificationKey.feature_value
        key_source = IdentificationKey.source
        df = where(
            key_fv.value == "Wildflowers",
            key_source.name == "Newcomb's Wildflower Guide",
        ).select(key_species.name).to_df()
        names = df["name"].tolist()
        assert "Symphyotrichum laeve" in names
