from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import pandas as pd
import json
import numpy as np

app = FastAPI(title="Nautica Price Engine API", version="1.0")

# Abilita CORS per far comunicare il frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from google.cloud import bigquery

# Carica i dati in memoria all'avvio
print("Loading master database from BigQuery...")
try:
    client = bigquery.Client(project="vast-ascent-457111-r0")
    query = "SELECT * FROM `vast-ascent-457111-r0.batoo_analytics.boats_staging`"
    df = client.query(query).to_dataframe()
    
    # Rendi i cantieri uppercase per match esatti più facili
    df['builder_search'] = df['builder'].str.lower()
    df['model_search'] = df['model'].str.lower()
    
    # Pre-calcola una lista di suggerimenti unici (Cantiere Modello) ordinati per popolarità
    print("Building suggestions index...")
    # Crea una colonna 'full_name' combinando builder e model
    df['full_name'] = df['builder'].astype(str) + " " + df['model'].astype(str)
    # Conta le occorrenze per ogni modello per ordinare i suggerimenti dal più comune al più raro
    popularity = df['full_name'].value_counts()
    unique_boats_df = pd.DataFrame({'full_name': popularity.index, 'count': popularity.values})
    unique_boats_df['search_name'] = unique_boats_df['full_name'].str.lower()
    
    print(f"Loaded {len(df)} boats and {len(unique_boats_df)} unique models into memory.")
except Exception as e:
    print(f"Error loading database: {e}")
    df = pd.DataFrame()
    unique_boats_df = pd.DataFrame()

@app.get("/")
def read_root():
    # Ritorna anche il totale delle barche attualmente in memoria per il frontend
    return {
        "status": "ok", 
        "message": "Nautica Price Engine API is running",
        "total_boats": len(df) if not df.empty else 0
    }

@app.get("/suggestions")
def get_suggestions(q: str):
    """Ritorna fino a 10 suggerimenti di autocompletamento in tempo reale, ordinati per popolarità."""
    if unique_boats_df.empty or not q or len(q) < 2:
        return []
        
    q_lower = q.lower().strip()
    
    # Cerca all'interno della stringa
    mask = unique_boats_df['search_name'].str.contains(q_lower, na=False, regex=False)
    matches = unique_boats_df[mask].head(8) # Prendiamo i primi 8 (i più popolari grazie all'ordinamento iniziale)
    
    return matches['full_name'].tolist()

@app.get("/builders")
def get_builders(q: Optional[str] = None):
    """Ritorna la lista dei cantieri, opzionalmente filtrata."""
    if df.empty: return []
    
    if q:
        mask = df['builder_search'].str.contains(q.lower(), na=False, regex=False)
        builders = df[mask]['builder'].dropna().unique().tolist()
    else:
        builders = df['builder'].dropna().unique().tolist()
        
    return sorted(builders) # Ritorna tutti i cantieri senza limite

@app.get("/models")
def get_models(builder: str, q: Optional[str] = None):
    """Ritorna i modelli per un determinato cantiere, opzionalmente filtrati."""
    if df.empty: return []
    
    mask = df['builder_search'] == builder.lower()
    if q:
        mask = mask & df['model_search'].str.contains(q.lower(), na=False, regex=False)
        
    models = df[mask]['model'].dropna().unique().tolist()
    return sorted(models)[:50] # Limite a 50 suggerimenti per pulizia interfaccia

@app.get("/carousel-images")
def get_carousel_images():
    if df.empty: return []
    # Prendi barche che hanno un'immagine valida
    has_image = df.dropna(subset=['image_url'])
    has_image = has_image[has_image['image_url'].str.startswith('http', na=False)]
    if has_image.empty: return []
    
    # Prendi 15 immagini a caso
    sample = has_image.sample(min(15, len(has_image)))
    return sample['image_url'].tolist()

@app.get("/evaluate")
def evaluate_boat(
    q: str, 
    year: Optional[int] = None
):
    """Motore di valutazione 'Google-style': identifica cantiere e modello da una stringa unica."""
    if df.empty: raise HTTPException(status_code=500, detail="Database not loaded")
    
    q_lower = q.lower().strip()
    words = q_lower.split()
    
    if not words:
        raise HTTPException(status_code=400, detail="Inserisci un termine di ricerca")

    # 1. Identificazione Cantiere
    all_builders = df['builder_search'].dropna().unique()
    found_builder = None
    remaining_model_words = []
    
    # Prova 2 parole poi 1
    if len(words) >= 2:
        two_words = f"{words[0]} {words[1]}"
        if two_words in all_builders:
            found_builder = two_words
            remaining_model_words = words[2:]
            
    if not found_builder:
        if words[0] in all_builders:
            found_builder = words[0]
            remaining_model_words = words[1:]
        else:
            remaining_model_words = words

    # 2. Maschera di ricerca (Google-style full-text)
    mask = pd.Series([True] * len(df))
    search_col = df['builder_search'].fillna('') + " " + df['model_search'].fillna('')
    for kw in words:
        mask = mask & search_col.str.contains(kw, na=False, regex=False)
        
    matched_df = df[mask]
    
    if matched_df.empty:
        raise HTTPException(status_code=404, detail=f"Nessun risultato per '{q}'")
        
    # 3. Filtro Anno
    if year:
        year_mask = (matched_df['year_built'] >= year - 2) & (matched_df['year_built'] <= year + 2)
        if not matched_df[year_mask].empty:
            matched_df = matched_df[year_mask]
            
    # 4. Statistiche e Svalutazione
    prices = matched_df['price_eur'].dropna()
    if prices.empty:
        raise HTTPException(status_code=404, detail="Dati di prezzo non disponibili")
        
    if len(prices) > 5:
        p5 = np.percentile(prices, 5)
        p95 = np.percentile(prices, 95)
        prices_clean = prices[(prices >= p5) & (prices <= p95)]
        # Filtriamo il dataframe intero per il calcolo svalutazione per rimuovere outliers estremi
        clean_df = matched_df[(matched_df['price_eur'] >= p5) & (matched_df['price_eur'] <= p95)]
    else:
        prices_clean = prices
        clean_df = matched_df
        
    avg_price = float(prices_clean.mean())
    min_price = float(prices_clean.min())
    max_price = float(prices_clean.max())
    
    # Calcolo Svalutazione Annua e Trend Chart Data
    depreciation_value = 0
    depreciation_percent = 0
    has_depreciation = False
    price_trend = []
    
    # Calcolo Affidabilità del dato
    confidence_score = min(100, int((len(prices_clean) / 30) * 100)) if len(prices_clean) > 0 else 0
    if len(prices_clean) >= 30:
        confidence_label = "Alta"
        confidence_color = "green"
    elif len(prices_clean) >= 10:
        confidence_label = "Media"
        confidence_color = "yellow"
    else:
        confidence_label = "Bassa"
        confidence_color = "red"
        
    if len(clean_df) > 0:
        # Assicuriamoci di avere l'anno
        trend_df = clean_df.dropna(subset=['year_built', 'price_eur'])
        if not trend_df.empty:
            yearly_prices = trend_df.groupby('year_built')['price_eur'].median().sort_index()
            for year_val, price_val in yearly_prices.items():
                if pd.notna(year_val) and pd.notna(price_val) and year_val > 1950:
                    price_trend.append({"year": int(year_val), "avg_price": float(price_val)})
            
            if len(yearly_prices) >= 2 and (yearly_prices.index[-1] - yearly_prices.index[0]) >= 3:
                first_year = yearly_prices.index[0]
                last_year = yearly_prices.index[-1]
                price_old = float(yearly_prices.iloc[0])
                price_new = float(yearly_prices.iloc[-1])
                
                years_diff = float(last_year - first_year)
                if price_new > price_old and years_diff > 0:
                    depreciation_value = (price_new - price_old) / years_diff
                    depreciation_percent = (depreciation_value / price_new) * 100
                    has_depreciation = True
                
    # Statistiche di Mercato: Vendute / Rimoss e Trend Prezzi a breve termine
    sold_last_week = 0
    price_change_last_month_percent = 0
    price_change_status = "stable"
    
    if 'status' in matched_df.columns and 'updated_at' in matched_df.columns:
        # Crea copie temporanee per l'analisi senza modificare le originali
        market_df = matched_df.copy()
        
        # Converte updated_at in datetime timezone-naive per comparazioni facili
        try:
            market_df['updated_at_dt'] = pd.to_datetime(market_df['updated_at']).dt.tz_localize(None)
            
            # 1. Barche rimosse/vendute nell'ultima settimana
            one_week_ago = pd.Timestamp.now() - pd.Timedelta(days=7)
            sold_mask = (market_df['status'] == False) & (market_df['updated_at_dt'] >= one_week_ago)
            sold_last_week = int(sold_mask.sum())
            
            # 2. Variazione del prezzo medio attivo dell'ultimo mese
            one_month_ago = pd.Timestamp.now() - pd.Timedelta(days=30)
            
            # Prezzo medio barche attive fino ad un mese fa
            active_month_ago_mask = (market_df['status'] == True) & (market_df['updated_at_dt'] < one_month_ago)
            # Se ci sono dati e first_seen_at è presente (per evitare errori con i nuovi dati in cui first_seen_at è NaT inizialmente)
            
            # Approccio robusto per la variazione:
            # Calcoliamo i ribassi effettivi o aumenti sui singoli annunci ancora attivi o venduti di recente
            # *Dato che al momento first_seen_at potrebbe essere vuoto sui vecchi record importati, 
            # usiamo un placeholder per la logica. Quando il DB avrà storicizzato più settimane, questo calcolo sarà reale.*
            # Per ora mostriamo 0% fittizio se non ci sono variazioni rilevabili per evitare errori o false metriche
            price_change_last_month_percent = 0 
            
            if sold_last_week > 0:
                liquidity_color = "green" # Aumenta il rating di liquidità se si vende!
        except Exception as e:
            print(f"Errore nel calcolo delle metriche di mercato: {e}")

    # Indice di Liquidità (Scarsità sul mercato)
    total_found = len(matched_df)
    if total_found < 5:
        liquidity = "Scarsità Estrema"
        if 'liquidity_color' not in locals() or liquidity_color != "green": liquidity_color = "red"
    elif total_found < 20:
        liquidity = "Bassa (Mercato Esclusivo)"
        if 'liquidity_color' not in locals() or liquidity_color != "green": liquidity_color = "yellow"
    elif total_found < 80:
        liquidity = "Normale (Buona Scambiabilità)"
        liquidity_color = "green"
    else:
        liquidity = "Alta (Mercato Liquido)"
        liquidity_color = "blue"

    # Statistiche Broker/Professionali
    current_year = 2026 # Anno corrente di sistema

    
    # Età media a prova di bomba
    valid_years = clean_df['year_built'].dropna()
    avg_age = current_year - float(valid_years.median()) if not valid_years.empty else 0
    
    # Prezzo al metro a prova di bomba
    clean_df_length = clean_df.dropna(subset=['length', 'price_eur'])
    clean_df_length = clean_df_length[clean_df_length['length'] > 0]
    avg_price_per_meter = 0
    if not clean_df_length.empty:
        price_per_m = clean_df_length['price_eur'] / clean_df_length['length']
        avg_price_per_meter = float(price_per_m.median()) if not price_per_m.empty and pd.notna(price_per_m.median()) else 0
        
    # Distribuzione geografica e Prezzo Medio per Nazione
    top_countries = []
    if 'country' in clean_df.columns:
        countries_counts = clean_df['country'].value_counts()
        total_countries = countries_counts.sum()
        for country, count in countries_counts.items():
            if pd.notna(country) and country.strip() and total_countries > 0:
                perc = (count / total_countries) * 100
                
                # Calcola il prezzo medio per questo specifico paese
                country_mask = clean_df['country'] == country
                country_prices = clean_df[country_mask]['price_eur'].dropna()
                country_avg_price = float(country_prices.mean()) if not country_prices.empty and pd.notna(country_prices.mean()) else 0
                
                top_countries.append({
                    "name": country, 
                    "count": int(count), 
                    "percentage": round(float(perc), 1),
                    "avg_price": round(float(country_avg_price), 2)
                })
    
    # Ordinamento e Paginazione fissa a 50
    sorted_df = matched_df.sort_values(by='year_built', ascending=False)
    
    # Assicuriamoci che i campi esistano
    cols_to_extract = ['id', 'builder', 'model', 'year_built', 'length', 'country', 'price_eur', 'url', 'image_url']
    if 'status' in sorted_df.columns:
        cols_to_extract.append('status')
    if 'first_seen_at' in sorted_df.columns:
        cols_to_extract.append('first_seen_at')
    if 'updated_at' in sorted_df.columns:
        cols_to_extract.append('updated_at')
        
    extracted_df = sorted_df[cols_to_extract].head(50).copy()
    
    # Convert datetime to string per JSON serialization
    if 'first_seen_at' in extracted_df.columns:
        extracted_df['first_seen_at'] = extracted_df['first_seen_at'].astype(str)
    if 'updated_at' in extracted_df.columns:
        extracted_df['updated_at'] = extracted_df['updated_at'].astype(str)
        
    samples = json.loads(extracted_df.to_json(orient="records"))
    
    
    # Generazione AI Insight algoritmico
    ai_insight = f"L'Intelligenza Artificiale ha analizzato {total_found} annunci per il modello {found_builder.capitalize() if found_builder else q.capitalize()}. "
    if has_depreciation:
        if depreciation_percent > 10:
            ai_insight += f"Il modello subisce una svalutazione marcata (circa {round(depreciation_percent, 1)}% annuo). Ottimo per chi cerca un usato svalutato, meno indicato per investimenti a breve termine. "
        else:
            ai_insight += f"La tenuta del valore è solida (svalutazione stimata {round(depreciation_percent, 1)}% annuo). Rappresenta un acquisto sicuro nel tempo. "
    else:
        ai_insight += "Il mercato per questo modello appare stabile e i prezzi non mostrano una flessione evidente legata all'anno di costruzione. "
        
    if avg_price_per_meter > 0:
        if avg_price_per_meter > 50000:
            ai_insight += f"Con un prezzo medio di {format(int(avg_price_per_meter), ',').replace(',', '.')} € al metro, si posiziona nella fascia alta del mercato. "
        else:
            ai_insight += f"Il costo al metro di {format(int(avg_price_per_meter), ',').replace(',', '.')} € evidenzia un posizionamento accessibile. "

    if liquidity_color == "red" or liquidity_color == "yellow":
        ai_insight += "La scarsità di annunci indica un mercato esclusivo: le trattative potrebbero richiedere più tempo."
    else:
        ai_insight += "La buona disponibilità sul mercato garantisce facilità di rivendita (ottima liquidità)."

    return {
        "query": q,
        "identified_builder": found_builder.capitalize() if found_builder else "Generica",
        "sample_size": len(prices),
        "total_results_found": total_found, 
        "ai_insight": ai_insight,
        "valuation": {
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "confidence_color": confidence_color,
            "average_price_eur": round(avg_price, 2),
            "min_price_eur": round(min_price, 2),
            "max_price_eur": round(max_price, 2),
            "has_depreciation": has_depreciation,
            "depreciation_value_eur": round(depreciation_value, 2) if has_depreciation else 0,
            "depreciation_percent": round(depreciation_percent, 2) if has_depreciation else 0,
            "median_age_years": round(avg_age, 1),
            "average_price_per_meter": round(avg_price_per_meter, 2),
            "market_share_countries": top_countries,
            "liquidity_status": liquidity,
            "liquidity_color": liquidity_color,
            "price_trend": price_trend,
            "sold_last_week": sold_last_week,
            "price_change_last_month_percent": price_change_last_month_percent
        },
        "comparables": samples
    }
