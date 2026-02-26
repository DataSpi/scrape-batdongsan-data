{{ config(materialized='view') }}

WITH location_hierarchy AS ( 
    SELECT 
        rld.id AS district_id,
        rld.district, 
        rlc.city 
    FROM {{ source('real_estate', 're_loc_district') }} rld 
    JOIN {{ source('real_estate', 're_loc_city') }} rlc 
        ON rld.city_id = rlc.id
)
SELECT 
    rre.id,
    rre.title,
    rre.link,
    rre.price,
    rre.bedrooms,
    rre.toilets,
    rre.area,
    rre.price_1m2,
    rre.location,
    rre.description,
    rre.time_scraped,
    rret.real_estate_type, 
    rp.project_name AS project,
    rre.agent_name, 
    loc.district, 
    loc.city 
FROM {{ source('real_estate', 're_real_estate') }} rre 
LEFT JOIN {{ source('real_estate', 're_project') }} rp 
    ON rre.project_id = rp.id
LEFT JOIN {{ source('real_estate', 're_real_estate_type') }} rret 
    ON rre.re_type_id = rret.id
LEFT JOIN location_hierarchy loc
    ON rre.district_id = loc.district_id