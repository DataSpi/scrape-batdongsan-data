import pandas as pd 
from utils.sqlalchemy_conn import dbConnector as db
from utils.common_tools import setup_logging
import matplotlib.pyplot as plt
import seaborn as sns
logger = setup_logging()

db_conn = db.spyno_sb_conn()

df = db.fetch_to_dataframe(conn=db_conn, query="select * from re_silver.real_estate")
prj = db.fetch_to_dataframe(conn=db_conn, query='select "projectId", name as project_name from re_bronze.m_projects')

df_merged = df.merge(prj[['projectId', 'project_name']], left_on='projectId', right_on='projectId', how='left')
df_merged['project_name'].value_counts()


print(df.districtId.value_counts())
print(df.wardId.value_counts())

df.groupby(['cityCode', 'districtId']).size().reset_index(name='listing_count').sort_values(by=['cityCode', 'listing_count'], ascending=False)


df.groupby(['cityCode', 'wardId']).size().reset_index(name='listing_count').sort_values(by=['cityCode', 'listing_count'], ascending=False)

df.query('districtId==0').cityCode.value_counts()
# all the districtId == 0 are in HCM city -> trang web inconsistent chỗ này
# bây giờ cần nối từ real_estate -> ward -> district -> city để kiểm tra


(df.product_id == df['productId']).value_counts()
# 2 cột này bằng nhau, có thể drop 1 cột 

ward = db.fetch_to_dataframe(conn=db_conn, query="select * from re_bronze.m_wards")
district = db.fetch_to_dataframe(conn=db_conn, query="select * from re_bronze.m_districts")
city = db.fetch_to_dataframe(conn=db_conn, query="select * from re_bronze.m_cities")


df.columns  
lkp_cols = ['product_id', 'cityCode', 'districtId', 'wardId', 'projectId']
loc_df = pd.DataFrame(df[lkp_cols].copy())


loc_df = loc_df.merge(ward[['wardId', 'name', 'districtId']], on='wardId',how='left', suffixes=('_loc', '_ward')).rename(columns={'name': 'ward_name'})#.drop(columns=['id'])
(loc_df['districtId_loc'] == loc_df['districtId_ward']).value_counts()

loc_df['districtId_loc'].value_counts()
# 19792 cái districtId_loc = 0, nhưng districtId_ward thì có giá trị, -> trang web tracking hơi kì cho districtId của SG
# từ vấn đề trên -> có thể suy ra wardId của SG cũng sẽ bị sai lệch không nhỉ? well, this is weid. 

loc_df.query('cityCode == "SG"').districtId_loc.value_counts()
loc_df.query('cityCode == "SG"').ward_name.value_counts()
loc_df.query('cityCode == "SG"')['districtId_ward'].value_counts()



loc_df = loc_df.merge(district[['districtId', 'name']], left_on='districtId_ward', right_on='districtId', how='left').rename(columns={
    'name': 'district_name', 
    'districtId': 'districtId_dis'
})

loc_df.columns
loc_df.groupby(['cityCode', 'districtId_loc', 'districtId_dis', 'district_name']).size().reset_index(name='count').sort_values(by=['cityCode', 'districtId_loc', 'districtId_dis', 'district_name'], ascending=False)

loc_df = loc_df.merge(city[['code', 'name']], left_on='cityCode', right_on='code', how='left').rename(columns={'name': 'city_name'}).drop(columns=['code'])

# -----------------------------------------------
# Analyzing
# -----------------------------------------------

# Grouping by the geographic hierarchy
location_stats = df_merged.groupby(['cityCode', 'districtId']).size().reset_index(name='listing_count')

# Displaying top 10 most active wards
print("### Top 10 Active Wards")
print(location_stats.sort_values(by='listing_count', ascending=False))

# Quick breakdown by Real Estate Type
type_counts = df_merged['real_estate_type'].value_counts()
print("\n### Listings by Property Type")
print(type_counts)



plt.figure(figsize=(12, 6))
sns.histplot(df_merged['price_num'], kde=True, color='#2a9d8f', bins=30)
plt.title('Distribution of Property Prices', fontsize=15)
plt.xlabel('Price (VND)')
plt.ylabel('Number of Listings')
plt.ticklabel_format(style='plain', axis='x') # Remove scientific notation
plt.grid(axis='y', alpha=0.3)
plt.show()

# Filtering out listings that aren't part of a specific project (if applicable)
project_prices = df_merged[df_merged['projectId'].notna()].groupby('project_name')['price_num'].mean().sort_values(ascending=False)

plt.figure(figsize=(10, 8))
project_prices.head(15).plot(kind='barh', color="#e76f51")
plt.title('Top 15 Most Expensive Projects (Average Price)')
plt.xlabel('Average Price')
plt.ylabel('Project Name')
plt.gca().invert_yaxis() # Highest price at the top
plt.show()