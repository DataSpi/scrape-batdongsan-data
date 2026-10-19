-- Rent counterpart to fct_real_estate_period.sql: one row per (listing, report period),
-- rebuilt from bronze -- see that file for why fct_real_estate_rent can't serve old
-- windows.

with source as (
    select b.*, p.period
    from {{ source('bronze', 'fct_real_estate_rent') }} b
    inner join {{ ref('dim_report_period') }} p
        on b.date_scraped between p.start_date and p.end_date
),

{{ clean_rent_listings('source', carry_cols=['period']) }},

deduped as (
    select
        *,
        row_number() over (
            partition by product_id, period
            order by scraped_at desc nulls last, link asc
        ) as rn
    from with_price_per_m2
    where product_id is not null
)

select
period
, {{ rent_listing_columns() }}
from deduped
where rn = 1
