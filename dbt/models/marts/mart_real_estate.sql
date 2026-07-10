-- Gold layer: one row per listing with resolved location names.
--
-- Location is resolved through the listing's projectId, not its own districtId/wardId/
-- cityCode columns directly — matching malloy/malloy_publisher/real_estate.malloy, which
-- deliberately keeps those direct joins commented out because the FK columns on the raw
-- listing are unreliable (~95% of apartment listings have projectId, districts/wards
-- resolved off the listing itself are much less complete; see the docstring in
-- src/_web2br/j_real_estate.py:crawl_city_by_district).

with re as (
    select * from {{ ref('stg_real_estate') }}
),

project as (
    select * from {{ ref('stg_projects') }}
),

loc_v1 as (
    select * from {{ ref('stg_locations_v1') }}
), 

processed_1 as (
select
    re.*,
    project.name as project_name,
    coalesce(re.districtId, project.districtId) as full_districtId
from re
left join project on re.projectId = project.projectId
)
select processed_1.* except (full_districtId), 
    loc_v1.name_district as district_name,
    loc_v1.name_city as city_name,
    loc_v1.lat as lat_v1,
    loc_v1.lng as lng_v1 
from processed_1
left join loc_v1 on processed_1.full_districtId = loc_v1.districtId
