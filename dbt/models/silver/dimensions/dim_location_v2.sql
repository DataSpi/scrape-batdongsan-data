-- Ports the removed legacy Python job j_locations.py (location_v2) to SQL.
-- Active (post-address-reform) hierarchy, refreshed by src/_web2br/metadata.py.

with ward as (
    select * from {{ source('bronze', 'dim_ward_v2') }}
),

city as (
    select * from {{ source('bronze', 'dim_city_v2') }}
),

geo as (
    select * from {{ ref('dim_ward_geo_v2') }}
)

select
    w.wardId,
    w.name as name_ward,
    w.cityCode,
    w.prefix as prefix_ward,
    c.name as name_city,
    c.prefix as prefix_city,
    geo.lat,
    geo.lng
from ward w
left join city c on w.cityCode = c.code
left join geo on w.wardId = geo.wardId
