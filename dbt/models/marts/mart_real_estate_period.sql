-- Gold layer per (listing, report period): same location resolution, bins and outlier
-- exclusion as mart_real_estate, over fct_real_estate_period. Source for the period
-- report site (scrape-bds-rp-evidence); compare periods only after checking coverage.
{{ sale_mart(ref('fct_real_estate_period')) }}
