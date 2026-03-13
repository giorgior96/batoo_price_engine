import httpx
from bs4 import BeautifulSoup
from config import ZYTE_PROXY

url = "https://www.topboats.com/it/barca/2020-tige-22rzx-9649363/"

with httpx.Client(proxy=ZYTE_PROXY, verify=False) as client:
    resp = client.get(url)
    print(f"Status Code: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Try to find the broker website link
    # Usually it's an anchor tag around the seller profile or somewhere else on the page
    # The user mentioned a specific div class: enhanced-seller-details-card-container__profile-right-section
    
    seller_section = soup.find('div', class_='enhanced-seller-details-card-container__profile-right-section')
    if seller_section:
        print("Found seller section!")
        
    # Let's find all external links in the page to see if any looks like the broker's website
    # or look for a specific "Website" button
    links = soup.find_all('a', href=True)
    external_links = []
    for a in links:
        href = a['href']
        if href.startswith('http') and 'topboats.com' not in href and 'facebook.com' not in href and 'instagram.com' not in href and 'twitter.com' not in href and 'youtube.com' not in href:
            external_links.append(href)
            
    print("External Links:", set(external_links))
    
    # Let's find the text "Sito web" or similar
    for a in links:
        text = a.get_text(strip=True).lower()
        if 'sito' in text or 'website' in text or 'web' in text:
            print("Found website link by text:", a['href'], text)
            
    # Also print any a tag that is a child of some broker info section
    broker_links = soup.select('.enhanced-seller-details-card-container a')
    for a in broker_links:
        print("Broker section link:", a.get('href'))
