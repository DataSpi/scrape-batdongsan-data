-- Gold layer for rental ("cho thuê") listings -- rent counterpart to mart_real_estate.sql.
-- Same location-resolution pattern (via projectId, then district/city name + lat/lng),
-- but its own price bins: rental prices are monthly rates, not comparable to
-- mart_real_estate's tỷ-scale bin_price/bin_price_1m2, so this mart uses distinctly
-- named bins (bin_price_per_month) instead of reusing those names.
--
-- No is_price_outlier equivalent yet: mart_real_estate's bound was derived empirically
-- from real sale listings (see fct_real_estate.sql); there's no equivalent observed
-- rental price/m2 distribution yet to calibrate one from.

-- Body lives in macros/listing_marts.sql, shared with mart_real_estate_rent_period.sql.
{{ rent_mart(ref('fct_real_estate_rent')) }}
