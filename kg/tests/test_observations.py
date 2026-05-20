"""Tests for observation and geographic area use cases.

Verifies iNaturalist-style observations with GPS coordinates, species
links, geographic area hierarchies, and environment descriptors.
Based on the Quest Maker use cases from docs/example_queries.md.
"""

from datetime import date

import pytest
from relationalai.semantics import define, select, where

from kg.model.core.taxonomy import Species
from kg.model.core.observations import Observation, GeographicArea
from kg.model.core.environment import EnvironmentDescriptor, EnvironmentValue
from kg.model.core.predicates import located_in


@pytest.fixture
def observation_data(blue_aster_hierarchy):
    """Create sample observations of Blue Aster in Vermont."""
    define(
        # Geographic areas
        vermont := GeographicArea.new(name="Vermont", type="state"),
        marsh_billings := GeographicArea.new(
            name="Marsh-Billings-Rockefeller NHP", type="park",
        ),
        located_in(marsh_billings, vermont),
        # Environment
        habitat := EnvironmentDescriptor.new(name="Habitat"),
        meadow := EnvironmentValue.new(value="Meadow"),
        meadow.descriptor(habitat),
        marsh_billings.environment(meadow),
        # Observations
        obs1 := Observation.new(
            date=date(2024, 7, 15),
            latitude=43.6313,
            longitude=-72.5340,
            image_url="https://inaturalist-open-data.s3.amazonaws.com/photos/example1.jpg",
        ),
        obs2 := Observation.new(
            date=date(2024, 8, 2),
            latitude=43.6320,
            longitude=-72.5350,
        ),
        obs1.species(blue_aster_hierarchy["species"]),
        obs2.species(blue_aster_hierarchy["species"]),
        obs1.area(marsh_billings),
        obs2.area(marsh_billings),
    )

    return {
        "vermont": vermont,
        "park": marsh_billings,
        "habitat": habitat,
        "meadow": meadow,
        "obs1": obs1,
        "obs2": obs2,
    }


class TestObservations:
    """Verify observation creation and querying."""

    def test_observation_has_date(self, observation_data):
        """Query observation by date."""
        df = where(Observation.date == date(2024, 7, 15)).select(
            Observation.date, Observation.latitude, Observation.longitude
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["latitude"] == 43.6313

    def test_observation_has_image(self, observation_data):
        """Query observation with image URL."""
        df = where(Observation.date == date(2024, 7, 15)).select(
            Observation.image_url
        ).to_df()
        assert len(df) == 1
        assert "inaturalist" in df.iloc[0]["image_url"]

    def test_observation_links_to_species(self, observation_data):
        """Observation should link to Symphyotrichum laeve."""
        obs_species = Observation.species
        df = where(
            Observation.date == date(2024, 7, 15),
        ).select(obs_species.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Symphyotrichum laeve"

    def test_multiple_observations_of_species(self, observation_data):
        """Multiple observations can link to the same species."""
        obs_species = Observation.species
        df = where(
            obs_species.name == "Symphyotrichum laeve",
        ).select(Observation.date).to_df()
        dates = df["date"].dt.date.tolist()
        assert date(2024, 7, 15) in dates
        assert date(2024, 8, 2) in dates


class TestGeographicAreas:
    """Verify geographic area hierarchies."""

    def test_area_exists(self, observation_data):
        """Query a geographic area by name and type."""
        df = where(GeographicArea.name == "Vermont").select(
            GeographicArea.name, GeographicArea.type
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["type"] == "state"

    def test_area_part_of(self, observation_data):
        """Park should be part of Vermont."""
        parent = GeographicArea.part_of
        df = where(
            GeographicArea.name == "Marsh-Billings-Rockefeller NHP",
        ).select(parent.name.alias("parent_name")).to_df()
        assert len(df) == 1
        assert df.iloc[0]["parent_name"] == "Vermont"

    def test_observation_in_area(self, observation_data):
        """Observations should be located in the park."""
        obs_area = Observation.area
        df = where(
            Observation.date == date(2024, 7, 15),
        ).select(obs_area.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Marsh-Billings-Rockefeller NHP"

    def test_area_has_environment(self, observation_data):
        """Park should have Meadow environment."""
        env = GeographicArea.environment
        df = where(
            GeographicArea.name == "Marsh-Billings-Rockefeller NHP",
        ).select(env.value).to_df()
        values = df["value"].tolist()
        assert "Meadow" in values


class TestQuestMakerQuery:
    """Verify the Quest Maker use case: location -> species -> features."""

    def test_species_at_location(self, observation_data):
        """Find species observed at a specific park."""
        obs_species = Observation.species
        obs_area = Observation.area
        df = where(
            obs_area.name == "Marsh-Billings-Rockefeller NHP",
        ).select(obs_species.name).to_df()
        names = df["name"].tolist()
        assert "Symphyotrichum laeve" in names

    def test_environment_at_observation_location(self, observation_data):
        """Find environment descriptors where species were observed."""
        obs_area = Observation.area
        area_env = obs_area.environment
        df = where(
            Observation.date == date(2024, 7, 15),
        ).select(area_env.value).to_df()
        values = df["value"].tolist()
        assert "Meadow" in values


@pytest.fixture
def full_observation_data(blue_aster_hierarchy):
    """Observation with all properties populated, mirroring an iNaturalist CSV row."""
    define(
        obs := Observation.new(
            inat_id="3257308",
            uuid="23b29ee6-c20b-432c-ae12-a9f95efab233",
            date=date(2016, 4, 30),
            time_observed_at="2016-04-30 23:40:24 UTC",
            latitude=41.2443031414,
            longitude=-73.5932051242,
            positional_accuracy=345.0,
            coordinates_obscured=False,
            image_url="https://inaturalist-open-data.s3.amazonaws.com/photos/3767447/medium.jpg",
            url="http://www.inaturalist.org/observations/3257308",
            quality_grade="research",
            num_identification_agreements=3,
            num_identification_disagreements=0,
            captive_cultivated=False,
            place_guess="Ward Pound Ridge Reservation, Pound Ridge, NY, US",
            species_guess="Panax trifolius",
            license="CC-BY-NC",
        ),
        obs.species(blue_aster_hierarchy["species"]),
    )
    return {"obs": obs}


class TestObservationProperties:
    """Verify all new Observation properties from iNaturalist observations.csv."""

    def test_inat_id(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.inat_id).to_df()
        assert len(df) == 1
        assert df.iloc[0]["inat_id"] == "3257308"

    def test_uuid(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.uuid).to_df()
        assert len(df) == 1
        assert df.iloc[0]["uuid"] == "23b29ee6-c20b-432c-ae12-a9f95efab233"

    def test_time_observed_at(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.time_observed_at).to_df()
        assert len(df) == 1
        assert df.iloc[0]["time_observed_at"] == "2016-04-30 23:40:24 UTC"

    def test_quality_grade(self, full_observation_data):
        df = where(Observation.quality_grade == "research").select(
            Observation.inat_id, Observation.quality_grade
        ).to_df()
        assert len(df) >= 1
        assert "3257308" in df["inat_id"].tolist()

    def test_num_identification_agreements(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(
            Observation.num_identification_agreements
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["num_identification_agreements"] == 3

    def test_num_identification_disagreements(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(
            Observation.num_identification_disagreements
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["num_identification_disagreements"] == 0

    def test_captive_cultivated(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(
            Observation.captive_cultivated
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["captive_cultivated"] == False  # noqa: E712

    def test_place_guess(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.place_guess).to_df()
        assert len(df) == 1
        assert "Pound Ridge" in df.iloc[0]["place_guess"]

    def test_positional_accuracy(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(
            Observation.positional_accuracy
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["positional_accuracy"] == 345.0

    def test_coordinates_obscured(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(
            Observation.coordinates_obscured
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["coordinates_obscured"] == False  # noqa: E712

    def test_image_url(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.image_url).to_df()
        assert len(df) == 1
        assert "inaturalist" in df.iloc[0]["image_url"]

    def test_url(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.url).to_df()
        assert len(df) == 1
        assert "inaturalist.org/observations/3257308" in df.iloc[0]["url"]

    def test_species_guess(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.species_guess).to_df()
        assert len(df) == 1
        assert df.iloc[0]["species_guess"] == "Panax trifolius"

    def test_license(self, full_observation_data):
        df = where(Observation.inat_id == "3257308").select(Observation.license).to_df()
        assert len(df) == 1
        assert df.iloc[0]["license"] == "CC-BY-NC"
