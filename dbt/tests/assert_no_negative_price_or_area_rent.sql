-- Fails if any listing has a negative parsed price or area (parse bug, not real data).
select product_id, price_per_month, area_num
from {{ ref('stg_real_estate_rent') }}
where price_per_month < 0 or area_num < 0
