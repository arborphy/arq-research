with source as (
    select * from {{ ref('observations') }}
),

enriched as (
    select
        *,
        -- H3 cells at multiple resolutions
        h3_latlng_to_cell(latitude, longitude, 7)  as h3_res7,   -- ~5.16 km² (~1.2 km edge)
        h3_latlng_to_cell(latitude, longitude, 9)  as h3_res9,   -- ~0.105 km² (~174 m edge)
        h3_latlng_to_cell(latitude, longitude, 12) as h3_res12   -- ~0.003 km² (~9 m edge)
    from source
    where latitude is not null
      and longitude is not null
)

select * from enriched
