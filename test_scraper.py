from scraper import TopBoatsScraper
import logging

if __name__ == "__main__":
    # Test for Olanda only
    logging.info("Testing scraper for Olanda...")
    scraper = TopBoatsScraper(max_threads=1)
    results = scraper.scrape_country("olanda")
    
    if results:
        print(f"Success! Found {len(results)} boats in Olanda (Page 1).")
        for i, boat in enumerate(results[:3]):
            print(f"\nBoat {i+1}:")
            for key, val in boat.items():
                print(f"  {key}: {val}")
    else:
        print("No results found. Check logs or Zyte API key.")
