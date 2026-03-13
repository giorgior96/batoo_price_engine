from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import pandas as pd
import json
import numpy as np
import httpx

app = FastAPI(title="Nautica Price Engine API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://batoo-analytics-3sd9.vercel.app",
        "https://*.vercel.app",  # preview deployments
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from google.cloud import bigquery

print("Loading master database from BigQuery...")
try:
    client = bigquery.Client(project="vast-ascent-457111-r0")
    query = "SELECT * FROM `vast-ascent-457111-r0.batoo_analytics.boats_staging`"
    df = client.query(query).to_dataframe()

    df['builder_search'] = df['builder'].str.lower()
    df['model_search'] = df['model'].str.lower()

    print("Building suggestions index...")
    df['full_name'] = df['builder'].astype(str) + " " + df['model'].astype(str)
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
    return {
        "status": "ok",
        "message": "Nautica Price Engine API is running",
        "total_boats": len(df) if not df.empty else 0
    }


@app.get("/suggestions")
def get_suggestions(q: str):
    if unique_boats_df.empty or not q or len(q) < 2:
        return []
    q_lower = q.lower().strip()
    mask = unique_boats_df['search_name'].str.contains(q_lower, na=False, regex=False)
    matches = unique_boats_df[mask].head(8)
    return matches['full_name'].tolist()


@app.get("/proxy-image")
async def proxy_image(url: str):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, follow_redirects=True)
            return Response(content=resp.content, media_type=resp.headers.get("Content-Type", "image/jpeg"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/builders")
def get_builders(q: Optional[str] = None):
    if df.empty: return []
    if q:
        mask = df['builder_search'].str.contains(q.lower(), na=False, regex=False)
        builders = df[mask]['builder'].dropna().unique().tolist()
    else:
        builders = df['builder'].dropna().unique().tolist()
    return sorted(builders)


@app.get("/models")
def get_models(builder: str, q: Optional[str] = None):
    if df.empty: return []
    mask = df['builder_search'] == builder.lower()
    if q:
        mask = mask & df['model_search'].str.contains(q.lower(), na=False, regex=False)
    models = df[mask]['model'].dropna().unique().tolist()
    return sorted(models)[:50]


@app.get("/carousel-images")
def get_carousel_images():
    if df.empty: return []
    has_image = df.dropna(subset=['image_url'])
    has_image = has_image[has_image['image_url'].str.startswith('http', na=False)]
    if has_image.empty: return []
    sample = has_image.sample(min(15, len(has_image)))
    return sample['image_url'].tolist()


@app.get("/sources")
def get_sources():
    """Ritorna le fonti/piattaforme presenti nel DB con conteggio."""
    if df.empty or 'source' not in df.columns:
        return []
    source_counts = df['source'].dropna().value_counts()
    return [
        {"name": str(src), "count": int(cnt)}
        for src, cnt in source_counts.items()
        if str(src).strip()
    ]


@app.get("/countries")
def get_countries():
    """Ritorna i paesi presenti nel DB con conteggio."""
    if df.empty or 'country' not in df.columns:
        return []
    country_counts = df['country'].dropna().value_counts()
    return [
        {"name": str(c), "count": int(cnt)}
        for c, cnt in country_counts.head(40).items()
        if str(c).strip()
    ]


@app.get("/sellers")
def get_sellers(q: Optional[str] = None):
    """Ritorna le agenzie/broker presenti nel DB, con autocomplete opzionale."""
    if df.empty or 'broker' not in df.columns:
        return []

    broker_col = df['broker'].dropna()
    broker_col = broker_col[broker_col.str.strip() != '']

    if q and len(q) >= 2:
        q_lower = q.lower()
        broker_col = broker_col[broker_col.str.lower().str.contains(q_lower, na=False, regex=False)]

    counts = broker_col.value_counts().head(30)
    return [
        {"name": str(name), "count": int(cnt)}
        for name, cnt in counts.items()
    ]


@app.get("/seller-stats")
def seller_stats(
    seller: str,
    lang: str = "it"
):
    """Ritorna statistiche complete per un'agenzia/broker specifico."""
    if df.empty:
        raise HTTPException(status_code=500, detail="Database not loaded")
    if 'broker' not in df.columns:
        raise HTTPException(status_code=404, detail="Colonna broker non disponibile nel database")

    # Ricerca intelligente: ogni parola della query deve essere presente nel nome (AND logic)
    # Es: "timone yachts" trova "Timone Yachts SRL", "Timone Yachts Italia", ecc.
    tokens = [t.strip() for t in seller.lower().split() if t.strip()]
    broker_lower = df['broker'].str.lower()
    mask = broker_lower.notna()
    for token in tokens:
        mask = mask & broker_lower.str.contains(token, na=False, regex=False)
    filtered = df[mask]

    if filtered.empty:
        raise HTTPException(status_code=404, detail=f"Nessun dato per l'agenzia '{seller}'")

    prices = filtered['price_eur'].dropna()

    # Top modelli
    top_models = (
        filtered.groupby(['builder', 'model']).size()
        .sort_values(ascending=False).head(10)
    )
    top_models_list = [
        {"name": f"{b} {m}", "count": int(c)}
        for (b, m), c in top_models.items()
    ]

    # Distribuzione per paese
    countries_list = []
    if 'country' in filtered.columns:
        c_counts = filtered['country'].value_counts().head(8)
        total_c = c_counts.sum()
        for c_name, c_cnt in c_counts.items():
            if pd.notna(c_name) and str(c_name).strip():
                c_prices = filtered[filtered['country'] == c_name]['price_eur'].dropna()
                countries_list.append({
                    "name": str(c_name),
                    "count": int(c_cnt),
                    "percentage": round(float(c_cnt / total_c * 100), 1),
                    "avg_price": round(float(c_prices.mean()), 2) if not c_prices.empty else 0,
                })

    # Fonti usate da questo broker
    sources_list = []
    if 'source' in filtered.columns:
        src_counts = filtered['source'].value_counts()
        for src, cnt in src_counts.items():
            if pd.notna(src) and str(src).strip():
                sources_list.append({"name": str(src), "count": int(cnt)})

    # Annunci recenti
    recent_cols = ['builder', 'model', 'year_built', 'price_eur', 'country', 'url', 'image_url', 'broker']
    for extra in ['source', 'status']:
        if extra in filtered.columns:
            recent_cols.append(extra)
    avail_cols = [c for c in recent_cols if c in filtered.columns]
    sort_col = 'updated_at' if 'updated_at' in filtered.columns else 'year_built'
    try:
        recent_df = filtered.sort_values(sort_col, ascending=False)[avail_cols].head(20).copy()
        for tc in ['updated_at', 'first_seen_at']:
            if tc in recent_df.columns:
                recent_df[tc] = recent_df[tc].astype(str)
        recent_listings = json.loads(recent_df.to_json(orient="records"))
    except Exception:
        recent_listings = []

    # Price trend per anno
    price_trend = []
    if 'year_built' in filtered.columns:
        trend_df = filtered.dropna(subset=['year_built', 'price_eur'])
        if not trend_df.empty:
            yearly = trend_df.groupby('year_built')['price_eur'].median().sort_index()
            for yr, pv in yearly.items():
                if pd.notna(yr) and yr > 1950:
                    price_trend.append({"year": int(yr), "avg_price": float(pv)})

    return {
        "seller": seller,
        "matched_names": sorted(filtered['broker'].dropna().unique().tolist()) if 'broker' in filtered.columns else [seller],
        "total_listings": len(filtered),
        "avg_price": round(float(prices.mean()), 2) if not prices.empty else 0,
        "median_price": round(float(prices.median()), 2) if not prices.empty else 0,
        "min_price": round(float(prices.min()), 2) if not prices.empty else 0,
        "max_price": round(float(prices.max()), 2) if not prices.empty else 0,
        "top_models": top_models_list,
        "countries": countries_list,
        "sources": sources_list,
        "price_trend": price_trend,
        "recent_listings": recent_listings,
    }


@app.get("/seller-listings")
def seller_listings(
    seller: str,
    page: int = 1,
    per_page: int = 20,
    source_filter: Optional[str] = None,
    sort: str = "year_desc",  # year_desc, year_asc, price_asc, price_desc
):
    """Ritorna TUTTI gli annunci di un broker/agenzia con paginazione."""
    if df.empty:
        raise HTTPException(status_code=500, detail="Database not loaded")
    if 'broker' not in df.columns:
        raise HTTPException(status_code=404, detail="Colonna broker non disponibile")

    # Ricerca intelligente multi-token AND: "timone yachts" → contiene "timone" AND "yachts"
    tokens = [t.strip() for t in seller.lower().split() if t.strip()]
    broker_lower = df['broker'].str.lower()
    mask = broker_lower.notna()
    for token in tokens:
        mask = mask & broker_lower.str.contains(token, na=False, regex=False)
    filtered = df[mask]

    if filtered.empty:
        raise HTTPException(status_code=404, detail=f"Nessun dato per '{seller}'")

    # Filtro per portale
    if source_filter and 'source' in filtered.columns:
        filtered = filtered[filtered['source'].str.lower() == source_filter.lower()]

    # Ordinamento
    sort_col = 'year_built'
    ascending = False
    if sort == 'year_asc':
        sort_col, ascending = 'year_built', True
    elif sort == 'price_asc':
        sort_col, ascending = 'price_eur', True
    elif sort == 'price_desc':
        sort_col, ascending = 'price_eur', False

    try:
        filtered = filtered.sort_values(sort_col, ascending=ascending)
    except Exception:
        pass

    total = len(filtered)
    total_pages = max(1, -(-total // per_page))  # ceil division
    start = (page - 1) * per_page
    end = start + per_page
    page_df = filtered.iloc[start:end]

    listing_cols = ['builder', 'model', 'year_built', 'price_eur', 'country', 'source', 'broker', 'url', 'image_url', 'length']
    for tc in ['status', 'updated_at', 'first_seen_at']:
        if tc in filtered.columns:
            listing_cols.append(tc)
    avail = [c for c in listing_cols if c in page_df.columns]
    page_df = page_df[avail].copy()
    for tc in ['updated_at', 'first_seen_at']:
        if tc in page_df.columns:
            page_df[tc] = page_df[tc].astype(str)
    page_df = page_df.where(pd.notna(page_df), None)

    return {
        "seller": seller,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "listings": json.loads(page_df.to_json(orient="records")),
    }


@app.get("/broker-stats")
def broker_stats(
    source: Optional[str] = None,
    country: Optional[str] = None,
    lang: str = "it"
):
    """Ritorna statistiche aggregate per una fonte/piattaforma e/o paese."""
    if df.empty:
        raise HTTPException(status_code=500, detail="Database not loaded")

    filtered = df.copy()
    if source:
        filtered = filtered[filtered['source'].str.lower() == source.lower()]
    if country:
        filtered = filtered[filtered['country'].str.lower() == country.lower()]

    if filtered.empty:
        raise HTTPException(status_code=404, detail="Nessun dato trovato per questa combinazione")

    prices = filtered['price_eur'].dropna()

    # Top 8 modelli per numero di annunci
    top_models = (
        filtered.groupby(['builder', 'model'])
        .size()
        .sort_values(ascending=False)
        .head(8)
    )
    top_models_list = [
        {"name": f"{b} {m}", "count": int(c)}
        for (b, m), c in top_models.items()
    ]

    # Price trend (mediana per anno)
    price_trend = []
    if 'year_built' in filtered.columns:
        trend_df = filtered.dropna(subset=['year_built', 'price_eur'])
        if not trend_df.empty:
            yearly = trend_df.groupby('year_built')['price_eur'].agg(['median', lambda x: np.percentile(x, 25), lambda x: np.percentile(x, 75)]).sort_index()
            yearly.columns = ['median', 'q25', 'q75']
            for yr, row in yearly.iterrows():
                if pd.notna(yr) and yr > 1950:
                    price_trend.append({
                        "year": int(yr),
                        "avg_price": round(float(row['median']), 2),
                        "q25": round(float(row['q25']), 2),
                        "q75": round(float(row['q75']), 2),
                    })

    # Distribuzione per paese
    countries_list = []
    if 'country' in filtered.columns:
        c_counts = filtered['country'].value_counts().head(6)
        total_c = c_counts.sum()
        for c_name, c_cnt in c_counts.items():
            if pd.notna(c_name):
                c_prices = filtered[filtered['country'] == c_name]['price_eur'].dropna()
                countries_list.append({
                    "name": str(c_name),
                    "count": int(c_cnt),
                    "percentage": round(float(c_cnt / total_c * 100), 1),
                    "avg_price": round(float(c_prices.mean()), 2) if not c_prices.empty else 0
                })

    # Annunci recenti
    recent_cols = ['builder', 'model', 'year_built', 'price_eur', 'country', 'url', 'image_url']
    if 'source' in filtered.columns: recent_cols.append('source')
    if 'status' in filtered.columns: recent_cols.append('status')
    avail_cols = [c for c in recent_cols if c in filtered.columns]
    sort_col = 'updated_at' if 'updated_at' in filtered.columns else 'year_built'
    try:
        recent_df = filtered.sort_values(sort_col, ascending=False)[avail_cols].head(20).copy()
        if 'updated_at' in recent_df.columns:
            recent_df['updated_at'] = recent_df['updated_at'].astype(str)
        if 'first_seen_at' in recent_df.columns:
            recent_df['first_seen_at'] = recent_df['first_seen_at'].astype(str)
        recent_listings = json.loads(recent_df.to_json(orient="records"))
    except Exception:
        recent_listings = []

    return {
        "source": source or "all",
        "country": country or "all",
        "total_listings": len(filtered),
        "avg_price": round(float(prices.mean()), 2) if not prices.empty else 0,
        "median_price": round(float(prices.median()), 2) if not prices.empty else 0,
        "min_price": round(float(prices.min()), 2) if not prices.empty else 0,
        "max_price": round(float(prices.max()), 2) if not prices.empty else 0,
        "top_models": top_models_list,
        "price_trend": price_trend,
        "countries": countries_list,
        "recent_listings": recent_listings,
    }


@app.get("/evaluate")
def evaluate_boat(
    q: str,
    year: Optional[int] = None,
    lang: str = "it",
    source_filter: Optional[str] = None,
    country_filter: Optional[str] = None,
):
    """Motore di valutazione 'Google-style': identifica cantiere e modello da una stringa unica."""
    if df.empty:
        raise HTTPException(status_code=500, detail="Database not loaded")

    q_lower = q.lower().strip()
    words = q_lower.split()

    if not words:
        raise HTTPException(status_code=400, detail="Inserisci un termine di ricerca")

    # 1. Identificazione Cantiere
    all_builders = df['builder_search'].dropna().unique()
    found_builder = None
    remaining_model_words = []

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

    # 2. Full-text search mask
    mask = pd.Series([True] * len(df))
    search_col = df['builder_search'].fillna('') + " " + df['model_search'].fillna('')
    for kw in words:
        mask = mask & search_col.str.contains(kw, na=False, regex=False)

    matched_df = df[mask]

    # 2b. Filtri aggiuntivi (fonte, paese)
    if source_filter and 'source' in matched_df.columns:
        src_mask = matched_df['source'].str.lower() == source_filter.lower()
        if src_mask.any():
            matched_df = matched_df[src_mask]

    if country_filter and 'country' in matched_df.columns:
        ctr_mask = matched_df['country'].str.lower() == country_filter.lower()
        if ctr_mask.any():
            matched_df = matched_df[ctr_mask]

    if matched_df.empty:
        raise HTTPException(status_code=404, detail=f"Nessun risultato per '{q}'")

    # 3. Filtro Anno (±2 anni)
    if year:
        year_mask = (matched_df['year_built'] >= year - 2) & (matched_df['year_built'] <= year + 2)
        if not matched_df[year_mask].empty:
            matched_df = matched_df[year_mask]

    # 4. Statistiche prezzi
    prices = matched_df['price_eur'].dropna()
    if prices.empty:
        raise HTTPException(status_code=404, detail="Dati di prezzo non disponibili")

    if len(prices) > 5:
        p5 = np.percentile(prices, 5)
        p95 = np.percentile(prices, 95)
        prices_clean = prices[(prices >= p5) & (prices <= p95)]
        clean_df = matched_df[(matched_df['price_eur'] >= p5) & (matched_df['price_eur'] <= p95)]
    else:
        prices_clean = prices
        clean_df = matched_df

    avg_price = float(prices_clean.mean())
    median_price = float(prices_clean.median())
    min_price = float(prices_clean.min())
    max_price = float(prices_clean.max())

    # 5. Affidabilità
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

    # 6. Svalutazione e Trend con IQR
    depreciation_value = 0
    depreciation_percent = 0
    has_depreciation = False
    price_trend = []

    if len(clean_df) > 0:
        trend_df = clean_df.dropna(subset=['year_built', 'price_eur'])
        if not trend_df.empty:
            yearly_median = trend_df.groupby('year_built')['price_eur'].median().sort_index()
            yearly_q25 = trend_df.groupby('year_built')['price_eur'].quantile(0.25).sort_index()
            yearly_q75 = trend_df.groupby('year_built')['price_eur'].quantile(0.75).sort_index()

            for year_val, price_val in yearly_median.items():
                if pd.notna(year_val) and pd.notna(price_val) and year_val > 1950:
                    price_trend.append({
                        "year": int(year_val),
                        "avg_price": float(price_val),
                        "q25": float(yearly_q25.get(year_val, price_val)),
                        "q75": float(yearly_q75.get(year_val, price_val)),
                    })

            if len(yearly_median) >= 2 and (yearly_median.index[-1] - yearly_median.index[0]) >= 3:
                price_old = float(yearly_median.iloc[0])
                price_new = float(yearly_median.iloc[-1])
                years_diff = float(yearly_median.index[-1] - yearly_median.index[0])
                if price_new > price_old and years_diff > 0:
                    depreciation_value = (price_new - price_old) / years_diff
                    depreciation_percent = (depreciation_value / price_new) * 100
                    has_depreciation = True

    # 7. Metriche di mercato (vendute/rimosse)
    sold_last_week = 0
    liquidity_color = None

    if 'status' in matched_df.columns and 'updated_at' in matched_df.columns:
        try:
            market_df = matched_df.copy()
            market_df['updated_at_dt'] = pd.to_datetime(market_df['updated_at']).dt.tz_localize(None)
            one_week_ago = pd.Timestamp.now() - pd.Timedelta(days=7)
            sold_mask = (market_df['status'] == False) & (market_df['updated_at_dt'] >= one_week_ago)
            sold_last_week = int(sold_mask.sum())
            if sold_last_week > 0:
                liquidity_color = "green"
        except Exception as e:
            print(f"Errore metriche mercato: {e}")

    # 8. Indice Liquidità
    total_found = len(matched_df)
    if total_found < 5:
        liquidity = "Scarsità Estrema"
        if not liquidity_color: liquidity_color = "red"
    elif total_found < 20:
        liquidity = "Bassa (Mercato Esclusivo)"
        if not liquidity_color: liquidity_color = "yellow"
    elif total_found < 80:
        liquidity = "Normale (Buona Scambiabilità)"
        liquidity_color = "green"
    else:
        liquidity = "Alta (Mercato Liquido)"
        liquidity_color = "blue"

    # 9. Età media e prezzo al metro
    current_year = 2026
    valid_years = clean_df['year_built'].dropna()
    avg_age = current_year - float(valid_years.median()) if not valid_years.empty else 0

    clean_df_length = clean_df.dropna(subset=['length', 'price_eur'])
    clean_df_length = clean_df_length[clean_df_length['length'] > 0]
    avg_price_per_meter = 0
    if not clean_df_length.empty:
        price_per_m = clean_df_length['price_eur'] / clean_df_length['length']
        avg_price_per_meter = float(price_per_m.median()) if not price_per_m.empty and pd.notna(price_per_m.median()) else 0

    # 10. Distribuzione geografica con prezzo medio per nazione
    top_countries = []
    if 'country' in clean_df.columns:
        countries_counts = clean_df['country'].value_counts()
        total_countries = countries_counts.sum()
        for country, count in countries_counts.items():
            if pd.notna(country) and country.strip() and total_countries > 0:
                perc = (count / total_countries) * 100
                country_prices = clean_df[clean_df['country'] == country]['price_eur'].dropna()
                country_avg_price = float(country_prices.mean()) if not country_prices.empty and pd.notna(country_prices.mean()) else 0
                top_countries.append({
                    "name": country,
                    "count": int(count),
                    "percentage": round(float(perc), 1),
                    "avg_price": round(float(country_avg_price), 2)
                })

    # 11. Source breakdown
    source_breakdown = []
    if 'source' in clean_df.columns:
        src_counts = clean_df['source'].dropna().value_counts()
        total_src = src_counts.sum()
        for src, cnt in src_counts.head(6).items():
            if pd.notna(src) and str(src).strip():
                src_prices = clean_df[clean_df['source'] == src]['price_eur'].dropna()
                source_breakdown.append({
                    "source": str(src),
                    "count": int(cnt),
                    "percentage": round(float(cnt / total_src * 100), 1),
                    "avg_price": round(float(src_prices.mean()), 2) if not src_prices.empty else 0,
                })

    # 12. Comparabili: ordina + percentile
    sorted_df = matched_df.sort_values(by='year_built', ascending=False)

    cols_to_extract = ['id', 'builder', 'model', 'year_built', 'length', 'country', 'price_eur', 'url', 'image_url']
    for extra_col in ['source', 'status', 'first_seen_at', 'updated_at']:
        if extra_col in sorted_df.columns:
            cols_to_extract.append(extra_col)

    extracted_df = sorted_df[cols_to_extract].head(50).copy()
    if 'first_seen_at' in extracted_df.columns:
        extracted_df['first_seen_at'] = extracted_df['first_seen_at'].astype(str)
    if 'updated_at' in extracted_df.columns:
        extracted_df['updated_at'] = extracted_df['updated_at'].astype(str)

    samples = json.loads(extracted_df.to_json(orient="records"))

    # Aggiungi percentile di prezzo a ogni comparable
    for s in samples:
        p = s.get('price_eur')
        if p is not None and not prices_clean.empty:
            s['price_percentile'] = int((prices_clean < p).mean() * 100)
        else:
            s['price_percentile'] = None

    # 13. AI Insight
    if lang == "en":
        ai_insight = f"The AI analyzed {total_found} listings for {found_builder.capitalize() if found_builder else q.capitalize()}. "
        if has_depreciation:
            if depreciation_percent > 7:
                ai_insight += f"The model shows marked depreciation (~{round(depreciation_percent,1)}%/yr). Great for used boat buyers, less ideal for short-term investment. "
            elif depreciation_percent > 4:
                ai_insight += f"Depreciation is in line with market average (~{round(depreciation_percent,1)}%/yr). "
            else:
                ai_insight += f"Strong value retention (est. {round(depreciation_percent,1)}%/yr depreciation). A safe long-term purchase. "
        else:
            ai_insight += "Market prices appear stable with no clear depreciation trend by year. "
        if avg_price_per_meter > 0:
            if avg_price_per_meter > 50000:
                ai_insight += f"At €{format(int(avg_price_per_meter),',')}/m, this is a premium segment vessel. "
            else:
                ai_insight += f"At €{format(int(avg_price_per_meter),',')}/m, it offers accessible value. "
        if liquidity_color in ("red", "yellow"):
            ai_insight += "Scarcity of listings suggests an exclusive market — negotiations may take time."
        else:
            ai_insight += "Good market availability ensures easy resale (excellent liquidity)."
    else:
        ai_insight = f"L'IA ha analizzato {total_found} annunci per il modello {found_builder.capitalize() if found_builder else q.capitalize()}. "
        if has_depreciation:
            if depreciation_percent > 7:
                ai_insight += f"Il modello subisce una svalutazione marcata (circa {round(depreciation_percent,1)}% annuo). Ottimo per chi cerca un usato svalutato, meno per investimenti a breve termine. "
            elif depreciation_percent > 4:
                ai_insight += f"La svalutazione è in linea con la media di mercato (circa {round(depreciation_percent,1)}% annuo). "
            else:
                ai_insight += f"La tenuta del valore è solida (svalutazione stimata {round(depreciation_percent,1)}% annuo). Un acquisto sicuro nel tempo. "
        else:
            ai_insight += "Il mercato per questo modello appare stabile e i prezzi non mostrano flessioni evidenti legate all'anno. "
        if avg_price_per_meter > 0:
            if avg_price_per_meter > 50000:
                ai_insight += f"Con {format(int(avg_price_per_meter),',').replace(',','.')} €/m, si posiziona nella fascia alta del mercato. "
            else:
                ai_insight += f"Il costo al metro di {format(int(avg_price_per_meter),',').replace(',','.')} € evidenzia un posizionamento accessibile. "
        if liquidity_color in ("red", "yellow"):
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
            "median_price_eur": round(median_price, 2),
            "min_price_eur": round(min_price, 2),
            "max_price_eur": round(max_price, 2),
            "has_depreciation": has_depreciation,
            "depreciation_value_eur": round(depreciation_value, 2) if has_depreciation else 0,
            "depreciation_percent": round(depreciation_percent, 2) if has_depreciation else 0,
            "median_age_years": round(avg_age, 1),
            "average_price_per_meter": round(avg_price_per_meter, 2),
            "market_share_countries": top_countries,
            "source_breakdown": source_breakdown,
            "liquidity_status": liquidity,
            "liquidity_color": liquidity_color,
            "price_trend": price_trend,
            "sold_last_week": sold_last_week,
            "price_change_last_month_percent": 0,
        },
        "comparables": samples,
    }
