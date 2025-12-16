-- Load local SQLite-exported plant tables into Snowflake
--
-- Usage (after exporting CSVs locally):
--   uvx --from snowflake-cli snow sql -f script/plants.sql -D "path=/abs/path/to/csv_dir"
--
-- Expected files in <path>:
--   plants.csv
--   plant_characteristics.csv
--   plant_native_statuses.csv

use role team_arq;
use database team_arq;
use schema source;

-- Dedicated stage for plant data loads
create stage if not exists team_arq.source.plants;

-- -----------------------------------------------------------------------------
-- Raw table: plants
-- -----------------------------------------------------------------------------
create table if not exists plants
(
    id integer,
    symbol string,
    scientific_name string,
    common_name string,
    group_name string,
    rank_id integer,
    rank string,
    accepted_id integer,
    has_synonyms boolean,
    has_subordinate_taxa boolean,
    has_wildlife boolean,
    has_wetland_data boolean,
    has_images boolean,
    has_related_links boolean,
    has_legal_statuses boolean,
    has_noxious_statuses boolean,
    has_documentation boolean,
    has_distribution_data boolean,
    has_invasive_statuses boolean,
    has_characteristics boolean,
    has_ethnobotany boolean,
    has_pollinator boolean,
    num_images integer,
    profile_image_filename string,
    profile_image_url string,
    image_id integer,
    plant_location_id integer,
    durations string,
    growth_habits string,
    other_common_names string,
    plant_guide_urls string,
    fact_sheet_urls string,
    created_at timestamp_ntz,
    updated_at timestamp_ntz,
    data_checksum string,
    reference string
);

put file://<% path %>/plants.csv @team_arq.source.plants/plants parallel=32;

copy into plants
from @team_arq.source.plants/plants
file_format = (
    type = csv,
    field_delimiter = ',',
    skip_header = 1,
    field_optionally_enclosed_by = '"',
    escape_unenclosed_field = none,
    empty_field_as_null = true
)
;

select count(*) as plants_rows from plants;

-- -----------------------------------------------------------------------------
-- Raw table: plant_characteristics
-- -----------------------------------------------------------------------------
create table if not exists plant_characteristics
(
    id integer,
    plant_id integer,
    active_growth_period string,
    bloat string,
    c_n_ratio string,
    coppice_potential string,
    fall_conspicuous string,
    fire_resistant string,
    flower_color string,
    flower_conspicuous string,
    foliage_color string,
    foliage_porosity_summer string,
    foliage_porosity_winter string,
    foliage_texture string,
    fruit_seed_color string,
    fruit_seed_conspicuous string,
    growth_form string,
    growth_rate string,
    height_at_20_years_maximum_feet string,
    height_mature_feet string,
    known_allelopath string,
    leaf_retention string,
    lifespan string,
    low_growing_grass string,
    nitrogen_fixation string,
    resprout_ability string,
    shape_and_orientation string,
    toxicity string,
    adapted_to_coarse_textured_soils string,
    adapted_to_fine_textured_soils string,
    adapted_to_medium_textured_soils string,
    anaerobic_tolerance string,
    caco_3_tolerance string,
    cold_stratification_required string,
    drought_tolerance string,
    fertility_requirement string,
    fire_tolerance string,
    frost_free_days_minimum string,
    hedge_tolerance string,
    moisture_use string,
    ph_maximum float,
    ph_minimum float,
    planting_density_per_acre_maximum string,
    planting_density_per_acre_minimum string,
    precipitation_maximum string,
    precipitation_minimum string,
    root_depth_minimum string,
    salinity_tolerance string,
    shade_tolerance string,
    temperature_minimum_f string,
    bloom_period string,
    commercial_availability string,
    fruit_seed_abundance string,
    fruit_seed_period_begin string,
    fruit_seed_period_end string,
    fruit_seed_persistence string,
    propagated_by_bare_root string,
    propagated_by_bulb string,
    propagated_by_container string,
    propagated_by_corm string,
    propagated_by_cuttings string,
    propagated_by_seed string,
    propagated_by_sod string,
    propagated_by_sprigs string,
    propagated_by_tubers string,
    seed_per_pound string,
    seed_spread_rate string,
    seedling_vigor string,
    small_grain string,
    vegetative_spread_rate string,
    berry_nut_seed_product string,
    christmas_tree_product string,
    fodder_product string,
    fuelwood_product string,
    lumber_product string,
    naval_store_product string,
    nursery_stock_product string,
    palatable_browse_animal string,
    palatable_human string,
    post_product string,
    pulpwood_product string,
    veneer_product string
);

put file://<% path %>/plant_characteristics.csv @team_arq.source.plants/plant_characteristics parallel=32;

copy into plant_characteristics
from @team_arq.source.plants/plant_characteristics
file_format = (
    type = csv,
    field_delimiter = ',',
    skip_header = 1,
    field_optionally_enclosed_by = '"',
    escape_unenclosed_field = none,
    empty_field_as_null = true
)
;

select count(*) as plant_characteristics_rows from plant_characteristics;

-- -----------------------------------------------------------------------------
-- Raw table: plant_native_statuses
-- -----------------------------------------------------------------------------
create table if not exists plant_native_statuses
(
    id integer,
    plant_id integer,
    region string,
    status string,
    status_type string
);

put file://<% path %>/plant_native_statuses.csv @team_arq.source.plants/plant_native_statuses parallel=32;

copy into plant_native_statuses
from @team_arq.source.plants/plant_native_statuses
file_format = (
    type = csv,
    field_delimiter = ',',
    skip_header = 1,
    field_optionally_enclosed_by = '"',
    escape_unenclosed_field = none,
    empty_field_as_null = true
)
;

select count(*) as plant_native_statuses_rows from plant_native_statuses;
