import asyncio
import json
import httpx
from boat24_scraper import Boat24Scraper
from mondialbroker_scraper import MondialBrokerScraper
from yachtall_scraper import YachtallScraper
from scraper import TopBoatsScraper

async def test_scrapers():
    results = {}
    
    print("Testing Boat24...")
    b24 = Boat24Scraper(max_concurrent=1)
    async with httpx.AsyncClient(proxy=b24.proxy, verify=False) as client:
        html = await b24.fetch_page(client, 0)
        items = b24.process_page_html(html)
        if items:
            results['boat24'] = items[0]
            print(f"Boat24 sample: {json.dumps(items[0], indent=2)}")

    print("\nTesting MondialBroker...")
    mb = MondialBrokerScraper(max_concurrent_details=1)
    async with httpx.AsyncClient() as client:
        html = await mb.fetch_page(client, 1)
        items = mb.process_page_html(html)
        if items:
            # Fetch detail for the first one
            item = await mb.fetch_detail(client, items[0])
            results['mondialbroker'] = item
            print(f"MondialBroker sample: {json.dumps(item, indent=2)}")

    print("\nTesting Yachtall...")
    ya = YachtallScraper(max_concurrent=1)
    async with httpx.AsyncClient(proxy=ya.proxy, verify=False, follow_redirects=True) as client:
        html = await ya.fetch_page(client, 2)
        items = ya.process_page_html(html)
        if items:
            results['yachtall'] = items[0]
            print(f"Yachtall sample: {json.dumps(items[0], indent=2)}")

    print("\nTesting TopBoats...")
    tb = TopBoatsScraper()
    # Scrape just 1 page of Italy
    items = tb.scrape_country("italia", max_pages=1)
    if items:
        results['topboats'] = items[0]
        print(f"TopBoats sample: {json.dumps(items[0], indent=2)}")

    with open("test_standard_output.json", "w") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    asyncio.run(test_scrapers())
