import json
import pandas as pd
import re
from thefuzz import process
from thefuzz import fuzz
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def load_data():
    files = [
        "boat24_boats.json",
        "mondialbroker_boats.json",
        "yachtall_boats.json",
        "topboats_data.json"
    ]
    all_data = []
    for f in files:
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                all_data.extend(data)
            logging.info(f"Loaded {len(data)} records from {f}")
        except FileNotFoundError:
            logging.warning(f"File {f} not found. Skipping.")
    return pd.DataFrame(all_data)

def clean_builder_name(name):
    if not isinstance(name, str):
        return "Unknown"
    
    # Rimuovi suffissi commerciali e punteggiatura inutile
    name = name.lower()
    suffixes_to_remove = [
        r'\byachts\b', r'\byacht\b', r'\bboats\b', r'\bboat\b', 
        r'\bmarine\b', r'\bs\.p\.a\.?\b', r'\bspa\b', r'\bsrl\b', 
        r'\bs\.r\.l\.?\b', r'\bgroup\b', r'\binc\b', r'\bllc\b', r'\bltd\b',
        r'\bcantieri navali\b', r'\bcantiere navale\b', r'\bcantieri\b'
    ]
    for suffix in suffixes_to_remove:
        name = re.sub(suffix, '', name)
    
    # Rimuovi caratteri speciali
    name = re.sub(r'[^a-z0-9\s-]', ' ', name)
    # Rimuovi spazi extra
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name.title() if name else "Unknown"

def normalize_builders(df, similarity_threshold=85):
    logging.info("Starting builder normalization...")
    
    # 1. Pulizia base
    df['builder_clean'] = df['builder'].apply(clean_builder_name)
    
    # 2. Ottieni la lista dei cantieri unici puliti e la loro frequenza
    builder_counts = df['builder_clean'].value_counts()
    unique_builders = builder_counts.index.tolist()
    
    # 3. Clustering fuzzy: raggruppa nomi simili verso il nome più frequente
    # Creiamo un dizionario di mappatura: {nome_sporco: nome_canonico}
    mapping = {}
    
    # Iteriamo dal cantiere più frequente al meno frequente
    for builder in unique_builders:
        if builder in mapping or builder == "Unknown":
            continue
            
        # Cerca i match per il cantiere corrente tra quelli non ancora mappati
        # Cerchiamo solo nei cantieri meno frequenti di quello attuale
        unmapped_builders = [b for b in unique_builders if b not in mapping]
        
        matches = process.extract(builder, unmapped_builders, scorer=fuzz.token_sort_ratio, limit=None)
        
        for match_str, score in matches:
            if score >= similarity_threshold:
                # Mappa il match al cantiere più frequente (il nostro 'builder' corrente)
                mapping[match_str] = builder
                
    # 4. Applica la mappatura
    df['builder_canonical'] = df['builder_clean'].map(mapping).fillna(df['builder_clean'])
    
    logging.info(f"Reduced unique builders from {len(unique_builders)} to {len(set(mapping.values()))}")
    return df

def clean_and_unify_data():
    df = load_data()
    
    # Mappa i vecchi nomi delle colonne se presenti nei dati esistenti
    if 'make' in df.columns:
        df = df.rename(columns={'make': 'builder'})
    if 'search_country' in df.columns:
        df = df.rename(columns={'search_country': 'country'})
    if 'price' in df.columns and 'price_eur' not in df.columns:
        df = df.rename(columns={'price': 'price_eur'})
    if 'year' in df.columns and 'year_built' not in df.columns:
        df = df.rename(columns={'year': 'year_built'})
        
    # Filtra record senza cantiere o modello
    df = df.dropna(subset=['builder', 'model'])
    
    # Converti anno e filtra (teniamo solo barche ragionevoli, es. 1950 in poi)
    df['year_built'] = pd.to_numeric(df['year_built'], errors='coerce')
    df = df[(df['year_built'] > 1950) & (df['year_built'] <= 2026)]
    df['year_built'] = df['year_built'].astype(int)
    
    # Prezzo deve essere valido
    df['price_eur'] = pd.to_numeric(df['price_eur'], errors='coerce')
    df = df[df['price_eur'] > 1000] # Elimina prezzi finti come "1€"
    
    # Normalizza i cantieri
    df = normalize_builders(df)
    
    # Seleziona le colonne per l'output finale
    columns_to_keep = [
        'id', 'builder_canonical', 'model', 'year_built', 'country', 
        'price_eur', 'length', 'image_url', 'source', 'broker', 'url'
    ]
    df_final = df[columns_to_keep].rename(columns={'builder_canonical': 'builder'})
    
    # Salva il dataset master
    output_file = "master_boats_db.json"
    df_final.to_json(output_file, orient='records', indent=2)
    logging.info(f"Successfully saved {len(df_final)} cleaned records to {output_file}")
    
    # Stampa un piccolo riassunto
    print("\n--- TOP 10 Cantieri (Canonicalizzati) ---")
    print(df_final['builder'].value_counts().head(10))

if __name__ == "__main__":
    clean_and_unify_data()
