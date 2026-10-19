{#
  Gold-layer body shared by mart_real_estate(_rent) and mart_real_estate(_rent)_period:
  location resolution via projectId + price bins. Takes the upstream fct relation so the
  per-listing and per-period marts can't drift apart. Columns of the fct (including
  `period` on the period variant) pass through via `processed_1.*`.
#}


{% macro sale_mart(fct_relation) %}
with re as (
    select * from {{ fct_relation }}
),

project as (
    select * from {{ ref('dim_project') }}
),

loc_v1 as (
    select * from {{ ref('dim_location_v1') }}
), 

processed_1 as (
select
    re.*,
    project.name as project_name,
    -- districtId=0 is batdongsan's IsDisplayNewAddress sentinel for "unresolved" (see
    -- src/scrapers/real_estate.py:crawl_city_by_district), not a real district - treat
    -- it as missing so we fall back to the project's districtId like a NULL would.
    coalesce(nullif(re.districtId, 0), project.districtId) as full_districtId
from re
left join project on re.projectId = project.projectId
)
select processed_1.* except (full_districtId, is_price_outlier),
    loc_v1.name_district as district_name,
    loc_v1.name_city as city_name,
    case
        when loc_v1.lat is not null and loc_v1.lng is not null
        then concat(cast(loc_v1.lat as string), ',', cast(loc_v1.lng as string))
    end as lat_long,
    case
        when processed_1.price_num is null then null
        when processed_1.price_num < 2000 then '0-2 tỷ'
        when processed_1.price_num < 3000 then '2-3 tỷ'
        when processed_1.price_num < 5000 then '3-5 tỷ'
        when processed_1.price_num < 10000 then '5-10 tỷ'
        when processed_1.price_num < 20000 then '10-20 tỷ'
        else '20 tỷ+'
    end as bin_price,
    case
        when processed_1.price_num is null then null
        when processed_1.price_num < 2000 then 1
        when processed_1.price_num < 3000 then 2
        when processed_1.price_num < 5000 then 3
        when processed_1.price_num < 10000 then 4
        when processed_1.price_num < 20000 then 5
        else 6
    end as bin_price_order,
    case
        when processed_1.price_1m2 is null then null
        when processed_1.price_1m2 < 40 then '0-40'
        when processed_1.price_1m2 < 60 then '40-60'
        else '60+'
    end as bin_price_1m2,
    case
        when processed_1.price_1m2 is null then null
        when processed_1.price_1m2 < 40 then 1
        when processed_1.price_1m2 < 60 then 2
        else 3
    end as bin_price_1m2_order
from processed_1
left join loc_v1 on processed_1.full_districtId = loc_v1.districtId
-- Source-data price/m2 errors (see fct_real_estate.is_price_outlier) are excluded from
-- the gold layer rather than reported on.
where not processed_1.is_price_outlier
{% endmacro %}


{% macro rent_mart(fct_relation) %}
with re as (
    select * from {{ fct_relation }}
),

project as (
    select * from {{ ref('dim_project') }}
),

loc_v1 as (
    select * from {{ ref('dim_location_v1') }}
),

processed_1 as (
select
    re.*,
    project.name as project_name,
    -- districtId=0 is batdongsan's IsDisplayNewAddress sentinel for "unresolved" (see
    -- src/scrapers/real_estate.py:crawl_city_by_district), not a real district - treat
    -- it as missing so we fall back to the project's districtId like a NULL would.
    coalesce(nullif(re.districtId, 0), project.districtId) as full_districtId
from re
left join project on re.projectId = project.projectId
)
select processed_1.* except (full_districtId),
    loc_v1.name_district as district_name,
    loc_v1.name_city as city_name,
    case
        when loc_v1.lat is not null and loc_v1.lng is not null
        then concat(cast(loc_v1.lat as string), ',', cast(loc_v1.lng as string))
    end as lat_long,
    -- Provisional thresholds based on the first live sample (5.5-27 triệu/tháng seen) --
    -- adjust once the full HCM+HN distribution is visible.
    case
        when processed_1.price_per_month is null then null
        when processed_1.price_per_month < 5 then '0-5 tr/tháng'
        when processed_1.price_per_month < 10 then '5-10 tr/tháng'
        when processed_1.price_per_month < 15 then '10-15 tr/tháng'
        when processed_1.price_per_month < 20 then '15-20 tr/tháng'
        when processed_1.price_per_month < 30 then '20-30 tr/tháng'
        else '30 tr/tháng+'
    end as bin_price_per_month,
    case
        when processed_1.price_per_month is null then null
        when processed_1.price_per_month < 5 then 1
        when processed_1.price_per_month < 10 then 2
        when processed_1.price_per_month < 15 then 3
        when processed_1.price_per_month < 20 then 4
        when processed_1.price_per_month < 30 then 5
        else 6
    end as bin_price_per_month_order
from processed_1
left join loc_v1 on processed_1.full_districtId = loc_v1.districtId
{% endmacro %}
