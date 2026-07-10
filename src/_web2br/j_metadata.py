import time

import pandas as pd
from curl_cffi import requests
from src.utils.gcp_conn import get_bigquery_client, upload_df_to_bigquery
from src.utils.common_tools import setup_logging
logger = setup_logging()

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2

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
        parent_id = getattr(parent, key_column)
        url = url_template.format(parent_id)

        # A single bad request (timeout, transient rate-limit, malformed body) used to
        # raise and crash the whole script, losing every row fetched so far (everything
        # is only uploaded at the very end). Retry a few times, then skip just this one
        # parent instead of aborting the run.
        infos = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = custom_request(url)
                infos = response_to_df(response)
                break
            except Exception as e:
                if attempt < MAX_ATTEMPTS:
                    logger.warning(f"{key_column}={parent_id} attempt {attempt}/{MAX_ATTEMPTS} failed ({e}), retrying...")
                    time.sleep(RETRY_BACKOFF_SECONDS)
                else:
                    logger.error(f"{key_column}={parent_id} failed after {MAX_ATTEMPTS} attempts ({e}), skipping.")

        if infos is not None:
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






# write to BigQuery
bq_client = get_bigquery_client()
# upload_df_to_bigquery(bq_client, cities, f"{bq_client.project}.re_bronze.m_cities", write_disposition="WRITE_TRUNCATE")
# upload_df_to_bigquery(bq_client, districts, f"{bq_client.project}.re_bronze.m_districts", write_disposition="WRITE_TRUNCATE")
# upload_df_to_bigquery(bq_client, wards_all, f"{bq_client.project}.re_bronze.m_wards", write_disposition="WRITE_TRUNCATE")
# upload_df_to_bigquery(bq_client, streets_all, f"{bq_client.project}.re_bronze.m_streets", write_disposition="WRITE_TRUNCATE")
# upload_df_to_bigquery(bq_client, projects_all, f"{bq_client.project}.re_bronze.m_projects", write_disposition="WRITE_TRUNCATE")


upload_df_to_bigquery(bq_client, cities_v2, f"{bq_client.project}.re_bronze.m_cities_v2", write_disposition="WRITE_TRUNCATE")
upload_df_to_bigquery(bq_client, wards_v2, f"{bq_client.project}.re_bronze.m_wards_v2", write_disposition="WRITE_TRUNCATE")
upload_df_to_bigquery(bq_client, streets_v2, f"{bq_client.project}.re_bronze.m_streets_v2", write_disposition="WRITE_TRUNCATE")
upload_df_to_bigquery(bq_client, projects_v2, f"{bq_client.project}.re_bronze.m_projects_v2", write_disposition="WRITE_TRUNCATE")