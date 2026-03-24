-- Flatten synonym definitions from trait_synonyms.json
-- Extracts definitions nested under category sections
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'synonyms_raw') }}
),

definitions_flattened as (
    select
        category.key::string as category,
        defn.key::string as synonym,
        defn.value:definition::string as definition,
        defn.value:commonLanguageDefinition::string as common_language_definition,
        defn.value:source::string as source_id,
        defn.value:page::integer as page,
        defn.value:latinForms::string as latin_forms,
        defn.value:note::string as note,
        loaded_at
    from source,
    lateral flatten(input => json_data:synonymDefinitions) category,
    lateral flatten(input => category.value, outer => true) defn
    where category.key != '_metadata'
      and defn.key != 'traitId'
      and defn.value is not null
      and typeof(defn.value) = 'OBJECT'
)

select * from definitions_flattened
