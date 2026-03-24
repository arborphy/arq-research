-- Flatten synonym sources from trait_synonyms.json
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'synonyms_raw') }}
),

sources_flattened as (
    select
        src.key::string as source_id,
        src.value:name::string as source_name,
        src.value:author::string as author,
        src.value:illustrator::string as illustrator,
        src.value:publisher::string as publisher,
        src.value:type::string as source_type,
        src.value:year::integer as year,
        src.value:isbn::string as isbn,
        src.value:doi::string as doi,
        src.value:journal::string as journal,
        src.value:url::string as url,
        src.value:repository::string as repository,
        src.value:institution::string as institution,
        src.value:growthHabitSearch::string as growth_habit_search,
        src.value:verified::boolean as verified,
        src.value:description::string as description,
        loaded_at
    from source,
    lateral flatten(input => json_data:sources) src
)

select * from sources_flattened
