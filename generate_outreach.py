import pandas as pd
import json
import csv

def generate_email(broker_name, stats):
    total_listings = stats['total_listings']
    total_value = stats['total_value']
    avg_price = stats['avg_price']
    
    # Format currency
    def format_currency(value):
        if value >= 1_000_000:
            return f"€{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"€{value/1_000:.0f}k"
        else:
            return f"€{value:.0f}"

    top_models_str = ", ".join([f"{m['name']}" for m in stats['top_models'][:3]])
    
    subject = f"Analisi portafoglio barche per {broker_name}"
    
    body = f"""Gentile team di {broker_name},

Vi contatto perché ho analizzato il vostro portafoglio di imbarcazioni online (in particolare su TopBoats) e sono rimasto impressionato. Abbiamo rilevato circa {total_listings} vostri annunci attivi.

Dal nostro motore di Batoo Analytics emerge che gestite un portafoglio stimato di oltre {format_currency(total_value)}, con un prezzo medio di {format_currency(avg_price)} per imbarcazione.
Tra i vostri modelli di punta spiccano: {top_models_str}.

Abbiamo sviluppato Nautica Price Engine (Batoo Analytics), un software basato sull'Intelligenza Artificiale che monitora costantemente il mercato nautico europeo. 
Il nostro strumento vi permette di:
1. Valutare istantaneamente il corretto prezzo di mercato (e la svalutazione) di qualsiasi modello prima di prenderlo in mandato.
2. Monitorare la liquidità di mercato e il tempo medio di vendita dei vostri top brand.
3. Scoprire le variazioni di prezzo dei vostri competitor in tempo reale.

Volevo chiedervi se sareste aperti a fare una veloce demo di 10 minuti la prossima settimana per mostrarvi come questo tool può farvi acquisire mandati al giusto prezzo e chiudere vendite più velocemente.

Fatemi sapere se siete interessati.

Un cordiale saluto,
[Tuo Nome]
Team Batoo Analytics
"""
    return subject, body

def main():
    print("Caricamento database imbarcazioni...")
    try:
        with open('master_boats_db.json', 'r') as f:
            db_data = json.load(f)
        df_boats = pd.DataFrame(db_data)
    except Exception as e:
        print(f"Errore caricamento DB: {e}")
        return

    print("Caricamento email broker...")
    brokers_df = pd.read_csv('topboats_brokers_emails.csv')
    
    # Filtriamo solo quelli con email
    brokers_with_email = brokers_df[brokers_df['emails'].notna() & (brokers_df['emails'] != '')].copy()
    print(f"Trovati {len(brokers_with_email)} broker con email valida.")

    outreach_data = []

    for _, row in brokers_with_email.iterrows():
        broker_name = row['broker']
        emails = row['emails']
        
        # Troviamo le barche di questo broker
        # Facciamo un match esatto per semplicità, ma potremmo usare lower() e contains
        broker_boats = df_boats[df_boats['broker'] == broker_name]
        
        if broker_boats.empty:
            continue
            
        prices = broker_boats['price_eur'].dropna()
        if prices.empty:
            continue
            
        total_listings = len(broker_boats)
        total_value = prices.sum()
        avg_price = prices.mean()
        
        # Top modelli
        top_models = (
            broker_boats.groupby(['builder', 'model']).size()
            .sort_values(ascending=False).head(3)
        )
        top_models_list = [
            {"name": f"{b} {m}", "count": int(c)}
            for (b, m), c in top_models.items()
        ]
        
        stats = {
            'total_listings': total_listings,
            'total_value': total_value,
            'avg_price': avg_price,
            'top_models': top_models_list
        }
        
        subject, body = generate_email(broker_name, stats)
        
        outreach_data.append({
            'broker': broker_name,
            'emails': emails,
            'subject': subject,
            'body': body,
            'total_listings': total_listings,
            'total_value': total_value
        })

    # Ordiniamo per valore totale del portafoglio decrescente (colpiamo prima i pesci grossi)
    outreach_data.sort(key=lambda x: x['total_value'], reverse=True)
    
    out_file = 'outreach_campaign_emails.csv'
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['broker', 'emails', 'subject', 'body', 'total_listings', 'total_value'])
        writer.writeheader()
        writer.writerows(outreach_data)

    print(f"\nGenerato file della campagna: {out_file}")
    
    # Stampiamo un esempio
    if outreach_data:
        print("\n--- ESEMPIO DI EMAIL (TOP BROKER) ---")
        print(f"Destinatario: {outreach_data[0]['emails']}")
        print(f"Oggetto: {outreach_data[0]['subject']}\n")
        print(outreach_data[0]['body'])
        print("-------------------------------------\n")

if __name__ == "__main__":
    main()