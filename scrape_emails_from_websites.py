import csv
import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm.asyncio import tqdm

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
SKIP_WORDS = ['noreply', 'privacy', 'webmaster', 'support@', 'example', 
              'sentry', 'google', 'facebook', 'yachtall', 'topboats', 
              'boat24', 'mondialbroker', 'schema', 'wix', 'wordpress', 'domain']

# Path to crawl inside the website looking for emails
CONTACT_PATHS = ['', '/contact', '/contacts', '/contact-us', '/contatti', '/about', '/about-us']

def is_valid_email(email):
    email = email.lower()
    if any(sw in email for sw in SKIP_WORDS):
        return False
    # Extra checks: must have a dot after @, cannot end with common image extensions
    if '.' not in email.split('@')[1]: return False
    if email.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')): return False
    return True

def extract_emails_from_html(html):
    emails = EMAIL_RE.findall(html)
    valid_emails = {e.lower() for e in emails if is_valid_email(e)}
    return valid_emails

async def fetch_and_extract(client, url):
    try:
        resp = await client.get(url, follow_redirects=True, timeout=15)
        if resp.status_code == 200:
            return extract_emails_from_html(resp.text)
    except Exception:
        pass
    return set()

async def process_website(client, semaphore, row):
    website = row['website']
    broker = row['broker']
    annunci = row['annunci_topboats']
    
    found_emails = set()
    
    if website:
        # Assicurati che l'URL abbia lo schema
        if not website.startswith('http'):
            website = 'http://' + website
            
        parsed_url = urlparse(website)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        async with semaphore:
            # Parallelizziamo le richieste per i path comuni del sito web
            tasks = []
            for path in CONTACT_PATHS:
                full_url = urljoin(base_url, path)
                tasks.append(fetch_and_extract(client, full_url))
            
            results = await asyncio.gather(*tasks)
            for emails in results:
                found_emails.update(emails)

    return {
        'broker': broker,
        'annunci_topboats': annunci,
        'website': website,
        'emails': ', '.join(sorted(found_emails)) if found_emails else ''
    }

async def async_main():
    brokers = []
    with open('topboats_brokers_websites.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            brokers.append(row)
            
    print(f"Caricati {len(brokers)} broker da topboats_brokers_websites.csv")

    # Filtriamo solo quelli con sito web
    to_process = [b for b in brokers if b['website']]
    print(f"Broker con sito web da scansionare: {len(to_process)}")

    semaphore = asyncio.Semaphore(30) # Non andiamo troppo veloci altrimenti alcuni server ci bloccano
    
    # Non usiamo proxy qui se non necessario (a meno che non ti blocchino molto)
    # in tal caso potremmo rimettere ZYTE_PROXY, ma i siti dei broker di solito non bloccano.
    # Proviamo senza proxy per maggiore velocità, ma con User-Agent di un browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    results = []
    
    async with httpx.AsyncClient(verify=False, headers=headers) as client:
        tasks = [process_website(client, semaphore, row) for row in to_process]
        
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scansione siti"):
            try:
                res = await f
                results.append(res)
            except Exception as e:
                pass

    # Aggiungiamo quelli senza sito con email vuota
    no_website = [b for b in brokers if not b['website']]
    for b in no_website:
        results.append({
            'broker': b['broker'],
            'annunci_topboats': b['annunci_topboats'],
            'website': '',
            'emails': ''
        })

    # Ri-ordiniamo per annunci
    results.sort(key=lambda x: int(x['annunci_topboats']), reverse=True)
    
    out_file = 'topboats_brokers_emails.csv'
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['broker', 'annunci_topboats', 'website', 'emails'])
        w.writeheader()
        w.writerows(results)
        
    print(f"\nSalvato: {out_file}")
    
    found_count = sum(1 for r in results if r['emails'])
    print(f"Trovate email per {found_count} broker su {len(results)} totali.")

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()