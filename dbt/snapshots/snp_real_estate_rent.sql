-- Rent counterpart to snp_real_estate.sql -- see that file for the full rationale
-- (check_cols choice, invalidate_hard_deletes). price_num/price_1m2 become
-- price_per_month/price_per_m2_per_month since rental prices are monthly rates, not
-- comparable to sale prices (same split as stg_real_estate_rent.sql).

{% snapshot snp_real_estate_rent %}

{{
    config(
      target_schema='re_silver',
      unique_key='product_id',
      strategy='check',
      check_cols=[
        'price_per_month',
        'price_per_m2_per_month',
        'area_num',
        'bedrooms',
        'toilets',
        'real_estate_type',
        'expired',
        'vipType',
        'productType',
      ],
      hard_deletes='new_record',
    )
}}

select * from {{ ref('stg_real_estate_rent') }}

{% endsnapshot %}
