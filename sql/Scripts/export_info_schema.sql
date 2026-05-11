SELECT c.table_schema , c.table_name , c.column_name , c.data_type FROM information_schema."columns" c 
WHERE table_schema IN ('re_bronze', 're_silver')
AND NOT (c.table_schema = 're_bronze' AND c.table_name = 'real_estate')
ORDER BY c.table_schema , c.table_name ; 