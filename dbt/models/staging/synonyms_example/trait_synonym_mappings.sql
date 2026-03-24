-- Flatten synonym-to-source mappings from trait_synonyms.json
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'synonyms_raw') }}
),

mappings_flattened as (
    select
        mapping.key::string as synonym,
        src_id.value::string as source_id,
        loaded_at
    from source,
    lateral flatten(input => json_data:synonymToSource) mapping,
    lateral flatten(input => mapping.value, outer => true) src_id
    where src_id.value is not null
)

select * from mappings_flattened
