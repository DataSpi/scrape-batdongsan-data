import pandas as pd
from utils.gcp_conn import get_bigquery_client, query_to_df, upload_df_to_bigquery

client = get_bigquery_client()

city = query_to_df(client, "select * from re_bronze.m_cities")
district = query_to_df(client, "select * from re_bronze.m_districts")
# ward = query_to_df(client, "select * from re_bronze.m_wards")
location_v1 = pd.merge(district, city, how="left", left_on="cityCode", right_on="code", suffixes=("_district", "_city")).drop(columns=["code"])

city_v2 = query_to_df(client, "select * from re_bronze.m_cities_v2")
ward_v2 = query_to_df(client, "select * from re_bronze.m_wards_v2")
location_v2 = pd.merge(ward_v2, city_v2, how="left", left_on="cityCode", right_on="code", suffixes=("_ward", "_city")).drop(columns=["code"])



# """
# việc đặt tên mới cho đường là k bắt buộc. 

# các phương pháp chuyển loc mới thành loc cũ: 
# 1. projectID (đúng 100% các chung cư có projectID, chiếm 95%, chỉ 5% không có projectID)
# 2. streetID (cần check lại)
#     - cùng 1 streetID thì v1 và v2 có cùng một đường không? 
#         - KL: cùng 1 đường, nhưng con đường đó có thể trải dài trên nhiều quận. 
#     - 
# """







upload_df_to_bigquery(client, location_v1, f"{client.project}.re_silver.locations_v1", write_disposition="WRITE_TRUNCATE")
upload_df_to_bigquery(client, location_v2, f"{client.project}.re_silver.locations_v2", write_disposition="WRITE_TRUNCATE")

