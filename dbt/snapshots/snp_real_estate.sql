-- SCD2 history of sale listings, keyed on product_id. Built on top of fct_real_estate
-- (already deduped to "most recent scraped_at per listing") rather than raw bronze:
-- each dbt snapshot run compares that week's current state to the last snapshot row
-- and inserts a new version only when a check_cols value actually changed.
--
-- check_cols is an explicit business-column list rather than 'all': excludes columns
-- that are either near-static (cityCode/districtId/wardId/streetId rarely change and
-- add no signal) or noisy (title edits by the poster shouldn't spawn a new SCD2 row).
--
-- hard_deletes='new_record': when a product_id drops out of fct_real_estate (listing
-- removed/sold), dbt closes the last row's dbt_valid_to AND inserts a new "current" row
-- with dbt_is_deleted='True', dbt_valid_to=NULL -- see vw_real_estate_current, which
-- reads that row as status='closed'.

{% snapshot snp_real_estate %}

{{
    config(
      target_schema='re_silver',
      unique_key='product_id',
      strategy='check',
      check_cols=[
        'price_num',
        'price_1m2',
        'is_price_outlier',
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

select * from {{ ref('fct_real_estate') }}

{% endsnapshot %}
