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
    -- districtId=0 is batdongsan's IsDisplayNewAddress sentinel for "unresolved" (see
    -- src/_web2br/j_real_estate.py:crawl_city_by_district), not a real district - treat
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
-- Source-data price/m2 errors (see stg_real_estate.is_price_outlier) are excluded from
-- the gold layer rather than reported on.
where not processed_1.is_price_outlier
-- bin_price/bin_price_1m2 buckets and the is_price_outlier bounds are calibrated for
-- total sale prices (tỷ-scale) -- a "cho thuê" (Rent) listing's price is a monthly
-- rate, not a total, so it reads as a nonsensically cheap sale if it slips past
-- is_price_outlier (e.g. missing area_num skips that check entirely). Keep rentals
-- out of this sale-price gold layer until they get their own mart.
and coalesce(processed_1.intent, '') != 'Rent'
