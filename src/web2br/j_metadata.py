import pandas as pd
from curl_cffi import requests
from utils.sqlalchemy_conn import dbConnector as db

def custom_request(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    response = requests.get(url, headers=headers, impersonate="chrome124")
    return response

def response_to_df(response):
    json_data = response.json()
    df = pd.DataFrame(json_data)
    return df

def get_info_by_districts(districts_df: pd.DataFrame, url_template="https://batdongsan.com.vn/Product/ProductSearch/GetWardsByDistrictIds?districtIds={}"):
    df_all = pd.DataFrame()
    for district in districts_df.itertuples():
        url = url_template.format(district.districtId)
        response = custom_request(url)
        wards = response_to_df(response)
        df_all = pd.concat([df_all, wards], ignore_index=True)
    return df_all


url = "https://batdongsan.com.vn/Product/ProductSearch/GetCities"
response = custom_request(url)
cities = response_to_df(response)
# cities.query('name=="Hồ Chí Minh" or name=="Hà Nội"')

url = "https://batdongsan.com.vn/Product/ProductSearch/GetDistricts"
response = custom_request(url)
districts = response_to_df(response)
# print(districts.query('cityCode=="SG"'))

sg_hn = districts.query('cityCode=="SG" or cityCode=="HN"')

wards_all = get_info_by_districts(sg_hn, url_template="https://batdongsan.com.vn/Product/ProductSearch/GetWardsByDistrictIds?districtIds={}")
streets_all = get_info_by_districts(sg_hn, url_template="https://batdongsan.com.vn/Product/ProductSearch/GetStreetsByDistrictIds?districtIds={}")
projects_all = get_info_by_districts(sg_hn, url_template="https://batdongsan.com.vn/Product/ProductSearch/GetProjectsByDistrictIds?districtIds={}")


# write to supabase 
conn = db.spyno_sb_conn()
db.write_df_to_table(conn, cities, schema="re_bronze", table="m_cities")
db.write_df_to_table(conn, districts, schema="re_bronze", table="m_districts")
db.write_df_to_table(conn, wards_all, schema="re_bronze", table="m_wards")
db.write_df_to_table(conn, streets_all, schema="re_bronze", table="m_streets")
db.write_df_to_table(conn, projects_all, schema="re_bronze", table="m_projects")
