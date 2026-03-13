
import httpx
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from config import ZYTE_PROXY
from tqdm import tqdm
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("boat24.log"),
        logging.StreamHandler()
    ]
)

class Boat24Scraper:
    def __init__(self, max_concurrent=20):
        self.base_url = "https://www.boat24.com"
        self.search_url = "https://www.boat24.com/it/barcheusate/?page={}"
        self.proxy = ZYTE_PROXY
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.all_data = []

    def parse_listing(self, card):
        try:
            # card is a div with class "blurb" (or similar)
            # Find the main link/title
            title_tag = card.find('h3', class_='blurb__title')
            if not title_tag: return None
            
            link_tag = title_tag.find('a')
            if not link_tag: return None
            
            url = link_tag.get('href', '')
            if url and not url.startswith('http'):
                url = self.base_url + url
                
            title = link_tag.get_text(strip=True)
            
            # ID is often in data-id of bookmark or similar
            boat_id = ""
            bookmark = card.find('div', class_='blurb__bookmark')
            if bookmark:
                boat_id = bookmark.get('data-id', '')
            
            # If not found, extract from URL
            if not boat_id:
                id_match = re.search(r'/detail/(\d+)/', url)
                if id_match:
                    boat_id = id_match.group(1)

            # Price
            price_numeric = None
            price_text = ""
            price_tag = card.find('p', class_='blurb__price')
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                clean_price = re.sub(r'[^\d]', '', price_text)
                if clean_price:
                    try:
                        price_numeric = int(clean_price)
                    except:
                        pass

            # Facts (Dimensions, Year, Engine)
            year = None
            length = None
            category = ""
            
            # Category is often above the title
            cat_tag = card.find('p', class_='blurb__title-header')
            if cat_tag:
                category = cat_tag.get_text(strip=True)

            facts = card.find_all('li', class_='blurb__fact')
            for fact in facts:
                key_tag = fact.find('span', class_='blurb__key')
                val_tag = fact.find('span', class_='blurb__value')
                if not key_tag or not val_tag: continue
                
                key = key_tag.get_text(strip=True).lower()
                val = val_tag.get_text(strip=True)
                
                if 'anno' in key:
                    year_match = re.search(r'(\d{4})', val)
                    if year_match:
                        year = int(year_match.group(1))
                elif 'dimensioni' in key or 'lunghezza' in key:
                    # "11,99 x 4,02 m"
                    length_match = re.search(r'(\d+[\.,]\d*)', val)
                    if length_match:
                        length = float(length_match.group(1).replace(',', '.'))

            # Image
            img_tag = card.find('img')
            img_url = ""
            if img_tag:
                # Boat24 uses data-srcset or data-src for lazyload
                img_url = img_tag.get('data-src') or img_tag.get('src')
                if not img_url or 'alpha.gif' in img_url:
                    # Try to find first image in srcset
                    srcset = img_tag.get('data-srcset')
                    if srcset:
                        img_url = srcset.split(',')[0].split(' ')[0]

            # Location/Broker info
            location = ""
            country = "italia" # Default se non troviamo nazioni estere
            location_tag = card.find('p', class_='blurb__location')
            if location_tag:
                location = location_tag.get_text(strip=True)
                
                # Lista delle nazioni comuni in italiano usate da Boat24
                known_countries = {
                    'germania', 'francia', 'spagna', 'croazia', 'grecia', 'olanda',
                    'svizzera', 'austria', 'turchia', 'belgio', 'danimarca', 
                    'svezia', 'norvegia', 'regno unito', 'gran bretagna', 'portogallo', 
                    'polonia', 'malta', 'cipro', 'monaco', 'montenegro', 'slovenia'
                }
                
                # Cerca di estrarre la nazione (es. "Spagna»Denia" o "Croazia")
                loc_lower = location.lower()
                
                # Se contiene il separatore », la prima parte è spesso la nazione o una regione italiana
                first_part = loc_lower.split('»')[0].strip()
                if first_part in known_countries:
                    country = first_part
                else:
                    # Fallback: cerca se una nazione nota è menzionata nella stringa
                    for kc in known_countries:
                        if kc in loc_lower:
                            # Evita falsi positivi (es. se ci fosse una città che si chiama come una nazione)
                            if loc_lower.startswith(kc):
                                country = kc
                                break
                            
                # Fallback vecchi codici tra parentesi (es. (HR))
                code_match = re.search(r'\( ([A-Z]{1,3}) \)', location) or re.search(r'\(([A-Z]{1,3})\)', location)
                if code_match and country == "italia":
                    code = code_match.group(1).upper()
                    country_map = {
                        'D': 'germania', 'F': 'francia', 'E': 'spagna', 'HR': 'croazia', 
                        'CH': 'svizzera', 'GR': 'grecia', 'NL': 'olanda', 'TR': 'turchia', 
                        'AT': 'austria', 'BE': 'belgio', 'DK': 'danimarca', 'SE': 'svezia', 
                        'NO': 'norvegia', 'UK': 'regno-unito', 'GB': 'regno-unito',
                        'PT': 'portogallo', 'PL': 'polonia', 'SI': 'slovenia', 'MT': 'malta', 
                        'CY': 'cipro', 'MC': 'monaco', 'ME': 'montenegro'
                    }
                    # Assicuriamoci che non sia una sigla di provincia italiana (2 lettere che non sono in mappa)
                    if code in country_map:
                        country = country_map[code]

            # Extract make/model from URL
            # Structure: /it/category/make-slug/model-slug/detail/id/
            builder = ""
            model = ""
            try:
                path_parts = url.strip('/').split('/')
                if 'detail' in path_parts:
                    detail_idx = path_parts.index('detail')
                    if detail_idx >= 2:
                        make_slug = path_parts[detail_idx - 2]
                        model_slug = path_parts[detail_idx - 1]
                        
                        # Use the original title to get the correct casing if possible
                        make_readable = make_slug.replace('-', ' ').lower()
                        
                        if title.lower().startswith(make_readable):
                            builder = title[:len(make_readable)].strip()
                            model = title[len(make_readable):].strip()
                        else:
                            builder = make_slug.replace('-', ' ').title()
                            model = model_slug.replace('-', ' ').title()
                            if model.lower().startswith(builder.lower()):
                                model = model[len(builder):].strip()
                
                if not builder and title:
                    parts = title.split(' ', 1)
                    builder = parts[0]
                    model = parts[1] if len(parts) > 1 else ""
            except:
                if title:
                    parts = title.split(' ', 1)
                    builder = parts[0]
                    model = parts[1] if len(parts) > 1 else ""

            return {
                "id": int(boat_id) if boat_id and boat_id.isdigit() else 0,
                "builder": builder,
                "model": model,
                "year_built": int(year) if year else None,
                "country": country,
                "price_eur": float(price_numeric) if price_numeric else None,
                "length": float(length) if length else None,
                "image_url": img_url,
                "source": "boat24",
                "broker": "private", 
                "url": url,
                "category": category,
                "status": True
            }
        except Exception as e:
            logging.error(f"Error parsing Boat24 card: {e}")
            return None

    async def fetch_page(self, client, page_offset):
        url = self.search_url.format(page_offset)
        async with self.semaphore:
            try:
                response = await client.get(url, timeout=60.0)
                if response.status_code == 200:
                    return response.text
                else:
                    logging.error(f"Failed to fetch Boat24 page {page_offset}: Status {response.status_code}")
                    return None
            except Exception as e:
                logging.error(f"Error fetching Boat24 page {page_offset}: {e}")
                return None

    def process_page_html(self, html):
        if not html: return []
        soup = BeautifulSoup(html, 'html.parser')
        # Listings are in <li> items containing a div with class "blurb"
        cards = soup.find_all('div', class_=re.compile(r'\bblurb\b'))
        
        page_results = []
        for card in cards:
            data = self.parse_listing(card)
            if data:
                page_results.append(data)
        return page_results

    async def run(self, start_offset=0, end_offset=34240):
        logging.info(f"Starting Boat24 scraping from offset {start_offset} to {end_offset}")
        
        # Use Zyte Proxy
        proxies = {"all://": self.proxy}
        
        async with httpx.AsyncClient(proxy=self.proxy, verify=False, follow_redirects=True) as client:
            chunk_size = 20 # Increased chunk size
            for i in range(start_offset, end_offset + 20, chunk_size * 20):
                current_end_offset = min(i + chunk_size * 20, end_offset + 20)
                offsets = range(i, current_end_offset, 20)
                
                tasks = [self.fetch_page(client, off) for off in offsets]
                pages_html = await asyncio.gather(*tasks)
                
                for html in pages_html:
                    items = self.process_page_html(html)
                    self.all_data.extend(items)
                
                logging.info(f"Boat24 Progress: {len(self.all_data)} boats collected (up to offset {current_end_offset-20})")
                
                # Check for stop condition (no more boats)
                if not any(pages_html):
                    break
                
                await asyncio.sleep(1)

        if self.all_data:
            df = pd.DataFrame(self.all_data)
            df.to_csv("boat24_boats.csv", index=False)
            df.to_json("boat24_boats.json", orient="records", indent=4)
            logging.info(f"Boat24 Scraping complete. Total boats: {len(self.all_data)}. Data saved.")
        else:
            logging.warning("No data collected from Boat24.")

if __name__ == "__main__":
    scraper = Boat24Scraper(max_concurrent=20)
    # Full offset range as mentioned: page 34240 / 20
    asyncio.run(scraper.run(start_offset=0, end_offset=34240))
