import pandas as pd 
import os 
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client

url: str = os.getenv("SUPABASE_PRJ_URL")
key: str = os.getenv("supabase_anon_key")

supabase: Client = create_client(url, key)

try:
    response = supabase.table("real_estate").select("*").execute()
    data = response.data
except Exception as e:
    raise RuntimeError(e)

data = response.data
df = pd.DataFrame(data)
print(df.head())


df.shape

