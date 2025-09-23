""" 
This is just a script for me to do one-time modifications to the Supabase database.
"""

from supabase import create_client, Client
import os
import pandas as pd
import numpy as np


# Get your credentials from environment variables
url: str = os.getenv("SUPABASE_PRJ_URL")
key: str = os.getenv("supabase_anon_key")

supabase: Client = create_client(url, key)

response = supabase.table("real_estate").select("*").execute()
df = pd.DataFrame(response.data)



# Extract information from the link
sep_keys = ["-pho-", "-phuong-", "-duong-"]
def extract_real_estate_type(link):
    sep_keys_dict = {k: link.find(k) for k in sep_keys if link.find(k) != -1} # find all keys and their positions
    if not sep_keys_dict:
        return None
    first_key = min(sep_keys_dict.items())[0] # find the first occurring key
    return link.split(sep=first_key, maxsplit=1)[0] # get the part before the key
df['real_estate_type'] = df['link'].apply(extract_real_estate_type)
df['real_estate_type'] = df['real_estate_type'].str.replace("https://batdongsan.com.vn/", "")  
displaying_dict = {
    "ban-can-ho-chung-cu"   : "Căn hộ chung cư", 
    "ban-nha-mat-pho"       : "Nhà mặt phố", 
    "ban-nha-rieng"         : "Nhà riêng"
    
}
df['real_estate_type'] = df['real_estate_type'].replace(displaying_dict, regex=False)

# Extract project name from the link
df['project'] = df['link'].str.split("-prj-").str[1].str.split("/").str[0]

df['price_num'] = df['price_num'] / 1000

# Overwrite all data in the real_estate table
# supabase.table("real_estate").delete().neq("unique_id", 0).execute()  # Delete all rows



df = df.astype({
    "title": "string",
    "link": "string",
    "bedrooms": "int64",
    "toilets": "int64",
    "location": "string",
    "description": "string",   # even if all nulls
    "agent_name": "string",
    "phone": "string",         # important: prevent float issues
    "price_num": "int64",
    "area_num": "float64",
    "price_per_m2_recal": "float64",
    # "time_scraped": "datetime64[ns]",
    "unique_id": "string", 
    'real_estate_type': "string", 
    'project': "string"

})
df['price_num'] = df['price_num'].fillna(0).astype(int)
# Ensure datetime is timezone-aware (UTC is safe default)
df["time_scraped"] = pd.to_datetime(df["time_scraped"], utc=True)
# Convert to ISO 8601 strings
df["time_scraped"] = df["time_scraped"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")



# Overwrite all data in the real_estate table
# supabase.table("real_estate").delete().neq("unique_id", 0).execute()  # Delete all rows where id ≠ 0


data_to_insert = df.to_dict(orient="records")
if data_to_insert:
    supabase.table("real_estate").insert(data_to_insert).execute()
