{{ 
  config(
    materialized='incremental', 
    unique_key='project_name',
    merge_exclude_columns=['id']
    ) 
}}


SELECT DISTINCT
  project AS project_name
FROM staging.real_estate
WHERE project IS NOT NULL