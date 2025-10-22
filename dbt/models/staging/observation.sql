-- needed for RAI
{{ config(
    post_hook='alter table {{this}} set change_tracking=true'
) }}


select
    obs.gbifid,
    obs.taxonkey,
    obs.eventdate,
    dayofyear(obs.eventdate) as dayofyear,
    year(obs.eventdate) as year,
    obs.basisofrecord,
    obs.countrycode,
    obs.stateprovince,
    obs.decimallatitude as lat,
    obs.decimallongitude as lon,
    H3_LATLNG_TO_CELL(lat, lon, 6) as h3_cell_6, -- 36km
    H3_LATLNG_TO_CELL(lat, lon, 7) as h3_cell_7, -- 5km
    H3_LATLNG_TO_CELL(lat, lon, 8) as h3_cell_8, -- 0.7km
    H3_LATLNG_TO_CELL(lat, lon, 9) as h3_cell_9, -- 0.1km
    H3_LATLNG_TO_CELL(lat, lon, 10) as h3_cell_10 -- 0.01km
from {{ source('gbif', 'observation') }} as obs
