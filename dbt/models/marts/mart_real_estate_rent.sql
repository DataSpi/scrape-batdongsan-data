-- Gold layer for rental ("cho thuê") listings -- rent counterpart to mart_real_estate.sql.
-- Same location-resolution pattern (via projectId, then district/city name + lat/lng),
-- but its own price bins: rental prices are monthly rates, not comparable to
-- mart_real_estate's tỷ-scale bin_price/bin_price_1m2, so this mart uses distinctly
-- named bins (bin_price_per_month) instead of reusing those names.
--
-- No is_price_outlier equivalent yet: mart_real_estate's bound was derived empirically
-- from real sale listings (see stg_real_estate.sql); there's no equivalent observed
-- rental price/m2 distribution yet to calibrate one from.

with re as (
    select * from {{ ref('stg_real_estate_rent') }}
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
    -- districtId=0 is batdongsan's IsDisplayNewAddress sentinel for "unresolved" (see
    -- src/_web2br/j_real_estate.py:crawl_city_by_district), not a real district - treat
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
