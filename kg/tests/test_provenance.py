"""Tests for data source provenance use cases.

Verifies that data sources are created with name and as_of_date,
and that provenance tracking works across the knowledge graph.
"""

from relationalai.semantics import define, select, where

from kg.model.core.provenance import DataSource
from kg.model.core.taxonomy import Species
from kg.model.core.keys.key import Description


class TestDataSources:
    """Verify data source creation and querying."""

    def test_inat_source_exists(self, inat_source):
        """Query the iNaturalist data source."""
        df = where(DataSource.name == "iNaturalist").select(
            DataSource.name, DataSource.as_of_date
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["as_of_date"] == "2025-01-15"

    def test_newcomb_source_exists(self, newcomb_source):
        """Query the Newcomb Field Guide data source."""
        df = where(
            DataSource.name == "Newcomb's Wildflower Guide"
        ).select(DataSource.name, DataSource.as_of_date).to_df()
        assert len(df) == 1
        assert df.iloc[0]["as_of_date"] == "1977-01-01"

    def test_multiple_sources(self, inat_source, newcomb_source):
        """Both data sources should be queryable."""
        df = select(DataSource.name).to_df()
        names = df["name"].tolist()
        assert "iNaturalist" in names
        assert "Newcomb's Wildflower Guide" in names

    def test_add_new_source(self):
        """Create and query a new data source."""
        define(
            DataSource.new(
                name="USDA Plants Database",
                as_of_date="2024-12-01",
            ),
        )

        df = where(
            DataSource.name == "USDA Plants Database"
        ).select(DataSource.as_of_date).to_df()
        assert len(df) == 1
        assert df.iloc[0]["as_of_date"] == "2024-12-01"


class TestProvenanceTracking:
    """Verify end-to-end provenance from data source to species."""

    def test_trace_species_to_source(self, blue_aster_hierarchy, newcomb_source):
        """Create a key and trace from species back to its data source."""
        define(
            key := Description.new(name="Provenance Test Key", version="test"),
            key.describes(blue_aster_hierarchy["species"]),
            key.source(newcomb_source),
        )

        key_species = Description.describes
        key_source = Description.source
        df = where(
            key_species.name == "Symphyotrichum laeve",
            Description.name == "Provenance Test Key",
        ).select(key_source.name, key_source.as_of_date).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Newcomb's Wildflower Guide"
        assert df.iloc[0]["as_of_date"] == "1977-01-01"

    def test_find_all_sources_for_species(self, blue_aster_hierarchy, inat_source):
        """Find all data sources linked to a species via identification keys."""
        define(
            key_inat := Description.new(name="iNat Key: Blue Aster", version="test"),
            key_inat.describes(blue_aster_hierarchy["species"]),
            key_inat.source(inat_source),
        )

        key_species = Description.describes
        key_source = Description.source
        df = where(
            key_species.name == "Symphyotrichum laeve",
        ).select(key_source.name).to_df()
        source_names = df["name"].tolist()
        assert "iNaturalist" in source_names
