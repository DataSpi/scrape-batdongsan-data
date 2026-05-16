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

def get_children_infos(parents_df: pd.DataFrame, key_column: str, url_template="https://batdongsan.com.vn/Product/ProductSearch/GetWardsByDistrictIds?districtIds={}"):
    df_all = pd.DataFrame()
    for parent in parents_df.itertuples():
        url = url_template.format(getattr(parent, key_column))
        response = custom_request(url)
        infos = response_to_df(response)
        df_all = pd.concat([df_all, infos], ignore_index=True)
    return df_all


# url = "https://batdongsan.com.vn/Product/ProductSearch/GetCities"
# response = custom_request(url)
# cities = response_to_df(response)
# # cities.query('name=="Hồ Chí Minh" or name=="Hà Nội"')

# url = "https://batdongsan.com.vn/Product/ProductSearch/GetDistricts"
# response = custom_request(url)
# districts = response_to_df(response)
# # print(districts.query('cityCode=="SG"'))

# sg_hn = districts.query('cityCode=="SG" or cityCode=="HN"')

# wards_all = get_children_infos(districts, key_column="districtId", url_template="https://batdongsan.com.vn/Product/ProductSearch/GetWardsByDistrictIds?districtIds={}")

# streets_all = get_children_infos(districts, key_column="districtId", url_template="https://batdongsan.com.vn/Product/ProductSearch/GetStreetsByDistrictIds?districtIds={}")
# projects_all = get_children_infos(districts, key_column="districtId", url_template="https://batdongsan.com.vn/Product/ProductSearch/GetProjectsByDistrictIds?districtIds={}")


{
    "GetCities": "/Product/ProductSearch/GetCitiesV2",
    "GetWardsByCityCode": "/Product/ProductSearch/GetWardsByCityCodeV2",
    "GetStreetsByWardIdV2": "/Product/ProductSearch/GetStreetsByWardIdV2",
    "GetProjectsByWardId": "/Product/ProductSearch/GetProjectsByWardIdV2"
}

ward_sg = response_to_df(custom_request("https://batdongsan.com.vn/Product/ProductSearch/GetWardsByCityCodeV2?cityCode=SG"))

response_to_df(custom_request("https://batdongsan.com.vn/Product/ProductSearch/GetProjectsByWardIdV2?wardId=1036"))




cities_v2 = response_to_df(custom_request("https://batdongsan.com.vn/Product/ProductSearch/GetCitiesV2"))
wards_v2 = get_children_infos(cities_v2, key_column="code", url_template="https://batdongsan.com.vn/Product/ProductSearch/GetWardsByCityCodeV2?cityCode={}")
streets_v2 = get_children_infos(wards_v2, key_column="wardId", url_template="https://batdongsan.com.vn/Product/ProductSearch/GetStreetsByWardIdV2?wardId={}")
projects_v2 = get_children_infos(wards_v2, key_column="wardId", url_template="https://batdongsan.com.vn/Product/ProductSearch/GetProjectsByWardIdV2?wardId={}")






# write to supabase 
conn = db.spyno_sb_conn()
# db.write_df_to_table(conn, cities, schema="re_bronze", table="m_cities", truncate=True)
# db.write_df_to_table(conn, districts, schema="re_bronze", table="m_districts", truncate=True)
# db.write_df_to_table(conn, wards_all, schema="re_bronze", table="m_wards", truncate=True)
# db.write_df_to_table(conn, streets_all, schema="re_bronze", table="m_streets", truncate=True)
# db.write_df_to_table(conn, projects_all, schema="re_bronze", table="m_projects", truncate=True)


db.write_df_to_table(conn, cities_v2, schema="re_bronze", table="m_cities_v2", truncate=True)
db.write_df_to_table(conn, wards_v2, schema="re_bronze", table="m_wards_v2", truncate=True)
db.write_df_to_table(conn, streets_v2, schema="re_bronze", table="m_streets_v2", truncate=True)
db.write_df_to_table(conn, projects_v2, schema="re_bronze", table="m_projects_v2", truncate=True)