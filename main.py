from utils import setup_logging, load_env, prevent_sleep, stop_sleep, format_worksheet
from scraper import get_soup, soup_to_df, scrape_all_pages
import gspread
from gspread_dataframe import set_with_dataframe
import re
import pandas as pd

logger = setup_logging()
env = load_env()
caffeinate_proc = prevent_sleep()

# Google Sheets setup
gc = gspread.service_account(filename='credentials.json')
spreadsheet_id = "1OtsXeovl50pEanLsx_ZmGpfD-iA72FCRYW27BzkVL9k"
sh = gc.open_by_key(spreadsheet_id)
try:
    sh.add_worksheet(title="raw", rows="100", cols="20")
except Exception as e:
    logger.info(f"Worksheet 'raw' may already exist: {e}")
worksheet = sh.worksheet("raw")


# Scraping
url = input("Enter the URL to scrape (e.g., https://batdongsan.com.vn/ban-can-ho-chung-cu-tan-binh): ").strip()
if not url:
    print("No URL provided. Proceed the default URL.")
    url = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tan-binh"
df = scrape_all_pages(base_url=url, load_sleep_time=2, scroll_sleep_time=1, headless=True)


# ----------------------------------------------
# Clean the DataFrame & save to Excel
# ----------------------------------------------
df['link'] = "https://batdongsan.com.vn" + df['link'].astype(str).str.replace(r'^\./', '', regex=True)

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
        return int(value * 1_000_000)
    elif unit == 'triệu':
        return int(value * 1_000)
    return None
def parse_area(area_str):
    if not area_str:
        return None
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

df['price_num'] = df['price'].apply(parse_price)
df['area_num'] = df['area'].apply(parse_area)
df.drop(columns=['price', 'area',], inplace=True)
df['price_per_m2_recal'] = df.apply(lambda row: row['price_num'] / row['area_num'] if row['price_num'] and row['area_num'] else None, axis=1)

# Split the 'images' column (list of image URLs) into separate columns
no_image_cols = df['images'].apply(lambda x: len(x) if isinstance(x, list) else 0).max()
for idx in range(no_image_cols):
    df[f'image_{idx+1}'] = df['images'].apply(lambda imgs: imgs[idx] if isinstance(imgs, list) and len(imgs) > idx else None)
    df[f'image_{idx+1}'] = df[f'image_{idx+1}'].apply(make_image_formula)


df['date_scraped'] = pd.Timestamp.now().normalize()
df['unique_id'] = df['link'].str[-10:]

df_keep = df.drop(columns=['images', 'price_per_m2'])



# Save to Google Sheets
# Get existing unique_ids from the sheet
existing_df = worksheet.get_all_records()
existing_ids = set(row.get('unique_id') for row in existing_df if 'unique_id' in row)

# Filter new records
new_records = df_keep[~df_keep['unique_id'].isin(existing_ids)]

# Append only new records
if not new_records.empty:
    set_with_dataframe(worksheet, new_records, include_column_header=False, resize=False, row=worksheet.row_count + 1)
    logger.info(f"Appended {len(new_records)} new records to Google Sheets.")
else:
    logger.info("No new records to append.")
df.to_excel("real_estate_listings.xlsx", index=False)
format_worksheet(worksheet)
stop_sleep(caffeinate_proc)


