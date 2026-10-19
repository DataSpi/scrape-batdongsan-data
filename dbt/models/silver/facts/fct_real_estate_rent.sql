-- Rental ("cho thuê") counterpart to fct_real_estate.sql, built from its own bronze
-- table (re_bronze.fct_real_estate_rent, written by src/scrapers/real_estate_rent.py -- a
-- separate scraper script from real_estate.py) rather than commingled with sale
-- listings: a rental price is a monthly rate ("23 triệu/tháng"), never a lump sum (tỷ),
-- so it is not comparable to fct_real_estate.price_num/price_1m2 and must not share
-- their bounds/bins downstream (see mart_real_estate_rent.sql).
--
-- Incremental: same approach as fct_real_estate.sql -- watermark on date_scraped (the
-- scrape-date column still exposed in the final select; scraped_at is dropped), rn dedup
-- still scoped per incremental batch, unique_key=product_id merges in rescraped listings.

{{
    config(
        materialized='incremental',
        unique_key='product_id',
    )
}}

with source as (
    select * from {{ source('bronze', 'fct_real_estate_rent') }}
    {% if is_incremental() %}
    {# >= not >: re-read the newest day too, so rows loaded for it after the last dbt run
       (a partial scrape topped up the same day) are picked up. Safe: unique_key merges by product_id. #}
    where date_scraped >= (select max(date_scraped) from {{ this }})
    {% endif %}
),

-- Per-row cleaning (link, type, price/area parsing) lives in
-- macros/clean_listings.sql, shared with fct_real_estate_rent_period.sql; only the dedup grain differs.
{{ clean_rent_listings('source') }},

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
{{ rent_listing_columns() }}
from deduped
where rn = 1
