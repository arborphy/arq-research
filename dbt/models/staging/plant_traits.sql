-- needed for RAI
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

-- Convert the wide `plant_characteristics` row into (plant_id, trait_name, trait_value)
-- so downstream models (e.g. the RAI semantic layer) can treat each characteristic as a trait.

with pc as (
    select
        * exclude (PH_MAXIMUM, PH_MINIMUM),
        to_varchar(PH_MAXIMUM) as PH_MAXIMUM,
        to_varchar(PH_MINIMUM) as PH_MINIMUM
    from {{ ref('plant_characteristics') }}
),

unp as (
    select
        PLANT_ID,
        TRAIT_NAME,
        TRAIT_VALUE
    from pc
    unpivot(
        TRAIT_VALUE for TRAIT_NAME in (
            ACTIVE_GROWTH_PERIOD,
            BLOAT,
            C_N_RATIO,
            COPPICE_POTENTIAL,
            FALL_CONSPICUOUS,
            FIRE_RESISTANT,
            FLOWER_COLOR,
            FLOWER_CONSPICUOUS,
            FOLIAGE_COLOR,
            FOLIAGE_POROSITY_SUMMER,
            FOLIAGE_POROSITY_WINTER,
            FOLIAGE_TEXTURE,
            FRUIT_SEED_COLOR,
            FRUIT_SEED_CONSPICUOUS,
            GROWTH_FORM,
            GROWTH_RATE,
            HEIGHT_AT_20_YEARS_MAXIMUM_FEET,
            HEIGHT_MATURE_FEET,
            KNOWN_ALLELOPATH,
            LEAF_RETENTION,
            LIFESPAN,
            LOW_GROWING_GRASS,
            NITROGEN_FIXATION,
            RESPROUT_ABILITY,
            SHAPE_AND_ORIENTATION,
            TOXICITY,
            ADAPTED_TO_COARSE_TEXTURED_SOILS,
            ADAPTED_TO_FINE_TEXTURED_SOILS,
            ADAPTED_TO_MEDIUM_TEXTURED_SOILS,
            ANAEROBIC_TOLERANCE,
            CACO_3_TOLERANCE,
            COLD_STRATIFICATION_REQUIRED,
            DROUGHT_TOLERANCE,
            FERTILITY_REQUIREMENT,
            FIRE_TOLERANCE,
            FROST_FREE_DAYS_MINIMUM,
            HEDGE_TOLERANCE,
            MOISTURE_USE,
            PH_MAXIMUM,
            PH_MINIMUM,
            PLANTING_DENSITY_PER_ACRE_MAXIMUM,
            PLANTING_DENSITY_PER_ACRE_MINIMUM,
            PRECIPITATION_MAXIMUM,
            PRECIPITATION_MINIMUM,
            ROOT_DEPTH_MINIMUM,
            SALINITY_TOLERANCE,
            SHADE_TOLERANCE,
            TEMPERATURE_MINIMUM_F,
            BLOOM_PERIOD,
            COMMERCIAL_AVAILABILITY,
            FRUIT_SEED_ABUNDANCE,
            FRUIT_SEED_PERIOD_BEGIN,
            FRUIT_SEED_PERIOD_END,
            FRUIT_SEED_PERSISTENCE,
            PROPAGATED_BY_BARE_ROOT,
            PROPAGATED_BY_BULB,
            PROPAGATED_BY_CONTAINER,
            PROPAGATED_BY_CORM,
            PROPAGATED_BY_CUTTINGS,
            PROPAGATED_BY_SEED,
            PROPAGATED_BY_SOD,
            PROPAGATED_BY_SPRIGS,
            PROPAGATED_BY_TUBERS,
            SEED_PER_POUND,
            SEED_SPREAD_RATE,
            SEEDLING_VIGOR,
            SMALL_GRAIN,
            VEGETATIVE_SPREAD_RATE,
            BERRY_NUT_SEED_PRODUCT,
            CHRISTMAS_TREE_PRODUCT,
            FODDER_PRODUCT,
            FUELWOOD_PRODUCT,
            LUMBER_PRODUCT,
            NAVAL_STORE_PRODUCT,
            NURSERY_STOCK_PRODUCT,
            PALATABLE_BROWSE_ANIMAL,
            PALATABLE_HUMAN,
            POST_PRODUCT,
            PULPWOOD_PRODUCT,
            VENEER_PRODUCT
        )
    )
)

select
    PLANT_ID,
    TRAIT_NAME,
    nullif(trim(to_varchar(TRAIT_VALUE)), '') as TRAIT_VALUE
from unp
where TRAIT_VALUE is not null
