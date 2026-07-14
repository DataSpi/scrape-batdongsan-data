-- Rental ("cho thuê") counterpart to stg_real_estate.sql, built from its own bronze
-- table (re_bronze.real_estate_rent, written by src/_web2br/j_real_estate_rent.py -- a
-- separate scraper script from j_real_estate.py) rather than commingled with sale
-- listings: a rental price is a monthly rate ("23 triệu/tháng"), never a lump sum (tỷ),
-- so it is not comparable to stg_real_estate.price_num/price_1m2 and must not share
-- their bounds/bins downstream (see mart_real_estate_rent.sql).

with source as (
    select * from {{ source('bronze', 'real_estate_rent') }}
),

cleaned_link as (
    select
        *,
        case
            when link is null then null
            when starts_with(link, 'http') then link
            else concat('https://batdongsan.com.vn', regexp_replace(link, r'^\./', ''))
        end as link_clean,
        trim(lower(regexp_replace(coalesce(link, ''), r'^https://batdongsan\.com\.vn/', ''))) as type_source
    from source
),

type_matched as (
    select
        *,
        case
            when strpos(type_source, 'cho-thue-can-ho-chung-cu') > 0 then 'cho-thue-can-ho-chung-cu'
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
        -- Rental cards are always "X triệu/tháng" in practice (never tỷ), but the tỷ
        -- branch below is kept for parity with stg_real_estate.sql in case a
        -- source-site data-entry slip ever lists one that way.
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
        end as price_per_month,
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
        -- IsDisplayNewAddress not carried through: absent from the rental tracking-data
        -- JSON entirely (unlike sale listings), and unused downstream even there.
        p.date_scraped,
        p.scraped_at
    from parsed p
    left join {{ ref('real_estate_type_mapping') }} m on p.matched_token = m.raw_token
),

with_price_per_m2 as (
    select
        *,
        case
            when price_per_month is not null and area_num is not null and area_num != 0
            then price_per_month / area_num
        end as price_per_m2_per_month
    from final
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
    from with_price_per_m2
    where product_id is not null
)

select
product_id
, title
, verify
-- , verified
, link
, real_estate_type
, price_per_month
, price_per_m2_per_month
-- No is_price_outlier column yet -- stg_real_estate's [5,1000] triệu/m2 bound was
-- derived empirically from real sale listings (see that model's comments); there's no
-- equivalent observed rental price/m2 distribution yet to calibrate a bound from.
-- Revisit once there's enough real data to eyeball.
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
from deduped
where rn = 1
