-- Warns (does not fail the build) whenever fct_real_estate flags a listing's price/m2
-- as an outlier -- surfaces the rows mart_real_estate is silently excluding so they can
-- be spot-checked against the live listing (see fct_real_estate.is_price_outlier for the
-- bound and the motivating case, product_id 45698293).
{{ config(severity='warn') }}
select product_id, title, link, price_num, area_num, price_1m2
from {{ ref('fct_real_estate') }}
where is_price_outlier
