-- Rent counterpart to vw_real_estate_current.sql -- see that model for the full
-- rationale.

{{ config(materialized='view') }}

select
    * except (dbt_valid_from, dbt_valid_to, dbt_updated_at, dbt_scd_id, dbt_is_deleted),
    case when dbt_is_deleted = 'True' then 'closed' else 'active' end as status,
    dbt_valid_from as status_since
from {{ ref('snp_real_estate_rent') }}
where dbt_valid_to is null
