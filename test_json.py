from scraper import TopBoatsScraper
import json
import logging

if __name__ == "__main__":
    logging.info("Estrazione di una singola pagina per Olanda...")
    scraper = TopBoatsScraper(max_threads=1)
    
    # Scrapiamo solo la prima pagina
    results = scraper.scrape_country("olanda", max_pages=1)
    
    if results:
        # Stampiamo i primi 5 risultati in formato JSON formattato
        json_output = json.dumps(results[:5], indent=4, ensure_ascii=False)
        print("\n--- RISULTATO JSON (Primi 5 elementi) ---")
        print(json_output)
        print(f"\nTotale elementi estratti: {len(results)}")
    else:
        print("Nessun risultato trovato.")
