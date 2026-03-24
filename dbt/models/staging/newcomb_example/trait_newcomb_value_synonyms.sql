-- Flatten value-level synonyms from Newcomb ontology
-- Handles synonyms at both nesting levels
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'newcomb_raw') }}
),

-- Synonyms from first-level values
value_synonyms_level1 as (
    select
        trait.key::string as trait_key,
        trait.value:id::string as trait_id,
        val.value:id::string as value_id,
        syn.value::string as synonym,
        1 as nesting_level,
        loaded_at
    from source,
    lateral flatten(input => json_data:traits) trait,
    lateral flatten(input => trait.value:values, outer => true) val,
    lateral flatten(input => val.value:synonyms, outer => true) syn
    where val.value:id is not null
      and syn.value is not null
),

-- Synonyms from second-level (nested) values
value_synonyms_level2 as (
    select
        trait.key::string as trait_key,
        trait.value:id::string as trait_id,
        nested_val.value:id::string as value_id,
        syn.value::string as synonym,
        2 as nesting_level,
        loaded_at
    from source,
    lateral flatten(input => json_data:traits) trait,
    lateral flatten(input => trait.value:values, outer => true) val,
    lateral flatten(input => val.value:values, outer => true) nested_val,
    lateral flatten(input => nested_val.value:synonyms, outer => true) syn
    where nested_val.value:id is not null
      and syn.value is not null
),

-- Union both levels
all_synonyms as (
    select * from value_synonyms_level1
    union all
    select * from value_synonyms_level2
)

select * from all_synonyms
