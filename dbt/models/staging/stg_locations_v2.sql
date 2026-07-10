-- Ports src/_br2sil/j_locations.py (location_v2) to SQL.
-- Active (post-address-reform) hierarchy, refreshed by src/_web2br/j_metadata.py.

with ward as (
    select * from {{ source('bronze', 'm_wards_v2') }}
),

city as (
    select * from {{ source('bronze', 'm_cities_v2') }}
),

geo as (
    select * from {{ ref('ward_geo_v2') }}
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
