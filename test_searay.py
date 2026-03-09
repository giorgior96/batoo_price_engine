from bs4 import BeautifulSoup
import re

def parse_listing_local(card):
    link_tag = card.find('a', class_='grid-listing-link')
    if not link_tag: return None
    
    ssr_meta = link_tag.get('data-ssr-meta', '')
    cantiere_meta = ssr_meta.split("|")[0].strip() if ssr_meta and "|" in ssr_meta else ""
    
    title_tag = card.find('h2', {'data-e2e': 'listingName'})
    title = title_tag.get_text(strip=True) if title_tag else ""
    
    year_match = re.search(r'^(\d{4})', title)
    year = year_match.group(1) if year_match else ""
    
    cantiere = cantiere_meta if cantiere_meta else "Unknown"
    
    modello = title
    if year:
        modello = modello.replace(year, "", 1)
    if cantiere:
        modello = modello.replace(cantiere, "", 1).strip()
            
    return {
        "anno": year,
        "cantiere": cantiere,
        "modello": modello,
        "title": title
    }

file_path = 'view-source_https___www.topboats.com_it_barche-in-vendita_paese-francia_page-2_.html'
with open(file_path, 'r') as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')
lines = soup.find_all('td', class_='line-content')
actual_html = "".join([line.get_text() for line in lines])

soup2 = BeautifulSoup(actual_html, 'html.parser')
cards = soup2.find_all('div', class_='grid-item')

for card in cards:
    if "Sea Ray" in card.get_text():
        data = parse_listing_local(card)
        if data:
            print(f"FOUND: Title='{data['title']}' -> Cantiere='{data['cantiere']}', Modello='{data['modello']}'")
