from scraper import TopBoatsScraper
import json
import logging

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.ERROR)
    scraper = TopBoatsScraper(max_threads=1)
    results = scraper.scrape_country("olanda", max_pages=1)
    
    if results:
        file_path = "topboats_preview.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"File salvato correttamente in: {file_path}")
        print(f"Numero di barche salvate: {len(results)}")
    else:
        print("Errore: Nessun dato estratto.")
