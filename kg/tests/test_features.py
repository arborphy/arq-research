"""Tests for feature and feature-value use cases.

Verifies Newcomb's wildflower guide features (Flower Symmetry, Plant Type,
Leaf Type, Leaf Arrangement) and their values using RAI queries.
"""

from relationalai.semantics import define, select, where

from kg.model.core.features import Feature, FeatureValue


class TestNewcombFeatures:
    """Verify the four Newcomb features are created correctly."""

    def test_four_features_exist(self, newcomb_features):
        """All four Newcomb features should be queryable."""
        df = select(Feature.name).to_df()
        names = df["name"].tolist()
        assert "Flower Symmetry" in names
        assert "Plant Type" in names
        assert "Leaf Type" in names
        assert "Leaf Arrangement" in names

    def test_feature_query_by_name(self, newcomb_features):
        """Query a specific feature by name."""
        df = where(Feature.name == "Plant Type").select(Feature.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Plant Type"


class TestFeatureValues:
    """Verify feature values and their relationships to features."""

    def test_plant_type_values(self, newcomb_features):
        """Plant Type should have Shrubs, Vines, Wildflowers values."""
        feature = FeatureValue.feature
        df = where(
            feature.name == "Plant Type",
        ).select(FeatureValue.value).to_df()
        values = df["value"].tolist()
        assert "Shrubs" in values
        assert "Vines" in values
        assert "Wildflowers" in values
        assert len(values) == 3

    def test_leaf_type_values(self, newcomb_features):
        """Leaf Type should have four values."""
        feature = FeatureValue.feature
        df = where(
            feature.name == "Leaf Type",
        ).select(FeatureValue.value).to_df()
        values = df["value"].tolist()
        assert "No apparent leaves" in values
        assert "Leaves entire" in values
        assert "Leaves toothed or lobed" in values
        assert "Leaves divided" in values
        assert len(values) == 4

    def test_value_belongs_to_one_feature(self, newcomb_features):
        """Each value should belong to exactly one feature."""
        feature = FeatureValue.feature
        df = where(
            FeatureValue.value == "Shrubs",
        ).select(feature.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Plant Type"

    def test_add_new_feature_value(self, newcomb_features):
        """Add a new value to an existing feature and query it."""
        define(
            pt_trees := FeatureValue.new(value="Trees"),
            pt_trees.feature(newcomb_features["plant_type"]),
        )

        feature = FeatureValue.feature
        df = where(
            feature.name == "Plant Type",
        ).select(FeatureValue.value).to_df()
        values = df["value"].tolist()
        assert "Trees" in values
