from utils import load_env, prevent_sleep, stop_sleep, format_worksheet
from scraper import scrape_all_pages
import re
import pandas as pd
from supabase import create_client, Client
import os
import numpy as np
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "..", "logs", "main.log")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', # Log format with timestamp, log level, and message
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler() 
    ] # using this 2 handlers to log both to file and console
    , force=True
)
logger = logging.getLogger(__name__)
logger.info("-------------------------Start the script-------------------------")

env = load_env()
caffeinate_proc = prevent_sleep()





def parse_price(price_str):
    if not price_str:
        return None
    price_str = price_str.lower().replace(',', '.').replace(' ', '')
    match = re.match(r'([\d\.]+)(tỷ|triệu)', price_str)
    if not match:
        return None
    value, unit = match.groups()
    try:
        value = float(value)
    except ValueError:
        return None
    if unit == 'tỷ':
        return int(value * 1_000)
    elif unit == 'triệu':
        return int(value * 1)
    return None

def parse_area(area_str):
    if area_str is None or (isinstance(area_str, float) and np.isnan(area_str)):
        return None
    area_str = str(area_str)
    match = re.search(r'([\d\.]+)\s*m', area_str.replace(',', '.'))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def make_image_formula(images):
    if images:
        return f'=IMAGE("{images}", 4, 200, 200)'
    return ''

def extract_real_estate_type(link):
    sep_keys_dict = {k: link.find(k) for k in sep_keys if link.find(
        k) != -1}  # find all keys and their positions
    if not sep_keys_dict:
        return None
    first_key = min(sep_keys_dict.items())[0]  # find the first occurring key
    # get the part before the key
    return link.split(sep=first_key, maxsplit=1)[0]



# Scraping
urls = [
    "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-hcm?vrs=1",
    "https://batdongsan.com.vn/ban-nha-dat-tp-hcm?vrs=1",
]
# url = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-hcm?vrs=1"
# url = "https://batdongsan.com.vn/ban-nha-dat-tp-hcm?vrs=1"

for url in urls:
    logger.info(f"--------------Scraping from: {url}--------------")
    df = scrape_all_pages(base_url=url, load_sleep_time=2,
                        scroll_sleep_time=1, headless=True, 
                        partial_page_num=1)
    df.to_excel("/home/spyno_kiem/scrape-batdongsan-data/data/real_estate_listings_raw.xlsx", index=False)   
    # ----------------------------------------------
    # Clean the DataFrame
    # ----------------------------------------------
    df['link'] = "https://batdongsan.com.vn" + \
        df['link'].astype(str).str.replace(r'^\./', '', regex=True)


    df['price_num'] = df['price'].apply(parse_price)
    df['area_num'] = df['area'].apply(parse_area)
    df.drop(columns=['price', 'area',], inplace=True)
    df['price_per_m2_recal'] = df.apply(
        lambda row: row['price_num'] / row['area_num'] if row['price_num'] and row['area_num'] else None, axis=1)

    # Split the 'images' column (list of image URLs) into separate columns
    no_image_cols = df['images'].apply(
        lambda x: len(x) if isinstance(x, list) else 0).max()
    for idx in range(no_image_cols):
        df[f'image_{idx+1}'] = df['images'].apply(
            lambda imgs: imgs[idx] if isinstance(imgs, list) and len(imgs) > idx else None)
        df[f'image_{idx+1}'] = df[f'image_{idx+1}'].apply(make_image_formula)


    df['date_scraped'] = pd.Timestamp.now().normalize()
    df['unique_id'] = df['link'].str[-10:]
    # Find duplicated unique_id rows
    duplicated_rows = df[df['unique_id'].duplicated(keep=False)]
    if not duplicated_rows.empty:
        logger.info("Duplicated rows based on unique_id:")
        logger.info(duplicated_rows[['link']])
    else:
        logger.info("No duplicated unique_id found.")
    df.to_excel("/home/spyno_kiem/scrape-batdongsan-data/data/real_estate_listings.xlsx", index=False) 


    # Extract information from the link
    sep_keys = ["-pho-", "-phuong-", "-duong-"]



    df['real_estate_type'] = df['link'].apply(extract_real_estate_type)
    df['real_estate_type'] = df['real_estate_type'].str.replace(
        "https://batdongsan.com.vn/", "")
    displaying_dict = {
        "ban-can-ho-chung-cu": "Căn hộ chung cư",
        "ban-nha-mat-pho": "Nhà mặt phố",
        "ban-nha-rieng": "Nhà riêng"
    }
    df['real_estate_type'] = df['real_estate_type'].replace(
        displaying_dict, regex=False)


    # Extract project name from the link
    df['project'] = df['link'].str.split("-prj-").str[1].str.split("/").str[0]


    # --------------------------------------------------------------
    # Save to Supabase
    # --------------------------------------------------------------

    # Get your credentials from environment variables
    url: str = os.getenv("SUPABASE_PRJ_URL")
    key: str = os.getenv("supabase_anon_key")

    supabase: Client = create_client(url, key)


    df.rename(columns={"date_scraped": "time_scraped"}, inplace=True)

    # replace problematic values
    df = df.replace([np.inf, -np.inf], np.nan)  # turn inf into NaN
    df = df.where(pd.notnull(df), None)         # turn NaN into None
    df["bedrooms"] = df["bedrooms"].fillna(0).astype("int64")
    df["toilets"] = df["toilets"].fillna(0).astype("int64")
    df["price_num"] = df["price_num"].fillna(0).astype("int64")


    keep_columns = [
        'title', 'link',
        # 'price_per_m2',
        'bedrooms', 'toilets', 'location',
        'description', 'agent_name', 'phone',
        # 'images',
        'price_num', 'area_num', 'price_per_m2_recal',
        'image_1', 'image_2', 'time_scraped',
        'unique_id',
        'real_estate_type', 'project'
    ]
    df[['bedrooms', 'toilets']]


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
        "unique_id": "string",
        'real_estate_type': "string",
        'project': "string"

    })

    # Convert all columns whose name contains 'image_' to string type
    image_cols = [col for col in df.columns if 'image_' in col]
    df[image_cols] = df[image_cols].astype(str)
    # print(type(df))


    # Ensure datetime is timezone-aware (UTC is safe default)
    df["time_scraped"] = pd.to_datetime(df["time_scraped"], utc=True)
    # Convert to ISO 8601 strings
    df["time_scraped"] = df["time_scraped"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")


    df.drop_duplicates(subset='unique_id', keep='first', inplace=True)
    df_final = df[keep_columns].rename(
        columns={
            "price_per_m2_recal": "price_1m2", 
            "price_num": "price",
            "area_num": "area"
            }
        )
    # Ensure JSON-safe values
    # df_final = df_final.replace([np.inf, -np.inf], np.nan)
    # df_final = df_final.where(pd.notnull(df_final), None)
    df_final = df_final.replace([np.inf, -np.inf], np.nan)
    df_final = df_final.astype(object)
    df_final = df_final.where(pd.notnull(df_final), None)
    df_final = df_final.query('location.notnull()')



    # 1. Fetch existing unique_ids from Supabase
    new_data = df_final.to_dict(orient="records")
    response = supabase.table("real_estate").upsert(new_data).execute()
    inserted_count = len(response.data)   # rows actually written to DB
    logger.info(f"Inserted {inserted_count} new records to Supabase.")
    logger.info(f"{len(new_data) - inserted_count} duplicates skipped.")


stop_sleep(caffeinate_proc)
logger.info("-------------------------Finish the script-------------------------")
