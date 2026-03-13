import pandas as pd
import csv
import os
from collections import Counter
import re
from google.cloud import bigquery

TRACKER_FILE = 'broker_tracker.csv'
CAMPAIGN_FILE = 'campaign_ready.csv'

def is_junk_broker(name):
    if not name or not isinstance(name, str): return True
    name = name.strip()
    if re.match(r'^[€$£]?\s*[\d\.,]+$', name): return True
    if len(name) < 4: return True
    if name.lower() in ('private', 'venditore privato', 'private seller', 
                        'band of boats', 'privat', 'privé', 'particulier'): return True
    return False

def normalize_broker_name(name):
    if not isinstance(name, str): return ""
    name = name.lower().strip()
    # Rimuoviamo suffissi legali comuni
    name = re.sub(r'\b(srl|s\.r\.l\.|spa|s\.p\.a\.|inc|inc\.|llc|l\.l\.c\.|ltd|ltd\.|sa|s\.a\.|gmbh|sl|s\.l\.)\b', '', name)
    name = re.sub(r'[^\w\s]', '', name) # rimuove punteggiatura
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def get_canonical_mapping(df):
    """
    Raggruppa broker con nomi simili. 
    Es. "Timone Yachts" e "Timone Yachts Genova" vengono mappati allo stesso broker (quello col nome più frequente o più corto).
    """
    broker_counts = df['broker'].dropna().value_counts()
    unique_brokers = broker_counts.index.tolist()
    
    normalized_to_original = {}
    broker_mapping = {}
    
    for broker in unique_brokers:
        if is_junk_broker(broker):
            broker_mapping[broker] = None
            continue
            
        norm = normalize_broker_name(broker)
        if len(norm) < 4:
            broker_mapping[broker] = None
            continue
            
        found_group = False
        for existing_norm, canonical_orig in list(normalized_to_original.items()):
            # Se sono identici dopo la normalizzazione
            if norm == existing_norm:
                broker_mapping[broker] = canonical_orig
                found_group = True
                break
            
            # Se uno è prefisso dell'altro (es: "timone yachts" in "timone yachts genova")
            # Richiediamo almeno 6 caratteri di base per evitare falsi positivi con parole corte
            if len(existing_norm) >= 6 and norm.startswith(existing_norm + ' '):
                broker_mapping[broker] = canonical_orig
                found_group = True
                break
            if len(norm) >= 6 and existing_norm.startswith(norm + ' '):
                # In questo caso il nuovo nome è più generico (es "timone yachts" trovato dopo "timone yachts genova")
                # Aggiorniamo il mapping al nome più generico
                broker_mapping[broker] = broker
                # E aggiorniamo il canonical anche per quello vecchio
                normalized_to_original[norm] = broker
                del normalized_to_original[existing_norm]
                # Ri-mappiamo tutti quelli che puntavano al vecchio canonical
                for k, v in broker_mapping.items():
                    if v == canonical_orig:
                        broker_mapping[k] = broker
                found_group = True
                break
                
        if not found_group:
            normalized_to_original[norm] = broker
            broker_mapping[broker] = broker
            
    return broker_mapping

def format_currency(value):
    if pd.isna(value) or value == 0:
        return "N/A"
    if value >= 1_000_000:
        return f"€{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"€{value/1_000:.0f}k"
    else:
        return f"€{value:.0f}"

def generate_email_it(broker_name, stats):
    top_models_str = ", ".join(stats['top_models'][:3])
    subject = f"Analisi portafoglio barche per {broker_name}"
    
    body = f"""Gentile team di {broker_name},

Vi contatto perché abbiamo analizzato il vostro portafoglio di imbarcazioni online (aggregando i dati da vari portali) e siamo rimasti impressionati. Abbiamo rilevato circa {stats['listings_count']} vostri annunci attivi.

Dal nostro motore di Batoo Analytics emerge che gestite un portafoglio stimato di oltre {format_currency(stats['total_value'])}, con un prezzo medio di {format_currency(stats['avg_price'])} per imbarcazione.
Tra i vostri modelli di punta spiccano: {top_models_str}.

Abbiamo sviluppato Nautica Price Engine (Batoo Analytics), un software basato sull'Intelligenza Artificiale che monitora costantemente il mercato nautico europeo. 
Il nostro strumento vi permette di:
1. Valutare istantaneamente il corretto prezzo di mercato (e la svalutazione) di qualsiasi modello prima di prenderlo in mandato.
2. Monitorare la liquidità di mercato e il tempo medio di vendita dei vostri top brand.
3. Scoprire le variazioni di prezzo dei vostri competitor in tempo reale.

Sareste aperti a fare una veloce demo di 10 minuti la prossima settimana per mostrarvi come questo tool può farvi acquisire mandati al giusto prezzo e chiudere vendite più velocemente?

Un cordiale saluto,
Giorgio
Team Batoo Analytics
"""
    return subject, body

def generate_email_en(broker_name, stats):
    top_models_str = ", ".join(stats['top_models'][:3])
    subject = f"Yacht portfolio analysis for {broker_name}"
    
    body = f"""Hi {broker_name} team,

I'm reaching out because we analyzed your online yacht portfolio and were very impressed. We've tracked around {stats['listings_count']} active listings from your brokerage across multiple portals.

According to our Batoo Analytics engine, you manage an estimated portfolio of over {format_currency(stats['total_value'])}, with an average listing price of {format_currency(stats['avg_price'])}.
Among your top models, we noticed: {top_models_str}.

We have developed the Nautica Price Engine (Batoo Analytics), an AI-driven software that constantly monitors the European yachting market. 
Our tool allows you to:
1. Instantly evaluate the correct market price (and depreciation) of any model before signing a mandate.
2. Monitor market liquidity and average selling times for your top brands.
3. Track your competitors' price changes in real time.

Would you be open to a quick 10-minute demo next week to see how this tool can help you secure mandates at the right price and close sales faster?

Best regards,
Giorgio
Batoo Analytics Team
"""
    return subject, body

def main():
    print("1. Connessione a BigQuery e caricamento DB imbarcazioni...")
    try:
        client = bigquery.Client(project="vast-ascent-457111-r0")
        query = "SELECT * FROM `vast-ascent-457111-r0.batoo_analytics.boats_staging`"
        df = client.query(query).to_dataframe()
        print(f"   Caricate {len(df)} imbarcazioni da BigQuery.")
    except Exception as e:
        print(f"Errore caricamento DB BigQuery: {e}")
        return

    print("2. Mapping e aggregazione Broker (risoluzione duplicati)...")
    broker_mapping = get_canonical_mapping(df)
    
    brokers_data = {}
    
    for _, row in df.iterrows():
        raw_broker = row.get('broker')
        if pd.isna(raw_broker): continue
        
        canonical_broker = broker_mapping.get(raw_broker)
        if not canonical_broker:
            continue
            
        if canonical_broker not in brokers_data:
            brokers_data[canonical_broker] = {
                'listings_count': 0,
                'prices': [],
                'models': [],
                'countries': [],
                'sources': set()
            }
            
        bd = brokers_data[canonical_broker]
        bd['listings_count'] += 1
        
        price = row.get('price_eur')
        if pd.notna(price) and price > 0:
            bd['prices'].append(price)
            
        builder = row.get('builder')
        model = row.get('model')
        if pd.notna(builder) and pd.notna(model):
            bd['models'].append(f"{builder} {model}")
            
        country = row.get('country')
        if pd.notna(country):
            bd['countries'].append(str(country).lower())
            
        source = row.get('source')
        if pd.notna(source):
            bd['sources'].add(source)

    records = []
    for broker, bd in brokers_data.items():
        if bd['listings_count'] < 5:
            continue
            
        total_value = sum(bd['prices'])
        avg_price = total_value / len(bd['prices']) if bd['prices'] else 0
        
        top_models = [m for m, c in Counter(bd['models']).most_common(3)]
        if not top_models: top_models = ["Generici"]
        
        main_country = Counter(bd['countries']).most_common(1)[0][0] if bd['countries'] else "unknown"
        lang = 'it' if main_country in ['italia', 'italy', 'san marino', 'svizzera', 'ch'] else 'en'
        
        records.append({
            'broker_name': broker,
            'listings_count': bd['listings_count'],
            'total_value': total_value,
            'avg_price': avg_price,
            'top_models': "|".join(top_models),
            'main_country': main_country,
            'portals': "|".join(bd['sources']),
            'language': lang,
            'website': '',
            'email': '',
            'status': 'TODO',
            'last_contact_date': ''
        })
        
    df_new = pd.DataFrame(records)
    print(f"   Trovati {len(df_new)} broker unici dopo la pulizia e raggruppamento.")
    
    print("3. Sincronizzazione con il Tracker esistente...")
    if os.path.exists(TRACKER_FILE):
        df_old = pd.read_csv(TRACKER_FILE)
        df_old = df_old.set_index('broker_name')
        df_new = df_new.set_index('broker_name')
        
        for col in ['website', 'email', 'status', 'last_contact_date']:
            if col in df_old.columns:
                df_new[col] = df_old[col]
                
        df_new = df_new.reset_index()
        df_new = df_new.fillna({
            'website': '', 'email': '', 'status': 'TODO', 'last_contact_date': ''
        })
    else:
        print("   Tracker non trovato, ne creo uno nuovo.")
        
    df_new = df_new.sort_values(by='total_value', ascending=False)
    
    # Integrazione vecchie email estratte
    if os.path.exists('topboats_brokers_emails.csv'):
        topboats_emails = pd.read_csv('topboats_brokers_emails.csv')
        email_dict = dict(zip(topboats_emails['broker'], topboats_emails['emails']))
        website_dict = dict(zip(topboats_emails['broker'], topboats_emails['website']))
        
        for idx, row in df_new.iterrows():
            # Il nome nel DB BQ potrebbe essere diverso (canonicalizzato), 
            # proviamo a fare il match per ritrovare l'email usando lo stesso canonical mapping.
            # Convertiamo i nomi di topboats in canonical e salviamo le loro mail
            pass
            
        # Refined Email matching
        canonical_emails = {}
        canonical_websites = {}
        for _, tb_row in topboats_emails.iterrows():
            tb_broker = tb_row['broker']
            canon_tb = broker_mapping.get(tb_broker)
            if canon_tb:
                if pd.notna(tb_row['emails']) and str(tb_row['emails']).strip():
                    canonical_emails[canon_tb] = str(tb_row['emails']).split(',')[0].strip()
                if pd.notna(tb_row['website']) and str(tb_row['website']).strip():
                    canonical_websites[canon_tb] = str(tb_row['website']).strip()

        for idx, row in df_new.iterrows():
            broker = row['broker_name']
            if not row['email'] and broker in canonical_emails:
                df_new.at[idx, 'email'] = canonical_emails[broker]
            if not row['website'] and broker in canonical_websites:
                df_new.at[idx, 'website'] = canonical_websites[broker]

    df_new.to_csv(TRACKER_FILE, index=False, quoting=csv.QUOTE_ALL)
    print(f"   Salvato master tracker in {TRACKER_FILE}")
    
    print("4. Generazione Email per la Campagna (solo broker con email e status TODO)...")
    campaign_list = []
    
    for _, row in df_new.iterrows():
        if row['email'] and str(row['email']).strip() != '' and row['status'] == 'TODO':
            stats = {
                'listings_count': row['listings_count'],
                'total_value': row['total_value'],
                'avg_price': row['avg_price'],
                'top_models': str(row['top_models']).split('|')
            }
            
            if row['language'] == 'it':
                subject, body = generate_email_it(row['broker_name'], stats)
            else:
                subject, body = generate_email_en(row['broker_name'], stats)
                
            campaign_list.append({
                'broker_name': row['broker_name'],
                'email': row['email'],
                'language': row['language'],
                'subject': subject,
                'body': body
            })
            
    df_camp = pd.DataFrame(campaign_list)
    df_camp.to_csv(CAMPAIGN_FILE, index=False, quoting=csv.QUOTE_ALL)
    print(f"   Salvate {len(df_camp)} email pronte da inviare in {CAMPAIGN_FILE}")
    print("\n--- Riepilogo Tracker ---")
    print(df_new['status'].value_counts())

if __name__ == "__main__":
    main()