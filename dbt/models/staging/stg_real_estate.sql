-- Ports src/_br2sil/j_real_estate.py to SQL. Two behavior changes vs. the legacy
-- pandas script (see dbt/models/staging/_staging.yml for details):
--   1. Real dedup by unique_id (legacy script only logged duplicates, kept appending them).
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
        replace(area, ',', '.') as area_clean
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
        current_date() as date_scraped,
        substr(p.link_clean, -10) as unique_id,
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

deduped as (
    select
        *,
        row_number() over (
            partition by unique_id
            order by scraped_at desc nulls last
        ) as rn
    from with_price_per_m2
    where unique_id is not null
)

select * except (rn)
from deduped
where rn = 1
