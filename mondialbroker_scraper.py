import httpx
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mondialbroker.log"),
        logging.StreamHandler()
    ]
)

class MondialBrokerScraper:
    def __init__(self, max_threads=10, max_concurrent_details=5):
        self.base_url = "https://www.mondialbroker.com/"
        self.search_url = "https://www.mondialbroker.com/cerca.aspx?opp=50&p={}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.max_threads = max_threads
        self.semaphore = asyncio.Semaphore(max_concurrent_details)
        self.all_data = []

    def uuid_to_int(self, uuid_str):
        if not uuid_str: return 0
        return int(hashlib.md5(uuid_str.encode()).hexdigest(), 16) % (2**31 - 1)

    def parse_listing(self, card):
        try:
            link = card.get('href', '')
            full_url = self.base_url + link if link.startswith('Barca.aspx') else link
            
            boat_id_str = ""
            pk_match = re.search(r'pk=([a-z0-9-]+)', link)
            if pk_match:
                boat_id_str = pk_match.group(1)
            
            boat_id = self.uuid_to_int(boat_id_str)

            title_tag = card.find('span', class_='blue bold')
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            builder = ""
            model = ""
            if title and " - " in title:
                parts = title.split(" - ", 1)
                builder = parts[0].strip()
                model = parts[1].strip()
            elif title:
                builder = title
            
            img_tag = card.find('img', id=re.compile(r'ImageBarca'))
            if not img_tag:
                img_div = card.find('div', class_=re.compile(r'col-.*-2'))
                if img_div:
                    img_tag = img_div.find('img')
            
            img_url = ""
            if img_tag:
                img_url = img_tag.get('src', '')
                if img_url and not img_url.startswith('http'):
                    img_url = self.base_url + img_url

            all_divs = card.find_all('div', recursive=False)
            
            year_text = ""
            lunghezza_text = ""
            localita = ""
            broker = ""

            if len(all_divs) >= 8:
                lunghezza_text = all_divs[3].get_text(strip=True)
                year_text = all_divs[4].get_text(strip=True)
                localita = all_divs[6].get_text(strip=True)
                broker = all_divs[7].get_text(strip=True)
            
            year_match = re.search(r'(\d{4})', year_text)
            year_numeric = int(year_match.group(1)) if year_match else None

            length_numeric = None
            if lunghezza_text:
                clean_length = lunghezza_text.replace(',', '.')
                length_match = re.search(r'(\d+\.?\d*)', clean_length)
                if length_match:
                    try:
                        length_numeric = float(length_match.group(1))
                    except:
                        pass

            return {
                "id": boat_id,
                "builder": builder,
                "model": model,
                "year_built": year_numeric,
                "country": "italia", # MondialBroker is primarily Italy
                "price_eur": None,
                "length": length_numeric,
                "image_url": img_url,
                "source": "mondialbroker",
                "broker": broker,
                "url": full_url,
                "category": "",
                "status": True
            }
        except Exception as e:
            logging.error(f"Error parsing Mondial Broker card: {e}")
            return None

    async def fetch_page(self, client, page):
        url = self.search_url.format(page)
        try:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            logging.error(f"Error fetching page {page}: {e}")
            return None

    async def fetch_detail(self, client, item):
        async with self.semaphore:
            try:
                response = await client.get(item['url'], headers=self.headers, timeout=30.0)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract Price
                    price_dt = soup.find('dt', string=re.compile(r'Prezzo', re.I))
                    if price_dt:
                        price_dd = price_dt.find_next_sibling('dd')
                        if price_dd:
                            price_text = price_dd.get_text(strip=True)
                            clean_price = re.sub(r'[^\d]', '', price_text)
                            if clean_price:
                                try:
                                    item['price_eur'] = float(clean_price)
                                except:
                                    pass
                    
                    # Extract Category
                    cat_link = soup.find('a', id='Content_LinkCorrelati2')
                    if cat_link:
                        cat_b = cat_link.find('b')
                        if cat_b:
                            item['category'] = cat_b.get_text(strip=True)
                    
                    if not item['category']:
                        cat_dt = soup.find('dt', string=re.compile(r'Categoria', re.I))
                        if cat_dt:
                            cat_dd = cat_dt.find_next_sibling('dd')
                            if cat_dd:
                                item['category'] = cat_dd.get_text(strip=True)

            except Exception as e:
                logging.error(f"Error fetching detail for {item['url']}: {e}")
        return item

    def process_page_html(self, html):
        if not html: return []
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('a', class_=re.compile(r'\bbarca\b'))
        
        page_results = []
        for card in cards:
            data = self.parse_listing(card)
            if data:
                page_results.append(data)
        return page_results

    async def run(self, start_page=1, end_page=323):
        logging.info(f"Starting Mondial Broker scraping from page {start_page} to {end_page}")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Step 1: Collect all basic info from listing pages
            chunk_size = 5
            for i in range(start_page, end_page + 1, chunk_size):
                current_end = min(i + chunk_size, end_page + 1)
                tasks = [self.fetch_page(client, p) for p in range(i, current_end)]
                pages_html = await asyncio.gather(*tasks)
                
                page_items = []
                for html in pages_html:
                    items = self.process_page_html(html)
                    page_items.extend(items)
                
                # Step 2: For each boat in the current chunk, fetch details (price, etc.)
                detail_tasks = [self.fetch_detail(client, item) for item in page_items]
                updated_items = await asyncio.gather(*detail_tasks)
                
                self.all_data.extend(updated_items)
                logging.info(f"Progress: {len(self.all_data)} boats collected (up to page {current_end-1})")
                await asyncio.sleep(0.5)

        if self.all_data:
            df = pd.DataFrame(self.all_data)
            df.to_csv("mondialbroker_boats.csv", index=False)
            df.to_json("mondialbroker_boats.json", orient="records", indent=4)
            logging.info(f"Scraping complete. Total boats: {len(self.all_data)}. Data saved.")
        else:
            logging.warning("No data collected.")

if __name__ == "__main__":
    scraper = MondialBrokerScraper(max_threads=10, max_concurrent_details=10)
    # The user mentioned 323 pages
    asyncio.run(scraper.run(start_page=1, end_page=323))
