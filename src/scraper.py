import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from utils import setup_logging
logger = setup_logging()

def get_soup(url, load_sleep_time, scroll_sleep_time, headless=True, chrome_binary_path=None):
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")

    if chrome_binary_path:
        options.binary_location = chrome_binary_path

    driver = webdriver.Firefox(options=options)

    driver.get(url)
    driver.implicitly_wait(load_sleep_time)

    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_sleep_time)

    html_content = driver.page_source
    driver.quit()

    html_content = BeautifulSoup(html_content, 'html.parser')
    return html_content


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

    return pd.DataFrame(results)

def scrape_all_pages(base_url, load_sleep_time=2, scroll_sleep_time=1, headless=True, partial_page_num=0) -> pd.DataFrame:
    html_soup = get_soup(
        url=base_url,
        load_sleep_time=load_sleep_time,
        scroll_sleep_time=scroll_sleep_time, 
        headless=headless
    )
    df = soup_to_df(html_soup)
    logger.info(f"Scraped {len(df)} listings from the first page.")

    page_num_list = html_soup.find_all("a", class_="re__pagination-number")
    page_num = max([int(i.text.strip()) for i in page_num_list]) if page_num_list else 1
    logger.info(f"Total pages: {page_num}")
    if partial_page_num > 0:
        page_num = min(page_num, partial_page_num)
        logger.info(f"Partial scraping mode: limiting to {page_num} pages.")

    for i in range(2, page_num + 1):
        if base_url.endswith('?vrs=1'): # check if the filter "tin xac thuc" is on or not
            next_url = f"{base_url[:-6]}/p{i}?vrs=1"
        else:
            next_url = f"{base_url}/p{i}"
        try: 
            html_soup_extra = get_soup(
                url=next_url,
                load_sleep_time=load_sleep_time,
                scroll_sleep_time=scroll_sleep_time, 
                headless=headless
            )
            df = pd.concat([df, soup_to_df(html_soup_extra)], ignore_index=True)
            logger.info(f"Scraped {len(df)} listings from page {i}.")
        except Exception as e:
            logger.error(f"Error occurred while scraping page {i}: {e}")
            logger.info("Proceeding to the next page...")
    return df



# soup = get_soup(
#     url="https://batdongsan.com.vn/ban-can-ho-chung-cu-tan-binh",
#     load_sleep_time=2,
#     scroll_sleep_time=1,
#     headless=True, 
# )
# df = soup_to_df(soup)
# print(df.head())