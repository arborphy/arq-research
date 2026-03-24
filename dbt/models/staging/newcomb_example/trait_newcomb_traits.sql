-- Flatten top-level trait categories from Newcomb ontology
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'newcomb_raw') }}
),

traits_flattened as (
    select
        trait.key::string as trait_key,
        trait.value:id::string as trait_id,
        trait.value:description::string as description,
        loaded_at
    from source,
    lateral flatten(input => json_data:traits) trait
)

select * from traits_flattened
