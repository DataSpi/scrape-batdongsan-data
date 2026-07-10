SELECT 
    re.unique_id,
    re."productId",
    re.title,
    re.price_num,
    re.area_num,
    re.price_per_m2_recal,
    re.verified,
    re."vipType",
    re.real_estate_type,
    re.date_scraped,
    c.name AS city_name,
    d.name AS district_name,
    w.name AS ward_name,
    s.name AS street_name,
    p.name AS project_name
FROM re_silver.real_estate re
LEFT JOIN re_bronze.m_cities c 
    ON re."cityCode" = c.code
LEFT JOIN re_bronze.m_districts d 
    ON re."districtId" = d."districtId"
LEFT JOIN re_bronze.m_wards w 
    ON re."wardId" = w."wardId"
LEFT JOIN re_bronze.m_streets s 
    ON re."streetId" = s."streetId"
LEFT JOIN re_bronze.m_projects p 
    ON re."projectId"= p."projectId"
WHERE 
    c.name IN ('Hà Nội', 'Hồ Chí Minh'); 

