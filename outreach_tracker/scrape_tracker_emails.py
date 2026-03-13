import csv
import re
import asyncio
import httpx
from urllib.parse import urljoin, urlparse
from tqdm.asyncio import tqdm

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
SKIP_WORDS = ['noreply', 'privacy', 'webmaster', 'support@', 'example', 
              'sentry', 'google', 'facebook', 'yachtall', 'topboats', 
              'boat24', 'mondialbroker', 'schema', 'wix', 'wordpress', 'domain']

CONTACT_PATHS = ['', '/contact', '/contacts', '/contact-us', '/contatti', '/about', '/about-us']

def is_valid_email(email):
    email = email.lower()
    if any(sw in email for sw in SKIP_WORDS):
        return False
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

async def process_website(client, semaphore, row, index):
    website = row['website'].strip()
    
    found_emails = set()
    if website:
        if not website.startswith('http'):
            website = 'http://' + website
            
        parsed_url = urlparse(website)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        async with semaphore:
            tasks = []
            for path in CONTACT_PATHS:
                full_url = urljoin(base_url, path)
                tasks.append(fetch_and_extract(client, full_url))
            
            results = await asyncio.gather(*tasks)
            for emails in results:
                found_emails.update(emails)

    return index, ', '.join(sorted(found_emails)) if found_emails else ''

async def async_main():
    brokers = []
    with open('broker_tracker.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            brokers.append(row)
            
    print(f"Caricati {len(brokers)} broker da broker_tracker.csv")

    to_process = [(i, b) for i, b in enumerate(brokers) if not b['email'].strip() and b['website'].strip()]
    print(f"Broker senza email ma con sito web da scansionare: {len(to_process)}")

    if not to_process:
        print("Nessun broker da scansionare. Esco.")
        return

    semaphore = asyncio.Semaphore(30)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*'
    }

    async with httpx.AsyncClient(verify=False, headers=headers) as client:
        tasks = [process_website(client, semaphore, row, idx) for idx, row in to_process]
        
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scansione siti"):
            try:
                idx, emails = await f
                if emails:
                    brokers[idx]['email'] = emails
            except Exception as e:
                pass
                
    found_count = sum(1 for idx, row in to_process if brokers[idx]['email'])
    print(f"Trovate email per {found_count} broker su {len(to_process)} scansionati.")

    with open('broker_tracker.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(brokers)
        
    print("File broker_tracker.csv aggiornato con successo.")

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()
