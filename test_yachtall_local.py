
from bs4 import BeautifulSoup
from yachtall_scraper import YachtallScraper
import re

def test_local_parsing():
    scraper = YachtallScraper()
    file_path = 'yachtall.html'
    
    with open(file_path, 'r') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    # Clean view-source
    line_contents = soup.find_all('td', class_='line-content')
    if line_contents:
        actual_html = "".join([lc.get_text() for lc in line_contents])
        soup = BeautifulSoup(actual_html, 'html.parser')

    cards = soup.find_all(attrs={"data-bid": True})
    # Wrap in parent div to simulate boatlist-item
    unique_parents = []
    seen_ids = set()
    for c in cards:
        bid = c.get('data-bid')
        if bid not in seen_ids:
            seen_ids.add(bid)
            unique_parents.append(c.find_parent('div'))

    print(f"Found {len(unique_parents)} potential boat cards.")
    
    for i, card in enumerate(unique_parents[:10]):
        if not card: continue
        data = scraper.parse_listing(card)
        if data:
            print(f"Card {i+1}: ID={data.get('id')}, Make='{data.get('make')}', Model='{data.get('model')}', Price={data.get('price')}, Year={data.get('year')}")
        else:
            print(f"Card {i+1}: Failed to parse")

if __name__ == "__main__":
    test_local_parsing()
