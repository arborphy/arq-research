-- Flatten trait values (including nested values) from Newcomb ontology
-- Handles 2-level nesting: trait -> value -> nested_value
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'newcomb_raw') }}
),

-- First level: direct trait values
trait_values_level1 as (
    select
        trait.key::string as trait_key,
        trait.value:id::string as trait_id,
        val.value:id::string as value_id,
        val.value:label::string as label,
        val.value:description::string as description,
        val.value:newcombOriginal::boolean as newcomb_original,
        null::string as parent_value_id,
        1 as nesting_level,
        loaded_at
    from source,
    lateral flatten(input => json_data:traits) trait,
    lateral flatten(input => trait.value:values, outer => true) val
    where val.value:id is not null
),

-- Second level: nested values within trait values
trait_values_level2 as (
    select
        trait.key::string as trait_key,
        trait.value:id::string as trait_id,
        nested_val.value:id::string as value_id,
        nested_val.value:label::string as label,
        nested_val.value:description::string as description,
        nested_val.value:newcombOriginal::boolean as newcomb_original,
        val.value:id::string as parent_value_id,
        2 as nesting_level,
        loaded_at
    from source,
    lateral flatten(input => json_data:traits) trait,
    lateral flatten(input => trait.value:values, outer => true) val,
    lateral flatten(input => val.value:values, outer => true) nested_val
    where nested_val.value:id is not null
),

-- Union both levels
all_values as (
    select * from trait_values_level1
    union all
    select * from trait_values_level2
)

select * from all_values
