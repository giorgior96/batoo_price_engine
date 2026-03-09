
import httpx
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from tqdm import tqdm
import time
from config import ZYTE_PROXY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("yachtall.log"),
        logging.StreamHandler()
    ]
)

class YachtallScraper:
    def __init__(self, max_concurrent=30):
        self.base_url = "https://www.yachtall.com"
        # Restore original search URL
        self.search_url = "https://www.yachtall.com/it/barche/barche-usate?pg={}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.proxy = ZYTE_PROXY
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.all_data = []

    def parse_listing(self, card):
        try:
            # Find the element with data-bid which is often in an img tag
            bid_tag = card.find(attrs={"data-bid": True})
            if not bid_tag:
                return None
            
            boat_id_str = bid_tag.get('data-bid', '')
            # Extract only digits for integer ID
            boat_id_numeric = "".join(filter(str.isdigit, boat_id_str))
            boat_id = int(boat_id_numeric) if boat_id_numeric else 0

            # URL and Model Info often in data-view or data-model
            model_info_tag = card.find(attrs={"data-model": True})
            url = ""
            title_full = ""
            if model_info_tag:
                url = model_info_tag.get('data-view', '')
                title_full = model_info_tag.get('data-model', '').split(',')[0].strip()
            
            if url and not url.startswith('http'):
                url = self.base_url + url

            # Builder/Make
            make = ""
            make_tag = card.find('span', class_='boat-only-huge', string=re.compile(r':'))
            if make_tag:
                make = make_tag.get_text(strip=True).strip(':').strip()
            
            if not make and title_full:
                # Fallback if make_tag not found
                make = title_full.split(' ', 1)[0]

            model = title_full
            if make and title_full.startswith(make):
                model = title_full[len(make):].strip()

            # Year
            year = None
            if model_info_tag:
                year_match = re.search(r'anno(?:&nbsp;|\s+)(\d{4})', model_info_tag.get('data-model', ''))
                if year_match:
                    year = int(year_match.group(1))

            # Price
            price_numeric = None
            price_tag = card.find('span', class_='color-orange-bold') or card.find('span', class_='nowrap', string=re.compile(r'€'))
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                clean_price = re.sub(r'[^\d]', '', price_text)
                if clean_price:
                    try:
                        price_numeric = float(clean_price)
                    except:
                        pass

            # Length
            length_numeric = None
            length_b = card.find('b', string=re.compile(r'\d+[,.]\d+\s*m'))
            if length_b:
                l_text = length_b.get_text(strip=True)
                l_match = re.search(r'(\d+[\.,]\d*)', l_text)
                if l_match:
                    length_numeric = float(l_match.group(1).replace(',', '.'))

            # Location and Country
            location = ""
            country = "italia"
            loc_label = card.find('span', class_='boat-only-huge', string=re.compile(r'Posto d’ormeggio', re.I))
            if loc_label:
                loc_val = loc_label.find_next_sibling('span', class_='boatlist-info-l')
                if loc_val:
                    location = loc_val.get_text(strip=True)
            
            if not location:
                # Fallback to any boatlist-info-l
                loc_val = card.find('span', class_='boatlist-info-l')
                if loc_val:
                    location = loc_val.get_text(strip=True)

            if location:
                if ',' in location:
                    country = location.split(',')[-1].strip().lower()
                else:
                    country = location.strip().lower()

            # Broker
            broker = ""
            broker_label = card.find('span', class_='boat-only-huge', string=re.compile(r'Azienda', re.I))
            if broker_label:
                broker_val = broker_label.find_next_sibling('span', class_='boatlist-info-r')
                if broker_val:
                    broker = broker_val.get_text(strip=True)
            
            if not broker:
                # Try finding in data-contact
                if model_info_tag:
                    broker = model_info_tag.get('data-contact', '')

            # Improved Image extraction
            img_url = ""
            all_imgs = card.find_all('img')
            for img in all_imgs:
                # Check both src and data-src for the real boat image
                for attr in ['src', 'data-src']:
                    val = img.get(attr, '')
                    if 'image.yachtall.com' in val:
                        img_url = val
                        break
                if img_url:
                    break

            return {
                "id": boat_id,
                "builder": make,
                "model": model,
                "year_built": year,
                "country": country,
                "price_eur": price_numeric,
                "length": length_numeric,
                "image_url": img_url,
                "source": "yachtall",
                "broker": broker,
                "url": url,
                "category": "",
                "status": True
            }
        except Exception as e:
            logging.error(f"Error parsing Yachtall card: {e}")
            return None

    async def fetch_page(self, client, page):
        url = self.search_url.format(page)
        async with self.semaphore:
            try:
                response = await client.get(url, headers=self.headers, timeout=30.0)
                if response.status_code == 200:
                    return response.text
                else:
                    logging.error(f"Failed to fetch Yachtall page {page}: Status {response.status_code}")
                    return None
            except Exception as e:
                logging.error(f"Error fetching Yachtall page {page}: {e}")
                return None

    def process_page_html(self, html):
        if not html: return []
        soup = BeautifulSoup(html, 'html.parser')
        # Listings are usually in divs with class boatlist-main-box or boatlist-item
        cards = soup.find_all('div', class_=re.compile(r'boatlist-main-box|boatlist-item'))
        
        if not cards:
            # Try another common container
            cards = soup.find_all('div', class_='boat-list')
            if not cards:
                # Fallback to finding by data-bid (not recommended as it might chop HTML)
                cards = [tag.find_parent('div', class_=re.compile(r'boatlist-.*')) for tag in soup.find_all(attrs={"data-bid": True})]
                cards = [c for c in cards if c] # remove None
                # De-duplicate
                seen_ids = set()
                unique_cards = []
                for c in cards:
                    bid_tag = c.find(attrs={"data-bid": True})
                    if bid_tag:
                        bid = bid_tag.get('data-bid')
                        if bid not in seen_ids:
                            seen_ids.add(bid)
                            unique_cards.append(c)
                cards = unique_cards

        page_results = []
        for card in cards:
            data = self.parse_listing(card)
            if data:
                page_results.append(data)
        return page_results

    async def run(self, start_page=1, end_page=1452):
        logging.info(f"Starting Yachtall scraping from page {start_page} to {end_page}")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            chunk_size = 30
            for i in range(start_page, end_page + 1, chunk_size):
                current_end = min(i + chunk_size, end_page + 1)
                tasks = [self.fetch_page(client, p) for p in range(i, current_end)]
                pages_html = await asyncio.gather(*tasks)
                
                for html in pages_html:
                    items = self.process_page_html(html)
                    self.all_data.extend(items)
                
                logging.info(f"Yachtall Progress: {len(self.all_data)} boats collected (up to page {current_end-1})")
                
                if not any(pages_html):
                    break
                
                await asyncio.sleep(1)

        if self.all_data:
            df = pd.DataFrame(self.all_data)
            df.to_csv("yachtall_boats.csv", index=False)
            df.to_json("yachtall_boats.json", orient="records", indent=4)
            logging.info(f"Yachtall Scraping complete. Total boats: {len(self.all_data)}. Data saved.")
        else:
            logging.warning("No data collected from Yachtall.")

if __name__ == "__main__":
    scraper = YachtallScraper(max_concurrent=30)
    # Total pages observed in sample: 1452
    asyncio.run(scraper.run(start_page=1, end_page=1452))
