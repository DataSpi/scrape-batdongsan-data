-- One row per (listing, report period): the state of the sale market as scraped during
-- each window in dim_report_period, rebuilt straight from bronze.
--
-- Why not filter fct_real_estate by date_scraped: fct keeps only the latest scrape per
-- product_id, so a listing still live at the next scrape gets its old row overwritten.
-- Filtering it on an old window returns only the listings that disappeared since -- a
-- survivor-biased, incomplete sample (rent 07/2026: 8.8k rows in fct vs 11.3k listings
-- actually scraped). snp_real_estate only starts 2026-09-23, so it can't recover older
-- windows either; bronze is append-only and still holds every scrape.
--
-- Bronze rows with null date_scraped (pre-pipeline legacy loads) fall outside every
-- window and are dropped on purpose: a report period must be a known date range.
-- Full rebuild every run (not incremental): bronze is small, and editing a window in
-- the seed must re-bucket rows that are already here.

with source as (
    select b.*, p.period
    from {{ source('bronze', 'fct_real_estate') }} b
    inner join {{ ref('dim_report_period') }} p
        on b.date_scraped between p.start_date and p.end_date
),

{{ clean_sale_listings('source', carry_cols=['period']) }},

deduped as (
    select
        *,
        -- same tiebreak as fct_real_estate, scoped to one period
        row_number() over (
            partition by product_id, period
            order by scraped_at desc nulls last, link asc
        ) as rn
    from flagged
    where product_id is not null
)

select
period
, {{ sale_listing_columns() }}
from deduped
where rn = 1
