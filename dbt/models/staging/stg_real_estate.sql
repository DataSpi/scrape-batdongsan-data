-- Ports src/_br2sil/j_real_estate.py to SQL. Two behavior changes vs. the legacy
-- pandas script (see dbt/models/staging/_staging.yml for details):
--   1. Real dedup by product_id (legacy script only logged duplicates, kept appending
--      them). Originally keyed on substr(link_clean, -10): the source site appends a
--      "?c=d1"-style tracking query string to the same listing's link on some scrapes
--      but not others, so that suffix silently produced two "unique" keys for one
--      listing and let 294 product_ids through as duplicates -- product_id is the
--      native, stable id and doesn't have this problem.
--   2. real_estate_type matching only implements the whitelist tokens that were actually
--      reachable in the legacy code (some whitelist entries were dead due to substring
--      shadowing by an earlier, broader token in the same priority list).

with source as (
    select * from {{ source('bronze', 'real_estate') }}
),

cleaned_link as (
    select
        *,
        case
            when link is null then null
            when starts_with(link, 'http') then link
            else concat('https://batdongsan.com.vn', regexp_replace(link, r'^\./', ''))
        end as link_clean,
        -- mirrors the legacy script: real_estate_type is derived from the raw `link`
        -- slug *before* it gets rewritten into a full URL above
        trim(lower(regexp_replace(coalesce(link, ''), r'^https://batdongsan\.com\.vn/', ''))) as type_source
    from source
),

type_matched as (
    select
        *,
        case
            when strpos(type_source, 'can-ho-chung-cu') > 0 then 'can-ho-chung-cu'
            when strpos(type_source, 'ban-nha-biet-thu-lien-ke') > 0 then 'ban-nha-biet-thu-lien-ke'
            when strpos(type_source, 'nha-rieng') > 0 then 'nha-rieng'
            when strpos(type_source, 'ban-nha-mat-pho') > 0 then 'ban-nha-mat-pho'
            when strpos(type_source, 'ban-shophouse-nha-pho-thuong-mai') > 0 then 'ban-shophouse-nha-pho-thuong-mai'
            when strpos(type_source, 'ban-condotel') > 0 then 'ban-condotel'
            else null
        end as matched_token
    from cleaned_link
),

price_area as (
    select
        *,
        lower(replace(replace(price, ',', '.'), ' ', '')) as price_clean,
        -- Vietnamese number format: '.' is a thousands separator, ',' is the decimal
        -- point (e.g. "1.030 m²" = 1030, "76,5 m²" = 76.5) -- strip the former before
        -- converting the latter, or "1.030" parses as the float 1.03.
        replace(replace(area, '.', ''), ',', '.') as area_clean
    from type_matched
),

parsed as (
    select
        *,
        regexp_extract(price_clean, r'^([\d\.]+)(?:tỷ|triệu)') as price_value_str,
        regexp_extract(price_clean, r'^[\d\.]+(tỷ|triệu)') as price_unit,
        safe_cast(regexp_extract(area_clean, r'([\d\.]+)\s*m') as float64) as area_num
    from price_area
),

final as (
    select
        p.product_id,
        p.title,
        p.verify,
        p.verified,
        p.link_clean as link,
        coalesce(m.real_estate_type, p.matched_token, p.type_source) as real_estate_type,
        case
            when p.price_unit = 'tỷ' then round(safe_cast(p.price_value_str as float64) * 1000)
            when p.price_unit = 'triệu' then round(safe_cast(p.price_value_str as float64))
            else null
        end as price_num,
        p.area_num,
        p.bedrooms,
        p.toilets,
        p.location,
        p.description,
        p.agent_name,
        p.phone,
        p.intent,
        p.pageType,
        p.productId,
        p.projectId,
        p.vipType,
        p.expired,
        p.cateId,
        p.cityCode,
        p.districtId,
        p.wardId,
        p.streetId,
        p.pageId,
        p.createByUser,
        p.productType,
        p.IsDisplayNewAddress,
        p.date_scraped,
        p.scraped_at
    from parsed p
    left join {{ ref('real_estate_type_mapping') }} m on p.matched_token = m.raw_token
),

with_price_per_m2 as (
    select
        *,
        case
            when price_num is not null and area_num is not null and area_num != 0
            then price_num / area_num
        end as price_per_m2_recal
    from final
),

flagged as (
    select
        *,
        -- Sanity bounds on price/m2 (triệu/m2), both checked empirically against this
        -- table:
        --   upper: the priciest named-tower listings actually on the market (Grand
        --     Marina Saigon, The Opera Metropole, The Grand Hà Nội, Empire City,
        --     Landmark 81) top out around 930, and nothing in the data sits between
        --     there and 1000 -- so 1000 is a gap, not a guess. Above it, every row so
        --     far has been a source-site data-entry error (e.g. product_id 45698293: an
        --     unedited typo in the total-price field inflated price_per_m2_recal to
        --     ~8,000 triệu/m2).
        --   lower: legitimate cheap listings exist (nhà ở xã hội in Bình Dương genuinely
        --     price around 6.65+), but nothing legitimate sits below that -- rows under
        --     5 top out at 4.4 and are the same bug mirrored (e.g. "The Magnolia MIK
        --     CĂN HỘ LUXURY" at 130 triệu total, clearly meant tỷ), so 5 is a gap too.
        -- Flag instead of dropping here so the raw row stays inspectable in re_silver;
        -- mart_real_estate excludes flagged rows from the gold layer.
        coalesce(price_per_m2_recal < 5 or price_per_m2_recal > 1000, false) as is_price_outlier
    from with_price_per_m2
),

deduped as (
    select
        *,
        -- link tiebreaks scraped_at (frequently null in the bronze data) so reruns keep
        -- the same row instead of picking arbitrarily among ties.
        row_number() over (
            partition by product_id
            order by scraped_at desc nulls last, link asc
        ) as rn
    from flagged
    where product_id is not null
)

select 
product_id
, title
, verify
-- , verified
, link
, real_estate_type
, price_num
, price_per_m2_recal as price_1m2
, is_price_outlier
, area_num
, bedrooms
, toilets
-- , location
-- , description
-- , agent_name
-- , phone
, intent
-- , pageType
-- , productId
, projectId
, vipType
, expired
, cateId
, cityCode
, districtId
, wardId
, streetId
-- , pageId
-- , createByUser
, productType
-- , IsDisplayNewAddress
, date_scraped
-- , scraped_at
-- except (rn)
from deduped
where rn = 1
