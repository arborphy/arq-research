-- needed for RAI
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}


select * from {{ ref('observation') }}
order by eventdate desc
limit 1000000
