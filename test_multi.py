from scraper import TopBoatsScraper
import logging
import pandas as pd
import config

if __name__ == "__main__":
    # Test multi-thread su 3 paesi
    test_countries = ["olanda", "francia", "italia"]
    logging.info(f"Avvio test multi-thread su: {test_countries}")
    
    # Sovrascriviamo temporaneamente la lista dei paesi nel config per il test
    config.COUNTRIES = test_countries
    
    scraper = TopBoatsScraper(max_threads=3)
    scraper.run()
    
    # Verifica risultati
    try:
        df = pd.read_csv("topboats_data.csv")
        print(f"\nTest completato con successo! Totale: {len(df)}")
        print("\nDistribuzione per paese:")
        print(df['paese_ricerca'].value_counts())
    except Exception as e:
        print(f"Errore nella lettura del file finale: {e}")
