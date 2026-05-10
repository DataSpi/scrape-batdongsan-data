SELECT 
    location, 
    COUNT(*) AS total_listings,
    ROUND(AVG(price_num)::numeric, 2) AS avg_price,
    ROUND(AVG(area_num)::numeric, 2) AS avg_area,
    ROUND(AVG(price_per_m2_recal)::numeric, 2) AS avg_price_per_m2
FROM re_silver.real_estate re 
GROUP BY location
HAVING COUNT(*) > 5
ORDER BY avg_price_per_m2 DESC;