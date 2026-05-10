import pandas as pd 
from utils.sqlalchemy_conn import dbConnector as db
from utils.common_tools import setup_logging
import matplotlib.pyplot as plt
import seaborn as sns
logger = setup_logging()

db_conn = db.spyno_sb_conn()

df = db.fetch_to_dataframe(conn=db_conn, query="select * from re_silver.real_estate limit 1000")
prj = db.fetch_to_dataframe(conn=db_conn, query='select "projectId", name as project_name from re_bronze.m_projects')

df_merged = df.merge(prj[['projectId', 'project_name']], left_on='projectId', right_on='projectId', how='left')
df_merged['project_name'].value_counts()

# -----------------------------------------------
# Analyzing
# -----------------------------------------------

# Grouping by the geographic hierarchy
location_stats = df.groupby(['cityCode', 'districtId', 'wardId']).size().reset_index(name='listing_count')

# Displaying top 10 most active wards
print("### Top 10 Active Wards")
print(location_stats.sort_values(by='listing_count', ascending=False).head(10))

# Quick breakdown by Real Estate Type
type_counts = df['real_estate_type'].value_counts()
print("\n### Listings by Property Type")
print(type_counts)



plt.figure(figsize=(12, 6))
sns.histplot(df['price_num'], kde=True, color='#2a9d8f', bins=30)
plt.title('Distribution of Property Prices', fontsize=15)
plt.xlabel('Price (VND)')
plt.ylabel('Number of Listings')
plt.ticklabel_format(style='plain', axis='x') # Remove scientific notation
plt.grid(axis='y', alpha=0.3)
plt.show()

# Filtering out listings that aren't part of a specific project (if applicable)
project_prices = df[df['projectId'].notna()].groupby('projectId')['price_num'].mean().sort_values(ascending=False)

plt.figure(figsize=(10, 8))
project_prices.head(15).plot(kind='barh', color='#e76f51')
plt.title('Top 15 Most Expensive Projects (Average Price)')
plt.xlabel('Average Price')
plt.ylabel('Project ID')
plt.gca().invert_yaxis() # Highest price at the top
plt.show()