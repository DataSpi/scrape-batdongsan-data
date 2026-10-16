-- Fails if any listing has a negative parsed price or area (parse bug, not real data).
select product_id, price_num, area_num
from {{ ref('fct_real_estate') }}
where price_num < 0 or area_num < 0
