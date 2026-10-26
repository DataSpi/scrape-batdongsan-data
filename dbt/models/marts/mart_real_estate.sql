-- Gold layer: one row per listing with resolved location names.
--
-- Location is resolved through the listing's projectId, not its own districtId/wardId/
-- cityCode columns directly — matching the removed Malloy model real_estate.malloy, which
-- deliberately kept those direct joins commented out because the FK columns on the raw
-- listing are unreliable (~95% of apartment listings have projectId, districts/wards
-- resolved off the listing itself are much less complete; see the docstring in
-- src/scrapers/real_estate.py:crawl_city_by_district).

-- Body lives in macros/listing_marts.sql, shared with mart_real_estate_period.sql.
{{ sale_mart(ref('fct_real_estate')) }}
