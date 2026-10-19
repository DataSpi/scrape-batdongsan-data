{#
  Per-row cleaning shared by fct_real_estate(_rent) (grain = listing, latest scrape wins)
  and fct_real_estate(_rent)_period (grain = listing x report period). Only the dedup
  partition differs between the two, so everything before it lives here: one copy of
  the parsing rules, not two that drift apart.

  Usage: `with source as (...), {{ clean_sale_listings('source') }}, deduped as (...)`.
  The macro emits the CTEs cleaned_link .. flagged (sale) / with_price_per_m2 (rent);
  `carry_cols` lists extra source columns (e.g. period) to pass through `final`, which
  otherwise selects an explicit column list.
#}

{% macro clean_sale_listings(source_cte, carry_cols=[]) %}
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
    from {{ source_cte }}
),

type_matched as (
    select
        *,
        case
            -- must precede 'can-ho-chung-cu' below: that broader token is a substring
            -- of every mini-apartment link slug and would shadow this match otherwise
            when strpos(type_source, 'can-ho-chung-cu-mini') > 0 then 'can-ho-chung-cu-mini'
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
        -- Vietnamese number format: '.' is a thousands separator, ',' is the decimal
        -- point (e.g. "1.030 m²" = 1030, "76,5 m²" = 76.5; same convention for price,
        -- e.g. "1.812,5 tỷ" = 1812.5) -- strip the former before converting the latter,
        -- or "1.030" parses as the float 1.03. Confirmed against production data: prices
        -- like "1.000 tỷ" are real 1000-tỷ land listings (cross-checked via price_per_m2
        -- * area), not 1-tỷ ones -- the old comma-only version silently undervalued them
        -- 1000x (and, worse, made 37 of them fail the price/m2 outlier check below).
        lower(replace(replace(replace(price, '.', ''), ',', '.'), ' ', '')) as price_clean,
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
        {% for col in carry_cols %}p.{{ col }},
        {% endfor -%}
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
        -- Hashed rather than carried through raw: a stable per-agent identifier (e.g.
        -- "same agent re-posting under a new product_id") without a callable phone
        -- number ever existing as its own column past this point -- p.agent_name is
        -- dropped outright below, since a hashed name has no analytical use on its own.
        to_hex(sha256(p.phone)) as agent_phone_hash,
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
    left join {{ ref('dim_real_estate_type_mapping') }} m on p.matched_token = m.raw_token
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
)
{% endmacro %}


{# Output columns of the sale fct models (after the dedup CTE). #}
{% macro sale_listing_columns() %}
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
, agent_phone_hash
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
{% endmacro %}


{% macro clean_rent_listings(source_cte, carry_cols=[]) %}
cleaned_link as (
    select
        *,
        case
            when link is null then null
            when starts_with(link, 'http') then link
            else concat('https://batdongsan.com.vn', regexp_replace(link, r'^\./', ''))
        end as link_clean,
        trim(lower(regexp_replace(coalesce(link, ''), r'^https://batdongsan\.com\.vn/', ''))) as type_source
    from {{ source_cte }}
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
        -- Vietnamese number format: '.' is a thousands separator, ',' is the decimal
        -- point (e.g. "1.030 m²" = 1030, "76,5 m²" = 76.5) -- strip the former before
        -- converting the latter, or "1.030" parses as the float 1.03. Same treatment as
        -- price in clean_sale_listings -- no rent row hits this today (rents stay well
        -- under 1000 triệu/tháng), but the bug would be silent if one ever did.
        lower(replace(replace(replace(price, '.', ''), ',', '.'), ' ', '')) as price_clean,
        replace(replace(area, '.', ''), ',', '.') as area_clean
    from type_matched
),

parsed as (
    select
        *,
        -- Rental cards are always "X triệu/tháng" in practice (never tỷ), but the tỷ
        -- branch below is kept for parity with clean_sale_listings in case a
        -- source-site data-entry slip ever lists one that way.
        regexp_extract(price_clean, r'^([\d\.]+)(?:tỷ|triệu)') as price_value_str,
        regexp_extract(price_clean, r'^[\d\.]+(tỷ|triệu)') as price_unit,
        safe_cast(regexp_extract(area_clean, r'([\d\.]+)\s*m') as float64) as area_num
    from price_area
),

final as (
    select
        {% for col in carry_cols %}p.{{ col }},
        {% endfor -%}
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
        -- Hashed rather than carried through raw -- see clean_sale_listings for the
        -- rationale (same treatment, same scraper field, separate bronze table).
        to_hex(sha256(p.phone)) as agent_phone_hash,
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
    left join {{ ref('dim_real_estate_type_mapping') }} m on p.matched_token = m.raw_token
),

with_price_per_m2 as (
    select
        *,
        case
            when price_per_month is not null and area_num is not null and area_num != 0
            then price_per_month / area_num
        end as price_per_m2_per_month
    from final
)
{% endmacro %}


{# Output columns of the rent fct models (after the dedup CTE). #}
{% macro rent_listing_columns() %}
product_id
, title
, verify
-- , verified
, link
, real_estate_type
, price_per_month
, price_per_m2_per_month
-- No is_price_outlier column yet -- fct_real_estate's [5,1000] triệu/m2 bound was
-- derived empirically from real sale listings (see clean_sale_listings); there's no
-- equivalent observed rental price/m2 distribution yet to calibrate a bound from.
-- Revisit once there's enough real data to eyeball.
, area_num
, bedrooms
, toilets
-- , location
-- , description
, agent_phone_hash
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
{% endmacro %}
