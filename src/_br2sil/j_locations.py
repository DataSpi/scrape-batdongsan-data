import pandas as pd
from utils.sqlalchemy_conn import dbConnector as db

conn = db.spyno_sb_conn()

city = db.fetch_to_dataframe(conn, "select * from re_bronze.m_cities")
district = db.fetch_to_dataframe(conn, "select * from re_bronze.m_districts")
# ward = db.fetch_to_dataframe(conn, "select * from re_bronze.m_wards")
location_v1 = pd.merge(district, city, how="left", left_on="cityCode", right_on="code", suffixes=("_district", "_city")).drop(columns=["code"])

city_v2 = db.fetch_to_dataframe(conn, "select * from re_bronze.m_cities_v2")
ward_v2 = db.fetch_to_dataframe(conn, "select * from re_bronze.m_wards_v2")
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







db.write_df_to_table(conn, location_v1, schema="re_silver", table="locations_v1", truncate=True)
db.write_df_to_table(conn, location_v2, schema="re_silver", table="locations_v2", truncate=True)

