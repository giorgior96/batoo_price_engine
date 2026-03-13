#!/usr/bin/env python3
"""
Step 1: Estrae top broker da topboats + yachtall dal JSON locale
Step 2: Cerca su DuckDuckGo per trovare il loro sito web + email
"""
import json, re, time, csv, httpx
from collections import defaultdict
from urllib.parse import quote_plus

# --- Configurazione ---
SOURCES = {'topboats', 'yachtall'}
MIN_ANNUNCI = 15
MAX_BROKERS = 100
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
SKIP_WORDS = ['noreply', 'privacy', 'webmaster', 'support@', 'example', 
              'sentry', 'google', 'facebook', 'yachtall', 'topboats', 
              'boat24', 'mondialbroker', 'schema', 'wix', 'wordpress']

# Nomi da ignorare (dati sporchi)
def is_junk_broker(name):
    name = name.strip()
    # Prezzi tipo "€ 55.000"
    if re.match(r'^[€$£]?\s*[\d\.,]+$', name): return True
    # Troppo corto
    if len(name) < 4: return True
    # Private
    if name.lower() in ('private', 'venditore privato', 'private seller', 
                        'band of boats', 'privat', 'privé', 'particulier'): return True
    return False

# --- STEP 1: Carica e filtra broker ---
print("Loading database...")
data = json.load(open('/home/giorgio/Scrivania/scraper/master_boats_db.json'))
print(f"Loaded {len(data)} boats")

broker_map = defaultdict(lambda: {'count': 0, 'sources': set()})
for boat in data:
    broker = (boat.get('broker') or '').strip()
    source = boat.get('source', '')
    if source in SOURCES and broker and not is_junk_broker(broker):
        broker_map[broker]['count'] += 1
        broker_map[broker]['sources'].add(source)

# Ordina per volume
ranked = sorted(broker_map.items(), key=lambda x: x[1]['count'], reverse=True)
ranked = [(b, v) for b, v in ranked if v['count'] >= MIN_ANNUNCI][:MAX_BROKERS]

print(f"\nTop {len(ranked)} brokers selezionati (min {MIN_ANNUNCI} annunci):")
for i, (broker, info) in enumerate(ranked[:20]):
    print(f"  {i+1:>3}. {broker[:50]:<50} {info['count']:>4} ann. | {', '.join(info['sources'])}")
print(f"  ... e altri {max(0, len(ranked)-20)}\n")

# --- STEP 2: DuckDuckGo search per ogni broker ---
def search_ddg(query):
    """Cerca su DuckDuckGo e restituisce i primi link/snippets"""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120',
        'Accept': 'text/html',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        r = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"    DDG error: {e}")
    return ''

def extract_first_result_url(html):
    """Estrae il primo URL dai risultati DuckDuckGo"""
    # DDG result links sono in format: <a class="result__url" href="...">
    urls = re.findall(r'class="result__url"[^>]*href="([^"]+)"', html)
    if urls:
        return urls[0]
    # Fallback: cerca redirect DuckDuckGo
    ddg_links = re.findall(r'//duckduckgo\.com/l/\?uddg=([^&"]+)', html)
    if ddg_links:
        from urllib.parse import unquote
        return unquote(ddg_links[0])
    # Fallback: qualsiasi link https
    links = re.findall(r'href="(https?://(?!duckduckgo)[^"]+)"', html)
    return links[0] if links else ''

def extract_emails_from_page(url, http_client):
    """Fetcha una pagina e cerca email"""
    try:
        r = http_client.get(url, timeout=12)
        if r.status_code != 200:
            return set(), ''
        emails = {e for e in EMAIL_RE.findall(r.text)
                 if not any(s in e.lower() for s in SKIP_WORDS) and '.' in e.split('@')[1]}
        return emails, url
    except:
        return set(), ''

print("="*60)
print("STEP 2: Ricerca DuckDuckGo per email broker")
print("="*60)

results = []
http = httpx.Client(timeout=15, follow_redirects=True,
                   headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120'})

for i, (broker, info) in enumerate(ranked):
    n = info['count']
    sources_str = '+'.join(sorted(info['sources']))
    print(f"\n[{i+1}/{len(ranked)}] {broker[:50]:<50} ({n} ann, {sources_str})")
    
    # Query DuckDuckGo
    query = f'"{broker}" yacht broker email contact'
    print(f"  🔍 Searching: {query[:60]}...")
    
    ddg_html = search_ddg(query)
    
    # Estrai email direttamente dagli snippet DDG (le pagine li includono)
    snippet_emails = {e for e in EMAIL_RE.findall(ddg_html)
                     if not any(s in e.lower() for s in SKIP_WORDS) and '.' in e.split('@')[1]}
    
    # Estrai primo URL risultato
    first_url = extract_first_result_url(ddg_html)
    
    website_emails = set()
    website = ''
    if first_url and 'duckduckgo' not in first_url:
        website = re.match(r'https?://[^/]+', first_url).group(0) if re.match(r'https?://[^/]+', first_url) else first_url
        print(f"  🌐 Website: {website}")
        website_emails, _ = extract_emails_from_page(first_url, http)
        
        # Se non trovate email → prova /contact
        if not website_emails:
            for path in ['/contact', '/contacts', '/contact-us', '/contatti', '/about']:
                contact_emails, _ = extract_emails_from_page(website + path, http)
                if contact_emails:
                    website_emails = contact_emails
                    print(f"  📧 Found on {path}")
                    break
            time.sleep(0.3)
    
    all_emails = snippet_emails | website_emails
    email_str = ', '.join(sorted(all_emails)) if all_emails else ''
    
    if all_emails:
        print(f"  ✅ EMAIL: {email_str[:80]}")
    else:
        print(f"  ⚪ No email found")
    
    results.append({
        'broker': broker, 'annunci': n, 'sources': sources_str,
        'email': email_str, 'website': website,
        'has_email': bool(all_emails)
    })
    
    time.sleep(1.5)  # cortesia verso DDG per non essere bannati

http.close()

# Salva CSV
out_path = '/tmp/broker_emails_ddg.csv'
with open(out_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['broker','annunci','sources','email','website','has_email'])
    w.writeheader()
    w.writerows(results)

found = sum(1 for r in results if r['has_email'])
print(f"\n{'='*60}")
print(f"RISULTATI: {len(results)} broker | {found} con email ({found/len(results)*100:.0f}%)")
print(f"Salvato: {out_path}")
print("\nBroker con email trovata:")
for r in results:
    if r['has_email']:
        print(f"  ✅ {r['broker'][:45]:<45} | {r['email'][:50]}")
