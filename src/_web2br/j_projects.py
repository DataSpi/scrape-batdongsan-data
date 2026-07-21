import argparse
import asyncio
import json
import os

import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from src.utils.common_tools import setup_logging
from src.utils.gcp_conn import get_bigquery_client, upload_df_to_bigquery

logger = setup_logging()


MAX_CONCURRENCY = 5
BATCH_SIZE = 100
BATCH_DELAY_SECONDS = 0
URL = os.getenv("URL", "https://batdongsan.com.vn/du-an-bat-dong-san-tp-hcm")
# URL = os.getenv("URL", "")


def soup_to_df(html_soup):
    def extract_card_configs(prj_card):
        """Extract card configurations from a project card."""
        card_config_all = prj_card.find("div", class_="re__prj-card-config re__clearfix")
        card_config_list = card_config_all.find_all("span", class_="re__prj-card-config-value")

        configs = []
        for card_config in card_config_list:
            if card_config.get('aria-label'):
                config = card_config.get('aria-label').strip()
            else:
                config = card_config.text.strip()
            configs.append(config)
        return configs

    # Find all prj cards
    prj_cards = html_soup.find_all("div", class_="js__project-card js__card-project-web re__prj-card-full")

    results = []
    for prj in prj_cards:
        title = prj.find("h3", class_="re__prj-card-title").text.strip()
        location = prj.find("div", class_="re__prj-card-location").text.strip()
        description = prj.find("div", class_="re__prj-card-summary").text.strip()
        prj_link = prj.find("a", class_="re__clearfix")['href']
        prj_id = prj.find("a", class_="re__clearfix")['tracking-label']
        configs = extract_card_configs(prj)

        results.append({
            "title"             : title,
            # Serialized to JSON, not a native list: re_bronze.projects.additional_info
            # is a STRING column, and WRITE_APPEND loads use the existing table schema
            # (no autodetect) -- a raw list column fails pyarrow conversion on upload.
            "additional_info"   : json.dumps(configs, ensure_ascii=False),
            "location"          : location,
            "description"       : description,
            "link"              : prj_link,
            "id"                : prj_id,
        })

    logger.info(f"Extracted {len(results)} listings from the page")
    return pd.DataFrame(results)



def get_urls_list(html_content, base_url):
    """Extract total number of pages from HTML content."""
    page_num_list = html_content.find_all("a", class_="re__pagination-number")
    page_num = max([int(i.text.strip()) for i in page_num_list]) if page_num_list else 1
    urls = [f"{base_url}/p{i}" for i in range(1, page_num + 1)]
    logger.info(f"Total pages to fetch: {page_num}")
    return urls



async def fetch_and_parse(url, session, semaphore):
    """Fetch HTML content from URL and parse it into a DataFrame."""
    async with semaphore:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        try:
            # The 'impersonate' argument is the magic part—it mimics Chrome's TLS fingerprint
            response = await session.get(url, headers=headers, impersonate="chrome124")

            if response.status_code == 200:
                logger.info(f"Success! Data received from {url}")
                html_content = BeautifulSoup(response.text, 'html.parser')
            else:
                logger.error(f"Failed with status code: {response.status_code} for {url}")
                return None, None

            df = soup_to_df(html_content)
            return df, html_content
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None, None

async def fetch_all_pages(urls: list, batch_size: int = BATCH_SIZE, batch_delay_seconds: int = BATCH_DELAY_SECONDS):
    """Fetch pages in bounded batches with a pause between batches."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    all_results = []

    async with AsyncSession() as session:
        for start_index in range(0, len(urls), batch_size):
            batch_number = (start_index // batch_size) + 1
            batch_urls = urls[start_index:start_index + batch_size]
            tasks = [fetch_and_parse(page_url, session, semaphore) for page_url in batch_urls]
            batch_results = await asyncio.gather(*tasks)
            all_results.extend(batch_results)

            has_more_batches = start_index + batch_size < len(urls)
            if has_more_batches:
                logger.info(
                    f"Completed batch {batch_number} ({len(batch_urls)} pages). "
                    f"Sleeping {batch_delay_seconds}s before the next batch."
                )
                await asyncio.sleep(batch_delay_seconds)

    return all_results

async def main(url=URL):
    # Fetch first page to get total pages
    semaphore = asyncio.Semaphore(1)
    async with AsyncSession() as session:
        df, html_content = await fetch_and_parse(url, session, semaphore)
    if df is None or len(df) == 0:
        logger.error(f"No listings found on the first page. HTML content:\n{html_content}")
        raise AssertionError("No listings found on the first page. Check if the page structure has changed or if the URL is correct.")

    logger.info(f"Initial page fetched. Extracted {len(df)} listings from the first page.")
    urls = get_urls_list(html_content, url)

    # Fetch all pages concurrently
    results = await fetch_all_pages(urls)

    # Combine all dataframes
    df_total = df.copy()
    for result_df, _ in results[1:]:
        if result_df is not None:
            df_total = pd.concat([df_total, result_df], ignore_index=True)

    return df_total

def parse_args():
    parser = argparse.ArgumentParser(description="Crawl batdongsan.com.vn project listings.")
    parser.add_argument("--url", default=URL, help="Project listing URL to crawl. Default: %(default)s")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    bq_client = get_bigquery_client()
    df_final = asyncio.run(main(url=args.url))
    upload_df_to_bigquery(bq_client, df_final, f"{bq_client.project}.re_bronze.projects", write_disposition="WRITE_APPEND")


