"""Load GoBotany data from Snowflake into the KG.

Tables consumed:
  - gobotany_taxon                    → Species, Family, Genus + taxonomy hierarchy
  - gobotany_character                → Feature
  - gobotany_character_value_label    → FeatureValue
  - gobotany_species_feature_values   → GoBotanyKey (links Species → FeatureValue)
    (this is a Snowflake view created by scripts/upload_gobotany.py)

GoBotanyKey extends IdentificationKey, so it is automatically included in the
derived Species.feature_values rule in kg/model/derived/species_features.py.
"""
from relationalai.semantics import Integer, String, define, where

from kg.model import m
from kg.model.core.taxonomy import Family, Genus, Species
from kg.model.core.features import Feature, FeatureValue
from kg.model.core.provenance import DataSource
from kg.model.core.keys.gobotany import GoBotanyKey

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

taxon_table = m.Table(f"{DB}.{SCHEMA}.gobotany_taxon", schema={
    "TAXON_ID": Integer,
    "SCIENTIFIC_NAME": String,
    "COMMON_NAME": String,
    "GENUS": String,
    "FAMILY": String,
    "SPECIES_URL": String,
})

# Links taxon_id → (pile_slug, character_short_name, value_index)
tcv_table = m.Table(f"{DB}.{SCHEMA}.gobotany_taxon_character_value", schema={
    "TAXON_ID": Integer,
    "PILE_SLUG": String,
    "CHARACTER_SHORT_NAME": String,
    "VALUE_INDEX": Integer,
})

character_table = m.Table(f"{DB}.{SCHEMA}.gobotany_character", schema={
    "CHARACTER_SHORT_NAME": String,
    "FRIENDLY_NAME": String,
    "CHARACTER_GROUP": String,
    "VALUE_TYPE": String,
})

cvl_table = m.Table(f"{DB}.{SCHEMA}.gobotany_character_value_label", schema={
    "PILE_SLUG": String,
    "CHARACTER_SHORT_NAME": String,
    "VALUE_INDEX": Integer,
    "CHOICE": String,
    "DISPLAY_LABEL": String,
})


# -- DataSource --
define(DataSource.new(name="GoBotany"))

# -- Taxonomy --
define(Family.new(name=taxon_table.FAMILY))
define(Genus.new(name=taxon_table.GENUS))
define(Species.new(name=taxon_table.SCIENTIFIC_NAME))

where(s := Species.filter_by(name=taxon_table.SCIENTIFIC_NAME)).define(
    s.common_name(taxon_table.COMMON_NAME),
    Species.source(s, DataSource.filter_by(name="GoBotany")),
)

where(
    g := Genus.filter_by(name=taxon_table.GENUS),
    f := Family.filter_by(name=taxon_table.FAMILY),
).define(Genus.part_of(g, f))

where(
    s := Species.filter_by(name=taxon_table.SCIENTIFIC_NAME),
    g := Genus.filter_by(name=taxon_table.GENUS),
).define(Species.part_of(s, g))

# -- Features (characters) --
define(Feature.new(name=character_table.CHARACTER_SHORT_NAME))

where(feat := Feature.filter_by(name=character_table.CHARACTER_SHORT_NAME)).define(
    feat.name(character_table.FRIENDLY_NAME),
    Feature.source(feat, DataSource.filter_by(name="GoBotany")),
)

# -- FeatureValues (discrete character values only; skip numeric ranges with NA choice) --
where(cvl_table.CHOICE != "NA").define(FeatureValue.new(value=cvl_table.CHOICE))

where(
    cvl_table.CHOICE != "NA",
    fv := FeatureValue.filter_by(value=cvl_table.CHOICE),
    feat := Feature.filter_by(name=cvl_table.CHARACTER_SHORT_NAME),
).define(
    fv.name(cvl_table.DISPLAY_LABEL),
    FeatureValue.feature(fv, feat),
    FeatureValue.source(fv, DataSource.filter_by(name="GoBotany")),
)

# -- GoBotanyKey: one per (pile, character, value_index) with a valid discrete choice --
where(cvl_table.CHOICE != "NA").define(GoBotanyKey.new(
    pile_slug=cvl_table.PILE_SLUG,
    character_short_name=cvl_table.CHARACTER_SHORT_NAME,
    value_index=cvl_table.VALUE_INDEX,
))

where(
    cvl_table.CHOICE != "NA",
    key := GoBotanyKey.filter_by(
        pile_slug=cvl_table.PILE_SLUG,
        character_short_name=cvl_table.CHARACTER_SHORT_NAME,
        value_index=cvl_table.VALUE_INDEX,
    ),
).define(
    GoBotanyKey.feature(key, Feature.filter_by(name=cvl_table.CHARACTER_SHORT_NAME)),
    GoBotanyKey.feature_value(key, FeatureValue.filter_by(value=cvl_table.CHOICE)),
    GoBotanyKey.source(key, DataSource.filter_by(name="GoBotany")),
)

# -- Link species to keys via taxon_character_value + taxon join --
where(
    tcv_table.TAXON_ID == taxon_table.TAXON_ID,
    key := GoBotanyKey.filter_by(
        pile_slug=tcv_table.PILE_SLUG,
        character_short_name=tcv_table.CHARACTER_SHORT_NAME,
        value_index=tcv_table.VALUE_INDEX,
    ),
    s := Species.filter_by(name=taxon_table.SCIENTIFIC_NAME),
).define(GoBotanyKey.species(key, s))
