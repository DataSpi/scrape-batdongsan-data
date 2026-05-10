import re
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()
import numpy as np
import logging

from utils.common_tools import dbConnector as db
from utils.sqlalchemy_conn import dbConnector as db


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "../..", "logs", "br2sil_j_real_estate.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


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

def normalize_real_estate_type(df: pd.DataFrame) -> pd.DataFrame:
    whitelist = [
        'Căn hộ chung cư',
        'Nhà mặt phố',
        'Nhà riêng',
        'can-ho-chung-cu',
        'ban-nha-biet-thu-lien-ke',
        'nha-rieng',
        'ban-nha-mat-pho',
        'ban-shophouse-nha-pho-thuong-mai',
        'ban-nha-rieng',
        'ban-can-ho-chung-cu', 
        'ban-condotel'
    ]

    def standardize_re_type(val: str) -> str:
        def str_normalize(s) -> str:
            if s is None or (isinstance(s, float) and pd.isna(s)):
                return ""
            return str(s).strip().lower()

        x = str_normalize(val)
        for token in whitelist:
            if token in x:
                return token
        return x

    df['real_estate_type'] = df['real_estate_type'].str.replace("https://batdongsan.com.vn/", "") # for some reason, this still here and need to be removed
    df['real_estate_type'] = df['real_estate_type'].map(standardize_re_type)

    type_mapping = {
        "nhà riêng": "nhà riêng",
        "căn hộ chung cư": "căn hộ chung cư",
        "nhà mặt phố": "nhà mặt phố",
        "ban-nha-biet-thu-lien-ke": "nhà biệt thự liền kề",
        "nha-rieng": "nhà riêng",
        "ban-nha-mat": "nhà mặt phố",
        "ban-nha-mat-pho": "nhà mặt phố",
        "ban-shophouse-nha-pho-thuong-mai": "shophouse nhà phố thương mại",
        "ban-shophouse-nha": "shophouse nhà phố thương mại",
        "can-ho-chung-cu": "căn hộ chung cư",
        'ban-condotel': 'condotel'
    }
    df['real_estate_type'] = df['real_estate_type'].replace(type_mapping, regex=False)
    return df


# ----------------------------------------------
# Read raw DataFrame
# ----------------------------------------------
conn = db.spyno_sb_conn()
df = db.fetch_to_dataframe(conn, query='SELECT * FROM re_bronze.real_estate')

# ----------------------------------------------
# Clean the DataFrame
# ----------------------------------------------
# Real estate type normalization & project extraction
df['real_estate_type'] = df['link']
df['link'] = df['link'].apply(
    lambda x: x if str(x).startswith("http") 
    else "https://batdongsan.com.vn" + str(x)
)
df['link'] = df['link'].str.replace(r'^\./', '', regex=True)
df = normalize_real_estate_type(df)
print(df['real_estate_type'].value_counts())
# df['project'] = df['link'].str.split("-prj-").str[1].fillna("").str.split("/").str[0] # fillna() add 2026-02-25 after the .str error


# Price and area parsing
df['price_num'] = df['price'].apply(parse_price)
df['area_num'] = df['area'].apply(parse_area)
df.drop(columns=['price', 'area',], inplace=True)
df['price_per_m2_recal'] = df.apply(
    lambda row: row['price_num'] / row['area_num'] if row['price_num'] and row['area_num'] else None, axis=1)

# Add date_scraped and unique_id & deduplicate check
df['date_scraped'] = pd.Timestamp.now().normalize()
df['unique_id'] = df['link'].str[-10:]
# Find duplicated unique_id rows
duplicated_rows = df[df['unique_id'].duplicated(keep=False)]
if not duplicated_rows.empty:
    logger.info("Duplicated rows based on unique_id:")
    logger.info(duplicated_rows[['link']])
else:
    logger.info("No duplicated unique_id found.")
    
# ----------------------------------------------
# Write to Supabase
# ----------------------------------------------
# db.execute_query(conn, "drop table if exists re_silver.real_estate cascade", fetch=False)
db.write_df_to_table(conn, df, schema="re_silver", table="real_estate")