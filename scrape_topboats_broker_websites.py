import json
import re
import csv
import asyncio
import httpx
from bs4 import BeautifulSoup
from config import ZYTE_PROXY
from tqdm.asyncio import tqdm

def is_junk_broker(name):
    name = name.strip()
    if re.match(r'^[€$£]?\s*[\d\.,]+$', name): return True
    if len(name) < 4: return True
    if name.lower() in ('private', 'venditore privato', 'private seller', 
                        'band of boats', 'privat', 'privé', 'particulier'): return True
    return False

async def extract_website_from_ad(client, url):
    try:
        resp = await client.get(url, follow_redirects=True, timeout=30)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        broker_links = soup.select('.enhanced-seller-details-card-container a')
        for a in broker_links:
            href = a.get('href', '')
            if href.startswith('http') and 'topboats.com' not in href and 'maps.google.com' not in href and 'google.com/maps' not in href:
                return href
    except Exception:
        pass
    return None

async def process_broker(client, semaphore, broker, urls):
    website = None
    async with semaphore:
        for url in urls[:3]:  # Proviamo fino a 3 URL
            website = await extract_website_from_ad(client, url)
            if website:
                break
    return {
        'broker': broker,
        'annunci_topboats': len(urls),
        'website': website
    }

async def async_main():
    print("Caricamento DB...")
    try:
        with open('master_boats_db.json', 'r') as f:
            db = json.load(f)
    except Exception as e:
        print(f"Error reading DB: {e}")
        return

    broker_ads = {}
    for b in db:
        if b.get('source') == 'topboats' and b.get('broker') and b.get('url'):
            broker = b['broker'].strip()
            if not is_junk_broker(broker):
                if broker not in broker_ads:
                    broker_ads[broker] = []
                broker_ads[broker].append(b['url'])

    ranked = sorted(broker_ads.items(), key=lambda x: len(x[1]), reverse=True)
    MIN_ANNUNCI = 15
    top_brokers = [(b, urls) for b, urls in ranked if len(urls) >= MIN_ANNUNCI]
    print(f"Trovati {len(top_brokers)} broker con almeno {MIN_ANNUNCI} annunci su TopBoats.")

    # Limitiamo la concorrenza a 50 per non saturare la connessione o l'API
    semaphore = asyncio.Semaphore(50)
    
    async with httpx.AsyncClient(proxy=ZYTE_PROXY, verify=False) as client:
        tasks = [process_broker(client, semaphore, broker, urls) for broker, urls in top_brokers]
        results = []
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Estrazione siti web"):
            try:
                res = await f
                results.append(res)
            except Exception as e:
                pass

    results.sort(key=lambda x: x['annunci_topboats'], reverse=True)
    
    out_file = 'topboats_brokers_websites.csv'
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['broker', 'annunci_topboats', 'website'])
        w.writeheader()
        w.writerows(results)
        
    print(f"\nSalvato: {out_file}")
    
    print("\nRisultati trovati (primi 20):")
    for r in results[:20]:
        if r['website']:
            print(f"✅ {r['broker'][:40]:<40} -> {r['website']}")
        else:
            print(f"❌ {r['broker'][:40]:<40} -> Nessun sito web trovato")

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()