import pandas as pd
import requests
import unicodedata
import io  # Add this import
import re
import os
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()


def clean_numeric_column(value):
    # If it's already a number (NaN or float), just return it
    if pd.isna(value) or isinstance(value, (int, float)):
        return value
    
    # Convert to string just in case
    val_str = str(value)
    
    # 1. Remove Wikipedia citations like [1], [nb 1], etc.
    val_str = re.sub(r'\[.*?\]', '', val_str)
    
    # 2. Remove non-numeric characters EXCEPT the decimal comma/dot
    # For population, we just want digits. We remove dots, spaces, and commas.
    val_str = re.sub(r'[^\d]', '', val_str)
    
    # 3. Convert to numeric, return NaN if the string is empty
    return pd.to_numeric(val_str, errors='coerce')



url = "https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_%C4%91%C6%A1n_v%E1%BB%8B_h%C3%A0nh_ch%C3%ADnh_c%E1%BA%A5p_huy%E1%BB%87n_c%E1%BB%A7a_Vi%E1%BB%87t_Nam"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

# Wrap response.text in io.StringIO()
tables = pd.read_html(io.StringIO(response.text))

# On this specific Wikipedia page, the main list is usually tables[0]
df = tables[0]

df.columns = [
    unicodedata.normalize("NFD", col)
    .encode("ascii", "ignore")
    .decode("utf-8")
    .lower()
    .replace(" ", "_")
    .replace("(", "")
    .replace(")", "")
    .replace("/", "_")
    for col in df.columns
]

num_col_to_convert = [
    'dan_so_nguoi', 
    'dien_tich_km',
    'mat_o_dan_so_nguoi_km', 
    'so_vhc_cap_xa'
]
for col in num_col_to_convert:
    df[col] = df[col].apply(clean_numeric_column)
    df[col] = df[col].astype('float64')
    print(f"Converted column '{col}' to numeric.")

df.to_csv("../data/seeds/vietnam_provinces.csv", index=False)



url: str = os.getenv("SUPABASE_PRJ_URL")
key: str = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)


response = supabase.table("real_estate").upsert(df).execute()



