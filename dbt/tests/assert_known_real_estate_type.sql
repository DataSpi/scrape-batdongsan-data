-- Fails if a non-null real_estate_type doesn't match any canonical label in the
-- mapping seed -- signals a new/unmapped listing-type slug appeared on the site.
select re.unique_id, re.real_estate_type
from {{ ref('stg_real_estate') }} re
left join {{ ref('real_estate_type_mapping') }} m on re.real_estate_type = m.real_estate_type
where re.real_estate_type is not null
  and m.real_estate_type is null
