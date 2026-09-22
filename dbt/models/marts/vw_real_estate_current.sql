-- Thin convenience read over snp_real_estate's "current row per listing" -- callers
-- (Looker Studio, ad hoc queries) shouldn't need to know dbt's internal snapshot
-- columns (dbt_valid_to, dbt_is_deleted) to answer "is this listing still up?". Full
-- price/attribute history stays queryable directly on snp_real_estate.

{{ config(materialized='view') }}

select
    * except (dbt_valid_from, dbt_valid_to, dbt_updated_at, dbt_scd_id, dbt_is_deleted),
    -- dbt_is_deleted is a string ('True'/'False'), not a native bool -- see dbt's
    -- snapshot meta-column docs for the check strategy.
    case when dbt_is_deleted = 'True' then 'closed' else 'active' end as status,
    dbt_valid_from as status_since
from {{ ref('snp_real_estate') }}
where dbt_valid_to is null
