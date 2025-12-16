-- needed for RAI
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}

select *
from {{ source('plants', 'plants') }}
