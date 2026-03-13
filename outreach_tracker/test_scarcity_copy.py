import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import json
import time

def format_currency(value):
    if pd.isna(value) or value == 0:
        return "N/A"
    if value >= 1_000_000:
        return f"€{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"€{value/1_000:.0f}k"
    else:
        return f"€{value:.0f}"

def generate_dual_language_email(broker_name, stats, specific_boat):
    top_models_str = ", ".join(stats['top_models'][:3])
    calendly_link = "https://calendly.com/giorgio96rota/30min"
    whatsapp_link = "https://wa.me/393454590116"

    # ITALIAN CONTENT
    it_title = f"Analisi Portafoglio: {broker_name}"
    it_greeting = f"Gentile team di {broker_name},"
    it_intro = f"Abbiamo analizzato il vostro portafoglio di imbarcazioni online (aggregando i dati da vari portali) e siamo rimasti impressionati."
    it_stat1, it_stat2, it_stat3 = "Annunci Attivi", "Valore Stimato", "Prezzo Medio"
    it_models_label = "I vostri modelli di punta:"
    
    it_boat_title = "Analisi Modello Specifico"
    it_boat_text = f"Come esempio delle nostre capacità analitiche, abbiamo valutato uno dei modelli che avete in vendita: <b>{specific_boat['name']}</b> (età media {specific_boat['year']})."
    it_li_dep = f"<b>Svalutazione stimata:</b> {specific_boat['depreciation']}% annuo."
    it_li_liq = f"<b>Liquidità di mercato:</b> {specific_boat['liquidity_it']}."
    it_li_price = f"<b>Prezzo medio Europeo:</b> {format_currency(specific_boat['avg_price'])}."

    it_pitch_title = "Cosa fa Batoo Analytics? 🚀"
    it_pitch_text = "Il nostro motore AI monitora 90.000+ annunci nel mercato nautico europeo, permettendovi di:"
    it_pt1 = "Valutare istantaneamente prezzo e svalutazione di qualsiasi modello prima di prendere un mandato."
    it_pt2 = "Monitorare la liquidità e i tempi medi di vendita dei vostri top brand."
    it_pt3 = "Scoprire i prezzi reali e le variazioni dei vostri competitor in tempo reale."
    
    it_cta_intro = "Il tool non è ancora pubblico, ma <b>stiamo selezionando 10 agenzie partner</b> per farglielo testare gratuitamente e in esclusiva.<br><br>Rispondete a questa email o prenotate una demo per ricevere le credenziali di accesso:"
    it_cta_button = "Prenota una Demo"
    it_reply = f"In alternativa potete anche scrivermi direttamente su WhatsApp al <a href='{whatsapp_link}' style='color: #2563eb; text-decoration: none;'>+39 345 459 0116</a>."

    # ENGLISH CONTENT
    en_title = f"Portfolio Analysis: {broker_name}"
    en_greeting = f"Hi {broker_name} team,"
    en_intro = f"We analyzed your online yacht portfolio across multiple portals and were very impressed with your inventory."
    en_stat1, en_stat2, en_stat3 = "Active Listings", "Est. Value", "Average Price"
    en_models_label = "Your top models:"
    
    en_boat_title = "Specific Model Analysis"
    en_boat_text = f"As an example of our analytical capabilities, we evaluated one of the models you have for sale: <b>{specific_boat['name']}</b> (avg age {specific_boat['year']})."
    en_li_dep = f"<b>Estimated depreciation:</b> {specific_boat['depreciation']}% per year."
    en_li_liq = f"<b>Market liquidity:</b> {specific_boat['liquidity_en']}."
    en_li_price = f"<b>European avg price:</b> {format_currency(specific_boat['avg_price'])}."

    en_pitch_title = "What is Batoo Analytics? 🚀"
    en_pitch_text = "Our AI engine monitors 90,000+ listings in the European yachting market, allowing you to:"
    en_pt1 = "Instantly evaluate the correct market price and depreciation of any model."
    en_pt2 = "Monitor market liquidity and average selling times for your top brands."
    en_pt3 = "Track real asking prices and competitor changes in real time."
    
    en_cta_intro = "The tool is not yet public, but <b>we are selecting 10 partner agencies</b> to test it for free and exclusively.<br><br>Reply to this email or book a demo to receive your access credentials:"
    en_cta_button = "Book a Demo"
    en_reply = f"Alternatively, you can message me directly on WhatsApp at <a href='{whatsapp_link}' style='color: #2563eb; text-decoration: none;'>+39 345 459 0116</a>."

    signoff = "Un cordiale saluto / Best regards,"
    signature = "Giorgio Rota<br>Founder, Batoo Analytics<br><a href='https://www.batoo.it' style='color: #64748b; text-decoration: none;'>www.batoo.it</a>"

    # Decide primary language based on stats
    primary = 'it' if stats.get('lang', 'it') == 'it' else 'en'
    
    subject = f"Analisi portafoglio barche per {broker_name} 📊" if primary == 'it' else f"Yacht portfolio analysis for {broker_name} 📊"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333333; background-color: #f4f5f7; margin: 0; padding: 0; -webkit-text-size-adjust: 100%; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
            .header {{ background-color: #0f172a; padding: 25px 20px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 22px; font-weight: 600; }}
            .content {{ padding: 30px 25px; }}
            .greeting {{ font-size: 17px; font-weight: 600; margin-bottom: 15px; color: #1e293b; }}
            .stats-container {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin: 20px 0; display: block; }}
            .stats-grid {{ display: table; width: 100%; table-layout: fixed; }}
            .stat-box {{ display: table-cell; text-align: center; padding: 15px 10px; vertical-align: middle; }}
            .stat-box.border-right {{ border-right: 1px solid #cbd5e1; }}
            .stat-value {{ font-size: 20px; font-weight: 700; color: #0ea5e9; margin-bottom: 4px; }}
            .stat-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; font-weight: 600; }}
            .models {{ background: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin-bottom: 25px; border-radius: 0 4px 4px 0; }}
            .models-label {{ font-weight: 600; color: #166534; margin-bottom: 4px; font-size: 13px; }}
            .models-text {{ color: #15803d; font-size: 14px; }}
            .boat-analysis {{ background-color: #fffbeb; border: 1px solid #fde68a; padding: 20px; border-radius: 8px; margin-bottom: 25px; }}
            .pitch-title {{ font-size: 17px; font-weight: 600; color: #1e293b; margin-bottom: 12px; }}
            .features {{ padding-left: 20px; margin-bottom: 25px; margin-top: 10px; }}
            .features li {{ margin-bottom: 8px; color: #475569; font-size: 14.5px; }}
            .cta-section {{ text-align: center; margin: 35px 0 20px 0; background: #eff6ff; padding: 25px; border-radius: 8px; border: 1px solid #bfdbfe; }}
            .cta-intro {{ margin-bottom: 15px; color: #1e3a8a; font-size: 15px; }}
            .cta-btn {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); }}
            .reply-text {{ margin-top: 25px; font-size: 14px; color: #475569; text-align: center; }}
            .footer {{ margin-top: 35px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 14px; }}
            .divider {{ height: 1px; background-color: #e2e8f0; margin: 40px 0; }}
            .lang-switch {{ text-align: center; font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px; }}
            
            @media only screen and (max-width: 480px) {{
                .stats-grid {{ display: block; }}
                .stat-box {{ display: block; width: 100%; border-right: none !important; border-bottom: 1px solid #cbd5e1; padding: 15px 0; }}
                .stat-box:last-child {{ border-bottom: none; }}
                .stat-value {{ font-size: 22px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{it_title if primary == 'it' else en_title}</h1>
            </div>
            <div class="content">
                <!-- PRIMARY LANGUAGE -->
                <div class="greeting">{it_greeting if primary == 'it' else en_greeting}</div>
                <p style="font-size: 15px;">{it_intro if primary == 'it' else en_intro}</p>
                
                <div class="stats-container">
                    <div class="stats-grid">
                        <div class="stat-box border-right">
                            <div class="stat-value">{stats['listings_count']}</div>
                            <div class="stat-label">{it_stat1 if primary == 'it' else en_stat1}</div>
                        </div>
                        <div class="stat-box border-right">
                            <div class="stat-value">{format_currency(stats['total_value'])}</div>
                            <div class="stat-label">{it_stat2 if primary == 'it' else en_stat2}</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{format_currency(stats['avg_price'])}</div>
                            <div class="stat-label">{it_stat3 if primary == 'it' else en_stat3}</div>
                        </div>
                    </div>
                </div>
                
                <div class="models">
                    <div class="models-label">{it_models_label if primary == 'it' else en_models_label}</div>
                    <div class="models-text">{top_models_str}</div>
                </div>

                <div class="boat-analysis">
                    <div class="pitch-title">{it_boat_title if primary == 'it' else en_boat_title}</div>
                    <p style="font-size: 14.5px; margin-bottom: 12px;">{it_boat_text if primary == 'it' else en_boat_text}</p>
                    <ul class="features">
                        <li>{it_li_dep if primary == 'it' else en_li_dep}</li>
                        <li>{it_li_liq if primary == 'it' else en_li_liq}</li>
                        <li>{it_li_price if primary == 'it' else en_li_price}</li>
                    </ul>
                </div>

                <div class="pitch-title">{it_pitch_title if primary == 'it' else en_pitch_title}</div>
                <p style="font-size: 14.5px;">{it_pitch_text if primary == 'it' else en_pitch_text}</p>
                <ul class="features">
                    <li>{it_pt1 if primary == 'it' else en_pt1}</li>
                    <li>{it_pt2 if primary == 'it' else en_pt2}</li>
                    <li>{it_pt3 if primary == 'it' else en_pt3}</li>
                </ul>

                <div class="cta-section">
                    <p class="cta-intro">{it_cta_intro if primary == 'it' else en_cta_intro}</p>
                    <a href="{calendly_link}" class="cta-btn">{it_cta_button if primary == 'it' else en_cta_button}</a>
                </div>
                
                <div class="reply-text">
                    {it_reply if primary == 'it' else en_reply}
                </div>

                <div class="divider"></div>
                <div class="lang-switch">⬇️ { "English Translation" if primary == 'it' else "Traduzione Italiana" } ⬇️</div>

                <!-- SECONDARY LANGUAGE -->
                <div class="greeting">{en_greeting if primary == 'it' else it_greeting}</div>
                <p style="font-size: 15px;">{en_intro if primary == 'it' else it_intro}</p>
                
                <div class="models">
                    <div class="models-label">{en_models_label if primary == 'it' else it_models_label}</div>
                    <div class="models-text">{top_models_str}</div>
                </div>

                <div class="boat-analysis">
                    <div class="pitch-title">{en_boat_title if primary == 'it' else it_boat_title}</div>
                    <p style="font-size: 14.5px; margin-bottom: 12px;">{en_boat_text if primary == 'it' else it_boat_text}</p>
                    <ul class="features">
                        <li>{en_li_dep if primary == 'it' else it_li_dep}</li>
                        <li>{en_li_liq if primary == 'it' else it_li_liq}</li>
                        <li>{en_li_price if primary == 'it' else it_li_price}</li>
                    </ul>
                </div>

                <div class="pitch-title">{en_pitch_title if primary == 'it' else it_pitch_title}</div>
                <p style="font-size: 14.5px;">{en_pitch_text if primary == 'it' else it_pitch_text}</p>
                <ul class="features">
                    <li>{en_pt1 if primary == 'it' else it_pt1}</li>
                    <li>{en_pt2 if primary == 'it' else it_pt2}</li>
                    <li>{en_pt3 if primary == 'it' else it_pt3}</li>
                </ul>

                <div class="cta-section">
                    <p class="cta-intro">{en_cta_intro if primary == 'it' else it_cta_intro}</p>
                    <a href="{calendly_link}" class="cta-btn">{en_cta_button if primary == 'it' else it_cta_button}</a>
                </div>
                
                <div class="reply-text">
                    {en_reply if primary == 'it' else it_reply}
                </div>

                <div class="footer">
                    {signoff}<br>
                    <strong>{signature}</strong>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_text = f"Visualizza questa email in un client che supporta HTML."
    return subject, plain_text, html


def fallback_boat():
    return {
        "name": "Axopar 37",
        "year": 2021,
        "depreciation": 5.8,
        "liquidity_it": "Altissima (Molto richiesto, vendita < 20 gg)",
        "liquidity_en": "Very High (High demand, sales < 20 days)",
        "avg_price": 245000
    }

def get_best_boat_data(top_models_list, df_boats):
    for model_name in top_models_list:
        if not model_name or model_name.strip() == "Generici":
            continue
            
        mask = df_boats['builder'].astype(str).str.lower() + " " + df_boats['model'].astype(str).str.lower()
        matched = df_boats[mask.str.contains(model_name.lower().strip(), regex=False, na=False)]
        
        if len(matched) >= 5:
            prices = matched['price_eur'].dropna()
            if not prices.empty:
                avg_price = prices.mean()
                year = int(matched['year_built'].median()) if not matched['year_built'].dropna().empty else 2018
                
                if len(matched) > 30:
                    liq_it = "Alta (Vendita in ~30 gg)"
                    liq_en = "High (Sales in ~30 days)"
                elif len(matched) > 10:
                    liq_it = "Normale (Buona Scambiabilità)"
                    liq_en = "Normal (Good Tradability)"
                else:
                    liq_it = "Bassa (Mercato Esclusivo)"
                    liq_en = "Low (Exclusive Market)"
                    
                return {
                    "name": model_name,
                    "year": year,
                    "depreciation": 4.5,
                    "liquidity_it": liq_it,
                    "liquidity_en": liq_en,
                    "avg_price": avg_price
                }
                
    return fallback_boat()

def send_test(to_email, smtp_pass):
    df_boats = pd.DataFrame([
        {'builder': 'Azimut', 'model': '60', 'price_eur': 900000, 'year_built': 2018},
    ])
    
    stats = {
        'listings_count': 45,
        'total_value': 12500000,
        'avg_price': 277000,
        'top_models': ['Azimut 60', 'Ferretti 550', 'Sanlorenzo 72'],
        'lang': 'it'
    }
    
    boat = get_best_boat_data(stats['top_models'], df_boats)
    subject, plain_text, html_content = generate_dual_language_email("Italian Yachts SRL", stats, boat)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"Giorgio Rota <giorgio96rota@gmail.com>"
    msg['To'] = to_email
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("giorgio96rota@gmail.com", smtp_pass)
        server.sendmail("giorgio96rota@gmail.com", to_email, msg.as_string())
        server.quit()
        print(f"✅ Email inviata con successo (Test Copy '10 agenzie') a {to_email}")
        
    except Exception as e:
        print(e)

if __name__ == "__main__":
    send_test("giorgio96rota@gmail.com", "itrjkodkvclwofzd")