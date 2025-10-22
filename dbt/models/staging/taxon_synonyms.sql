-- needed for RAI
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

SELECT
    TAXONID,
    VERNACULARNAME,
    LANGUAGE
FROM
    {{ source('gbif', 'vernacular_name') }}
