"""Load Newcomb species data from Snowflake into the KG.

Maps stg_newcomb_species columns to:
  - Species (linked via species_inat)
  - Feature / FeatureValue (flower_type, plant_type, leaf_type)
  - NewcombKey (identified by flower_type + plant_type + leaf_type)
  - DataSource (Newcomb's Wildflower Guide)
"""
from relationalai.semantics import String, define, where

from kg.model import m
from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, FeatureValue
from kg.model.core.keys.newcomb import NewcombKey
from kg.model.core.provenance import DataSource

DB = "chaker_temp"
SCHEMA = "public_arborphy"

newcomb_table = m.Table(f"{DB}.{SCHEMA}.stg_newcomb_species", schema={
    "SPECIES_INAT": String,
    "SPECIES_INAT_LINK": String,
    "KEY_FLOWER_TYPE": String,
    "KEY_PLANT_TYPE": String,
    "KEY_LEAF_TYPE": String,
    "KEY_GROUP_NUMBER": String,
})

# -- Static entities --
define(
    DataSource.new(name="Newcomb's Wildflower Guide"),
    Feature.new(name="flower_type"),
    Feature.new(name="plant_type"),
    Feature.new(name="leaf_type"),
)

# -- Species --
define(Species.new(name=newcomb_table.SPECIES_INAT))

where(species := Species.filter_by(name=newcomb_table.SPECIES_INAT)).define(
    species.inat_link(newcomb_table.SPECIES_INAT_LINK),
    Species.source(species, DataSource.filter_by(name="Newcomb's Wildflower Guide")),
)

# -- FeatureValues --
define(FeatureValue.new(value=newcomb_table.KEY_FLOWER_TYPE))
define(FeatureValue.new(value=newcomb_table.KEY_PLANT_TYPE))
define(FeatureValue.new(value=newcomb_table.KEY_LEAF_TYPE))

where(fv := FeatureValue.filter_by(value=newcomb_table.KEY_FLOWER_TYPE)).define(
    fv.name(newcomb_table.KEY_FLOWER_TYPE),
    FeatureValue.feature(fv, Feature.filter_by(name="flower_type")),
)
where(fv := FeatureValue.filter_by(value=newcomb_table.KEY_PLANT_TYPE)).define(
    fv.name(newcomb_table.KEY_PLANT_TYPE),
    FeatureValue.feature(fv, Feature.filter_by(name="plant_type")),
)
where(fv := FeatureValue.filter_by(value=newcomb_table.KEY_LEAF_TYPE)).define(
    fv.name(newcomb_table.KEY_LEAF_TYPE),
    FeatureValue.feature(fv, Feature.filter_by(name="leaf_type")),
)

# -- NewcombKey (identified by the 3 trait values) --
define(NewcombKey.new(
    flower_type=newcomb_table.KEY_FLOWER_TYPE,
    plant_type=newcomb_table.KEY_PLANT_TYPE,
    leaf_type=newcomb_table.KEY_LEAF_TYPE,
))

where(key := NewcombKey.filter_by(
    flower_type=newcomb_table.KEY_FLOWER_TYPE,
    plant_type=newcomb_table.KEY_PLANT_TYPE,
    leaf_type=newcomb_table.KEY_LEAF_TYPE,
)).define(
    key.group_number(newcomb_table.KEY_GROUP_NUMBER),
    NewcombKey.species(key, Species.filter_by(name=newcomb_table.SPECIES_INAT)),
    NewcombKey.source(key, DataSource.filter_by(name="Newcomb's Wildflower Guide")),
    NewcombKey.feature_value(key, FeatureValue.filter_by(value=newcomb_table.KEY_FLOWER_TYPE)),
    NewcombKey.feature_value(key, FeatureValue.filter_by(value=newcomb_table.KEY_PLANT_TYPE)),
    NewcombKey.feature_value(key, FeatureValue.filter_by(value=newcomb_table.KEY_LEAF_TYPE)),
)
