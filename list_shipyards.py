from bs4 import BeautifulSoup

file_path = 'view-source_https___www.topboats.com_it_barche-in-vendita_paese-francia_page-2_.html'
with open(file_path, 'r') as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')
lines = soup.find_all('td', class_='line-content')
actual_html = "".join([line.get_text() for line in lines])

soup2 = BeautifulSoup(actual_html, 'html.parser')
links = soup2.find_all('a', class_='grid-listing-link')

shipyards = set()
for link in links:
    ssr_meta = link.get('data-ssr-meta', '')
    if ssr_meta:
        shipyard = ssr_meta.split("|")[0].strip()
        shipyards.add(shipyard)

for s in sorted(list(shipyards)):
    print(s)
