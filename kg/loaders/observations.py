"""Load observations from Snowflake stg_observations into the KG.

Maps stg_observations columns to:
  - Observation (with all properties)
  - Species (linked via scientific_name)
  - H3Cell at resolutions 7, 9, 12 (with parent hierarchy)
"""
from relationalai.semantics import Bool, Date, Float, Int64, Integer, String, define, where

from kg.model import m
from kg.model.core.taxonomy import Species
from kg.model.core.observations import Observation
from kg.model.core.h3cell import H3Cell
from kg.model.core.provenance import DataSource

DB = "chaker_temp"
SCHEMA = "public_arborphy"

obs_table = m.Table(f"{DB}.{SCHEMA}.stg_observations", schema={
    "ID": String,
    "UUID": String,
    "SCIENTIFIC_NAME": String,
    "COMMON_NAME": String,
    "TAXON_ID": String,
    "ICONIC_TAXON_NAME": String,
    "OBSERVED_ON": Date,
    "TIME_OBSERVED_AT": String,
    "LATITUDE": Float,
    "LONGITUDE": Float,
    "POSITIONAL_ACCURACY": Float,
    "COORDINATES_OBSCURED": Bool,
    "IMAGE_URL": String,
    "URL": String,
    "QUALITY_GRADE": String,
    "NUM_IDENTIFICATION_AGREEMENTS": Integer,
    "NUM_IDENTIFICATION_DISAGREEMENTS": Integer,
    "CAPTIVE_CULTIVATED": Bool,
    "PLACE_GUESS": String,
    "SPECIES_GUESS": String,
    "DESCRIPTION": String,
    "LICENSE": String,
    "H3_RES7": Int64,
    "H3_RES9": Int64,
    "H3_RES12": Int64,
})

# -- Data Source --
define(DataSource.new(name="iNaturalist"))

# -- Species (create) --
define(Species.new(name=obs_table.SCIENTIFIC_NAME))

# -- Species (properties) --
where(
    species := Species.filter_by(name=obs_table.SCIENTIFIC_NAME),
).define(
    species.common_name(obs_table.COMMON_NAME),
    species.inat_taxon_id(obs_table.TAXON_ID),
    species.iconic_taxon(obs_table.ICONIC_TAXON_NAME),
    Species.source(species, DataSource.filter_by(name="iNaturalist")),
)

# -- H3 Cells (create) --
define(H3Cell.new(index=obs_table.H3_RES7))
define(H3Cell.new(index=obs_table.H3_RES9))
define(H3Cell.new(index=obs_table.H3_RES12))

# -- H3 Cells (properties + parent hierarchy) --
where(cell7 := H3Cell.filter_by(index=obs_table.H3_RES7)).define(
    cell7.resolution(7),
)
where(cell9 := H3Cell.filter_by(index=obs_table.H3_RES9)).define(
    cell9.resolution(9),
    cell9.part_of(H3Cell.filter_by(index=obs_table.H3_RES7)),
)
where(cell12 := H3Cell.filter_by(index=obs_table.H3_RES12)).define(
    cell12.resolution(12),
    cell12.part_of(H3Cell.filter_by(index=obs_table.H3_RES9)),
)

# -- Observations (create) --
define(Observation.new(inat_id=obs_table.ID))

# -- Observations (properties + relationships) --
where(obs := Observation.filter_by(inat_id=obs_table.ID)).define(
    obs.uuid(obs_table.UUID),
    obs.date(obs_table.OBSERVED_ON),
    obs.time_observed_at(obs_table.TIME_OBSERVED_AT),
    obs.latitude(obs_table.LATITUDE),
    obs.longitude(obs_table.LONGITUDE),
    obs.positional_accuracy(obs_table.POSITIONAL_ACCURACY),
    obs.coordinates_obscured(obs_table.COORDINATES_OBSCURED),
    obs.image_url(obs_table.IMAGE_URL),
    obs.url(obs_table.URL),
    obs.quality_grade(obs_table.QUALITY_GRADE),
    obs.num_identification_agreements(obs_table.NUM_IDENTIFICATION_AGREEMENTS),
    obs.num_identification_disagreements(obs_table.NUM_IDENTIFICATION_DISAGREEMENTS),
    obs.captive_cultivated(obs_table.CAPTIVE_CULTIVATED),
    obs.place_guess(obs_table.PLACE_GUESS),
    obs.species_guess(obs_table.SPECIES_GUESS),
    obs.description(obs_table.DESCRIPTION),
    obs.license(obs_table.LICENSE),
    Observation.source(obs, DataSource.filter_by(name="iNaturalist")),
    Observation.species(obs, Species.filter_by(name=obs_table.SCIENTIFIC_NAME)),
    Observation.h3cell(obs, H3Cell.filter_by(index=obs_table.H3_RES9)),
)
