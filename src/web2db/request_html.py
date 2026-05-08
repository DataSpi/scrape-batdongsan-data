import asyncio
# from curl_cffi.aio import AsyncSession
from curl_cffi.requests import AsyncSession
from src.web2db.scraper import soup_to_df
from bs4 import BeautifulSoup
import pandas as pd

# Maximum number of concurrent requests
MAX_CONCURRENCY = 5
URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-mizuki-park"

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
                print(f"Success! Data received from {url}")
                html_content = BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"Failed with status code: {response.status_code} for {url}")
                return None, None
                
            df = soup_to_df(html_content)
            return df, html_content
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None, None


def get_total_pages(html_content, base_url):
    """Extract total number of pages from HTML content."""
    page_num_list = html_content.find_all("a", class_="re__pagination-number")
    page_num = max([int(i.text.strip()) for i in page_num_list]) if page_num_list else 1
    urls = [f"{base_url}/p{i}" for i in range(1, page_num + 1)]
    return page_num, urls


async def fetch_all_pages(urls:list, page_num:int):
    """Fetch all pages concurrently."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    
    async with AsyncSession() as session:
        tasks = [fetch_and_parse(page_url, session, semaphore) for page_url in urls]
        results = await asyncio.gather(*tasks)
    
    return results


async def main(url=URL):
    # Fetch first page to get total pages
    semaphore = asyncio.Semaphore(1)
    async with AsyncSession() as session:
        df, html_content = await fetch_and_parse(url, session, semaphore)
    
    page_num, urls = get_total_pages(html_content, url)
    print(f"Total pages to fetch: {page_num}")
    
    # Fetch all pages concurrently
    results = await fetch_all_pages(urls, page_num)
    
    # Combine all dataframes
    df_total = df.copy()
    for result_df, _ in results[1:]:
        if result_df is not None:
            df_total = pd.concat([df_total, result_df], ignore_index=True)
    
    return df_total

if __name__ == "__main__":
    df_final = asyncio.run(main())
    df_final.to_excel("/home/spyno_kiem/scrape-batdongsan-data/data/real_estate_listings_raw2.xlsx", index=False)


