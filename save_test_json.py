from scraper import TopBoatsScraper
import json
import logging

# Configura il logging per vedere l'avanzamento
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    print("Inizio scraping di test (1 pagina, Italia)...")
    scraper = TopBoatsScraper(max_threads=1)
    
    # Eseguiamo lo scrape di una sola pagina per l'Italia
    results = scraper.scrape_country("italia", max_pages=1)
    
    if results:
        file_name = "test_scrape_output.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        
        print("\nSuccesso! Estratti {} elementi.".format(len(results)))
        print("I dati sono stati salvati in: {}".format(file_name))
        
        # Mostriamo un'anteprima dei primi 3 elementi per verifica immediata
        print("\nAnteprima primi 3 elementi:")
        for boat in results[:3]:
            print("- {} {} {} ({})".format(boat['anno'], boat['cantiere'], boat['modello'], boat['prezzo']))
    else:
        print("\nNessun dato raccolto. Controlla la connessione o i proxy.")
