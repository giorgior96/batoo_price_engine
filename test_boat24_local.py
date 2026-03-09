
from bs4 import BeautifulSoup
from boat24_scraper import Boat24Scraper
import re

def test_local_parsing():
    scraper = Boat24Scraper()
    file_path = 'boat24.html'
    
    with open(file_path, 'r') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    # Clean view-source
    line_contents = soup.find_all('td', class_='line-content')
    if line_contents:
        actual_html = "".join([lc.get_text() for lc in line_contents])
        soup = BeautifulSoup(actual_html, 'html.parser')

    cards = soup.find_all('div', class_=re.compile(r'\bblurb\b'))
    
    print(f"Found {len(cards)} cards with class 'blurb'.")
    
    for i, card in enumerate(cards[:5]):
        data = scraper.parse_listing(card)
        if data:
            print(f"Card {i+1}: ID={data.get('id')}, Make='{data.get('make')}', Model='{data.get('model')}', Price={data.get('price')}")
        else:
            print(f"Card {i+1}: Failed to parse")

if __name__ == "__main__":
    test_local_parsing()
