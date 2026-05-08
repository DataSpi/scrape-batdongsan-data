import asyncio
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
import pandas as pd

from utils.sqlalchemy_conn import dbConnector as db
from utils.common_tools import setup_logging
logger = setup_logging()

# Maximum number of concurrent requests
MAX_CONCURRENCY = 5
URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-mizuki-park"



def soup_to_df(html_soup):
    # Find all listing cards
    cards = html_soup.find_all("div", class_="js__card-full-web")

    results = []
    for card in cards:
        # Title
        title_tag = card.find("span", class_="pr-title js__card-title")
        title = title_tag.text.strip() if title_tag else None

        # Link
        link_tag = card.find("a", class_="js__product-link-for-product-id")
        link = link_tag['href'] if link_tag and link_tag.has_attr('href') else None

        # Price
        price_tag = card.find("span", class_="re__card-config-price")
        price = price_tag.text.strip() if price_tag else None

        # Area
        area_tag = card.find("span", class_="re__card-config-area")
        area = area_tag.text.strip() if area_tag else None

        # Price per m2
        ppm2_tag = card.find("span", class_="re__card-config-price_per_m2")
        price_per_m2 = ppm2_tag.text.strip() if ppm2_tag else None

        # Bedrooms
        bedroom_tag = card.find("span", class_="re__card-config-bedroom")
        bedrooms = bedroom_tag.find("span").text.strip() if bedroom_tag and bedroom_tag.find("span") else None

        # Bathrooms
        toilet_tag = card.find("span", class_="re__card-config-toilet")
        toilets = toilet_tag.find("span").text.strip() if toilet_tag and toilet_tag.find("span") else None

        # Location
        location_tag = card.find("div", class_="re__card-location")
        location = location_tag.find("span").text.strip() if location_tag and location_tag.find("span") else None

        # Description
        desc_tag = card.find("div", class_="re__card-description")
        description = desc_tag.text.strip() if desc_tag else None

        # Agent name
        agent_tag = card.find("div", class_="agent-name")
        agent_name = agent_tag.text.strip() if agent_tag else None

        # Agent phone (may be masked)
        phone_tag = card.find("span", class_="js__card-phone-btn")
        phone = phone_tag.find_all("span")[-1].text.strip() if phone_tag else None

        # Images
        img_tags = card.find_all("img")
        images = [img['src'] for img in img_tags if img.has_attr('src')]

        results.append({
            "title": title,
            "link": link,
            "price": price,
            "area": area,
            "price_per_m2": price_per_m2,
            "bedrooms": bedrooms,
            "toilets": toilets,
            "location": location,
            "description": description,
            "agent_name": agent_name,
            "phone": phone,
            "images": images
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

async def fetch_all_pages(urls:list):
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
    
    urls = get_urls_list(html_content, url)
    
    # Fetch all pages concurrently
    results = await fetch_all_pages(urls)
    
    # Combine all dataframes
    df_total = df.copy()
    for result_df, _ in results[1:]:
        if result_df is not None:
            df_total = pd.concat([df_total, result_df], ignore_index=True)
    
    return df_total

if __name__ == "__main__":
    conn = db.spyno_sb_conn()
    df_final = asyncio.run(main())
    db.write_df_to_table(conn, df_final, schema="re_bronze", table="real_estate")


