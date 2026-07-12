-- Warns (does not fail the build) whenever stg_real_estate flags a listing's price/m2
-- as an outlier -- surfaces the rows mart_real_estate is silently excluding so they can
-- be spot-checked against the live listing (see stg_real_estate.is_price_outlier for the
-- bound and the motivating case, product_id 45698293).
{{ config(severity='warn') }}
select product_id, title, link, price_num, area_num, price_1m2
from {{ ref('stg_real_estate') }}
where is_price_outlier
