-- Ports src/_br2sil/j_locations.py (location_v1) to SQL.
-- Legacy (old-address) hierarchy. m_cities/m_districts are frozen (see _sources.yml).

with district as (
    select * from {{ source('bronze', 'm_districts') }}
),

city as (
    select * from {{ source('bronze', 'm_cities') }}
),

geo as (
    select * from {{ ref('district_geo_v1') }}
)

select
    d.districtId,
    d.name as name_district,
    d.cityCode,
    d.prefix as prefix_district,
    c.name as name_city,
    c.prefix as prefix_city,
    geo.lat,
    geo.lng
from district d
left join city c on d.cityCode = c.code
left join geo on d.districtId = geo.districtId
