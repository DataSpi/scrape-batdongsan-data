-- Gold layer per (listing, report period) for rentals: same as mart_real_estate_rent,
-- over fct_real_estate_rent_period.
{{ rent_mart(ref('fct_real_estate_rent_period')) }}
