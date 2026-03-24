-- Extract metadata from Newcomb trait ontology
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

with source as (
    select * from {{ source('traits', 'newcomb_raw') }}
),

metadata as (
    select
        json_data:metadata:title::string as title,
        json_data:metadata:version::string as version,
        json_data:metadata:description::string as description,
        json_data:metadata:synonymSourcesFile::string as synonym_sources_file,
        json_data:metadata:newcombOriginalNote::string as newcomb_original_note,
        json_data:metadata:source:title::string as source_title,
        json_data:metadata:source:author::string as source_author,
        json_data:metadata:source:lccn::string as source_lccn,
        json_data:metadata:source:excerpt::string as source_excerpt,
        loaded_at
    from source
)

select * from metadata
