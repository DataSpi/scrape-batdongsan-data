-- Ports the removed legacy Python job j_real_estate.py to SQL. Two behavior changes vs. the legacy
-- pandas script (see dbt/models/silver/facts/_facts.yml and dbt/models/silver/_seeds.yml for details):
--   1. Real dedup by product_id (legacy script only logged duplicates, kept appending
--      them). Originally keyed on substr(link_clean, -10): the source site appends a
--      "?c=d1"-style tracking query string to the same listing's link on some scrapes
--      but not others, so that suffix silently produced two "unique" keys for one
--      listing and let 294 product_ids through as duplicates -- product_id is the
--      native, stable id and doesn't have this problem.
--   2. real_estate_type matching only implements the whitelist tokens that were actually
--      reachable in the legacy code (some whitelist entries were dead due to substring
--      shadowing by an earlier, broader token in the same priority list).
--
-- Incremental: only rescans bronze rows newer than what's already here (watermark on
-- date_scraped, the one scrape-date column this model still exposes -- scraped_at is
-- dropped from the final select below, so it can't be read back off `this`). The
-- row_number()/rn dedup further down still runs per incremental batch (safety net for
-- reruns writing >1 bronze row per product_id in the same batch); unique_key=product_id
-- lets dbt's merge replace a listing's old row when it's rescraped, same "most recent
-- wins" semantics as the old full-refresh version, just without rescanning all of bronze
-- every run.

{{
    config(
        materialized='incremental',
        unique_key='product_id',
    )
}}

with source as (
    select * from {{ source('bronze', 'fct_real_estate') }}
    {% if is_incremental() %}
    {# >= not >: re-read the newest day too, so rows loaded for it after the last dbt run
       (a partial scrape topped up the same day) are picked up. Safe: unique_key merges by product_id. #}
    where date_scraped >= (select max(date_scraped) from {{ this }})
    {% endif %}
),

-- Per-row cleaning (link, type, price/area parsing, outlier flag) lives in
-- macros/clean_listings.sql, shared with fct_real_estate_period.sql; only the dedup grain differs.
{{ clean_sale_listings('source') }},

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
{{ sale_listing_columns() }}
from deduped
where rn = 1
