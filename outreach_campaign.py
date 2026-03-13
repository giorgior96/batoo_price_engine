import json
import requests
import time
import re

API_URL = "http://localhost:8000/evaluate"
DATA_FILE = "broker_outreach_list.json"

def generate_email_body(broker_name, broker_email, builder, model, year, price, depreciation_percent, liquidity_status, best_country_name, best_country_price):
    
    price_formatted = f"€ {price:,.0f}".replace(",", ".")
    best_price_formatted = f"€ {best_country_price:,.0f}".replace(",", ".")
    
    # Rimuoviamo il ".0" fastidioso e puliamo il testo
    if isinstance(year, float):
        year = int(year)
        
    builder_clean = str(builder).title().strip()
    model_clean = str(model).title().strip()
    
    subject = f"Analisi di mercato per il tuo {builder_clean} {model_clean}"
    
    body = f"""Oggetto: {subject}
A: {broker_email} ({broker_name})

Ciao {broker_name},

Ho visto che avete in vendita un {builder_clean} {model_clean} del {year} a {price_formatted}.

Ho passato il tuo annuncio nel nostro nuovo algoritmo (Batoo Price Engine) che scansiona in tempo reale oltre 95.000 annunci tra Boat24, MondialBroker, Yachtall e iNautia in tutta Europa.

Sono emersi un paio di dati interessanti sul tuo modello:
- Svalutazione: Questo modello perde mediamente il {depreciation_percent}% del suo valore ogni anno.
- Liquidita': E' un mercato classificato come "{liquidity_status}".
"""
    
    if best_country_name and best_country_price > 0:
        body += f"- Arbitraggio: Sapevi che in {best_country_name} questo stesso modello viene venduto a un prezzo medio di {best_price_formatted}?\n"
        
    body += """
Abbiamo costruito Batoo per aiutare i broker a fare le valutazioni corrette da presentare agli armatori, giustificare i ribassi di prezzo basandosi su dati matematici (non opinioni) e chiudere le vendite piu' in fretta.

Come procediamo?
Se ti interessa, rispondi semplicemente "Si" a questa email (o scrivimi su WhatsApp al +39 3XX XXX XXXX) e ti mando gratis il report in PDF con l'analisi completa dei competitor per questa barca.

A presto,
Giorgio - Batoo
"""
    return body

def main():
    print("Caricamento lista contatti Navisnet...")
    with open(DATA_FILE, 'r') as f:
        brokers = json.load(f)
        
    print(f"Trovati {len(brokers)} broker.")
    
    for broker_name, data in brokers.items():
        email = data['email']
        builder = data['target_builder']
        model = data['target_model']
        price = data['target_price']
        year = data['target_year']
        
        query_str = f"{builder} {model}"
        
        # Interroghiamo l'API Batoo
        try:
            res = requests.get(f"{API_URL}?q={requests.utils.quote(query_str)}")
            if res.status_code == 200:
                api_data = res.json()
                val = api_data.get('valuation', {})
                
                # Formattiamo i dati
                depreciation_percent = round(val.get('depreciation_percent', 0), 1)
                liquidity_status = val.get('liquidity_status', 'Normale')
                
                countries = val.get('market_share_countries', [])
                best_country_name = None
                best_country_price = 0
                if countries:
                    best_country = sorted(countries, key=lambda x: x.get('avg_price', 0), reverse=True)[0]
                    best_country_name = best_country['name']
                    best_country_price = best_country['avg_price']
                
                email_text = generate_email_body(
                    broker_name=broker_name,
                    broker_email=email,
                    builder=builder,
                    model=model,
                    year=year,
                    price=price,
                    depreciation_percent=depreciation_percent,
                    liquidity_status=liquidity_status,
                    best_country_name=best_country_name,
                    best_country_price=best_country_price
                )
                
                print(email_text)
                print("="*60 + "\n")
                
            # Piccola pausa per non uccidere il server locale
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Errore su {broker_name}: {e}")

if __name__ == "__main__":
    main()
