from supabase import create_client, Client
import os
import pandas as pd
import numpy as np


# Get your credentials from environment variables
url: str = os.getenv("SUPABASE_PRJ_URL")
key: str = os.getenv("supabase_anon_key")

supabase: Client = create_client(url, key)

# Example: fetch rows from a table
df = pd.read_excel("real_estate_listings.xlsx")
df.rename(columns={"date_scraped": "time_scraped"}, inplace=True)

keep_columns = [
    'title', 'link', 
    # 'price_per_m2', 
    'bedrooms', 'toilets', 'location',
    'description', 'agent_name', 'phone', 
    # 'images', 
    'price_num', 'area_num', 'price_per_m2_recal', 
    'image_1', 'image_2', 'time_scraped',
    'unique_id'
]


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
    "time_scraped": "datetime64[ns]",
    "unique_id": "string"
})

# Convert all columns whose name contains 'image_' to string type
image_cols = [col for col in df.columns if 'image_' in col]
df[image_cols] = df[image_cols].astype(str)
# print(type(df))


# Ensure datetime is timezone-aware (UTC is safe default)
df["time_scraped"] = pd.to_datetime(df["time_scraped"], utc=True)
# Convert to ISO 8601 strings
df["time_scraped"] = df["time_scraped"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
# replace problematic values
df = df.replace([np.inf, -np.inf], np.nan)  # turn inf into NaN
df = df.where(pd.notnull(df), None)         # turn NaN into None


df.drop_duplicates(subset='unique_id', keep='first', inplace=True)

data = df[keep_columns].to_dict(orient="records")
response = supabase.table("real_estate").insert(data).execute()


