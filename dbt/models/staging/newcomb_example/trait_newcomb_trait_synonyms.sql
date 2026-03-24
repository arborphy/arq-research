-- Flatten trait-level synonyms from Newcomb ontology
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'newcomb_raw') }}
),

trait_synonyms_flattened as (
    select
        trait.key::string as trait_key,
        trait.value:id::string as trait_id,
        syn.value::string as synonym,
        loaded_at
    from source,
    lateral flatten(input => json_data:traits) trait,
    lateral flatten(input => trait.value:synonyms, outer => true) syn
)

select * from trait_synonyms_flattened
where synonym is not null
