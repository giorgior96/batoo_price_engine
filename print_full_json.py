from scraper import TopBoatsScraper
import json
import logging
import sys

# Disabilita il logging per avere un output pulito del JSON
logging.getLogger().setLevel(logging.ERROR)

if __name__ == "__main__":
    scraper = TopBoatsScraper(max_threads=1)
    results = scraper.scrape_country("olanda", max_pages=1)
    
    if results:
        # Stampiamo l'intero array JSON
        print(json.dumps(results, indent=4, ensure_ascii=False))
    else:
        print("[]")
