import httpx
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time
from config import ZYTE_PROXY, COUNTRIES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

class TopBoatsScraper:
    def __init__(self, max_threads=5):
        self.base_url = "https://www.topboats.com"
        self.max_threads = max_threads
        self.results = []
        self.proxy = ZYTE_PROXY
        
    def get_session(self):
        return httpx.Client(
            proxy=self.proxy,
            timeout=60.0,
            follow_redirects=True,
            verify=False  # Zyte might use its own certs
        )

    def parse_listing(self, card, country):
        try:
            link_tag = card.find('a', class_='grid-listing-link')
            if not link_tag:
                return None
            
            url = self.base_url + link_tag['href']
            boat_id = link_tag.get('data-reporting-click-product-id', '')
            
            title_tag = card.find('h2', {'data-e2e': 'listingName'})
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # Extract Year from title (e.g., "2008 JPK 998")
            year_match = re.search(r'^(\d{4})', title)
            year = year_match.group(1) if year_match else ""
            
            # Extract data from data-ssr-meta
            # Format: "Cantiere|type|length|location_code|price_numeric"
            ssr_meta = link_tag.get('data-ssr-meta', '')
            cantiere_meta = ""
            categoria = ""
            lunghezza = ""
            if ssr_meta and "|" in ssr_meta:
                meta_parts = ssr_meta.split("|")
                if len(meta_parts) >= 1: cantiere_meta = meta_parts[0].strip()
                if len(meta_parts) >= 2: categoria = meta_parts[1].strip()
                if len(meta_parts) >= 3: lunghezza = meta_parts[2].strip()
            
            if cantiere_meta:
                cantiere = cantiere_meta
                modello = title
                if year:
                    modello = modello.replace(year, "", 1)
                modello = modello.replace(cantiere, "", 1).strip()
            else:
                # Fallback to old split logic
                remaining_title = title.replace(year, "").strip()
                parts = remaining_title.split(" ", 1)
                cantiere = parts[0] if len(parts) > 0 else ""
                modello = parts[1] if len(parts) > 1 else remaining_title
            
            price_tag = card.find('p', {'data-e2e': 'listingPrice'})
            price_text = price_tag.get_text(strip=True) if price_tag else ""
            
            # Numeric Price Extraction
            price_numeric = None
            if price_text and any(char.isdigit() for char in price_text):
                # Remove everything except digits
                clean_price = re.sub(r'[^\d]', '', price_text)
                if clean_price:
                    price_numeric = int(clean_price)
            
            # Numeric Length Extraction
            length_numeric = None
            if lunghezza:
                try:
                    length_numeric = float(lunghezza)
                except ValueError:
                    pass

            broker_tag = card.find('p', {'data-e2e': 'listingSellerContent'})
            broker_text = broker_tag.get_text(strip=True) if broker_tag else ""
            
            broker = ""
            localita = ""
            if "|" in broker_text:
                seller_parts = broker_text.split("|", 1)
                broker = seller_parts[0].strip()
                localita = seller_parts[1].strip()
            else:
                broker = broker_text
            
            # Tags / Condition
            tags = [tag.get_text(strip=True) for tag in card.find_all('label', class_=re.compile('style-module_label'))]
            condizione = "Nuovo" if any(t.lower() in ["new", "nuovo"] for t in tags) else "Usato"
            
            img_tag = card.find('div', {'data-e2e': 'listingImage'}).find('img') if card.find('div', {'data-e2e': 'listingImage'}) else None
            img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
            
            return {
                "id": int(boat_id) if boat_id and boat_id.isdigit() else 0,
                "builder": cantiere,
                "model": modello,
                "year_built": int(year) if year.isdigit() else None,
                "country": country,
                "price_eur": float(price_numeric) if price_numeric else None,
                "length": float(length_numeric) if length_numeric else None,
                "image_url": img_url,
                "source": "topboats",
                "broker": broker,
                "url": url,
                "category": categoria,
                "status": True
            }
        except Exception as e:
            logging.error(f"Error parsing card: {e}")
            return None

    def scrape_country(self, country, max_pages=None):
        country_results = []
        page = 1
        
        with self.get_session() as client:
            while True:
                if max_pages and page > max_pages:
                    logging.info(f"Reached max_pages limit ({max_pages}) for {country}")
                    break
                    
                # https://www.topboats.com/it/barche-in-vendita/paese-francia/page-2/
                page_url = f"{self.base_url}/it/barche-in-vendita/paese-{country}/"
                if page > 1:
                    page_url += f"page-{page}/"
                
                logging.info(f"Scraping {country} - Page {page}")
                
                try:
                    retries = 3
                    for attempt in range(retries):
                        response = client.get(page_url)
                        if response.status_code == 200:
                            break
                        if response.status_code in [502, 503, 504, 429] and attempt < retries - 1:
                            wait_time = (attempt + 1) * 2
                            logging.warning(f"Status {response.status_code} on {page_url}. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        break

                    # Detect pagination end: redirect to page 1
                    if page > 1 and str(response.url).strip("/") == f"{self.base_url}/it/barche-in-vendita/paese-{country}".strip("/"):
                        logging.info(f"End of pagination reached for {country} (redirected to page 1)")
                        break
                    
                    if response.status_code != 200:
                        logging.error(f"Failed to fetch {page_url}: {response.status_code}")
                        break
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    cards = soup.find_all('div', class_='grid-item')
                    
                    if not cards:
                        logging.info(f"No cards found for {country} at page {page}")
                        break
                        
                    for card in cards:
                        data = self.parse_listing(card, country)
                        if data:
                            country_results.append(data)
                    
                    page += 1
                    # Small delay to be polite and let Zyte breathe
                    time.sleep(0.5)
                    
                except Exception as e:
                    logging.error(f"Error scraping {country} page {page}: {e}")
                    break
        
        return country_results

    def run(self):
        logging.info(f"Starting scraper for {len(COUNTRIES)} countries with {self.max_threads} threads.")
        
        all_data = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Wrap with tqdm for progress bar
            futures = {executor.submit(self.scrape_country, country): country for country in COUNTRIES}
            
            for future in tqdm(futures, total=len(COUNTRIES), desc="Processing Countries"):
                country = futures[future]
                try:
                    data = future.result()
                    all_data.extend(data)
                    logging.info(f"Finished {country}: {len(data)} boats found.")
                except Exception as e:
                    logging.error(f"Country {country} failed: {e}")
        
        if all_data:
            df = pd.DataFrame(all_data)
            df.to_csv("topboats_data.csv", index=False)
            df.to_json("topboats_data.json", orient="records", indent=4)
            logging.info(f"Scraping complete. Total boats: {len(all_data)}. Data saved to CSV and JSON.")
        else:
            logging.warning("No data collected.")

if __name__ == "__main__":
    scraper = TopBoatsScraper(max_threads=10)
    scraper.run()
