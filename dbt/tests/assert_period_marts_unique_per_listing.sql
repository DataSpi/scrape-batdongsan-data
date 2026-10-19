-- Fails if a listing appears more than once within the same report period.
select 'sale' as side, period, product_id, count(*) as n
from {{ ref('mart_real_estate_period') }}
group by 1, 2, 3
having count(*) > 1
union all
select 'rent' as side, period, product_id, count(*) as n
from {{ ref('mart_real_estate_rent_period') }}
group by 1, 2, 3
having count(*) > 1
