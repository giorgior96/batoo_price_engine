import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import json
import csv
import os
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

def generate_html_email(broker_name, stats, specific_boat=None, lang='it'):
    top_models_str = ", ".join(stats['top_models'][:3])
    calendly_link = "https://calendly.com/giorgio96rota/30min"
    
    if lang == 'it':
        subject = f"Analisi portafoglio barche per {broker_name} 📊"
        title = f"Analisi Portafoglio: {broker_name}"
        intro = f"Abbiamo analizzato il vostro portafoglio di imbarcazioni online (aggregando i dati da vari portali) e siamo rimasti impressionati."
        
        stat1_label = "Annunci Attivi"
        stat2_label = "Valore Stimato"
        stat3_label = "Prezzo Medio"
        
        models_label = "I vostri modelli di punta:"
        
        boat_analysis_title = "Analisi Modello Specifico"
        if specific_boat:
            boat_text = f"Come esempio delle nostre capacità analitiche, abbiamo valutato uno dei modelli che avete attualmente in vendita: <b>{specific_boat['name']} ({specific_boat['year']})</b>."
            li_dep = f"<b>Svalutazione stimata:</b> {specific_boat['depreciation']}% annuo."
            li_liq = f"<b>Liquidità di mercato:</b> {specific_boat['liquidity']} (velocità di vendita)."
            li_price = f"<b>Prezzo medio Europeo:</b> {format_currency(specific_boat['avg_price'])}."
        else:
            boat_text = ""
            li_dep = ""
            li_liq = ""
            li_price = ""

        pitch_title = "Cosa fa Batoo Analytics? 🚀"
        pitch_text = "Il nostro motore di intelligenza artificiale monitora 90.000+ annunci nel mercato nautico europeo, permettendovi di:"
        point1 = "Valutare istantaneamente il corretto prezzo e la svalutazione di qualsiasi modello prima di prendere un mandato."
        point2 = "Monitorare la liquidità e i tempi medi di vendita dei vostri top brand."
        point3 = "Scoprire i prezzi reali e le variazioni dei vostri competitor in tempo reale."
        
        cta_intro = "Per mostrarvi come questi dati possano farvi acquisire mandati migliori e vendere più velocemente, vi propongo una rapida chiamata conoscitiva di 15 minuti."
        cta_button = "Prenota una Demo"
        signoff = "Un cordiale saluto,"
        signature = "Giorgio Rota<br>Founder, Batoo Analytics"
    else:
        subject = f"Yacht portfolio analysis for {broker_name} 📊"
        title = f"Portfolio Analysis: {broker_name}"
        intro = f"We analyzed your online yacht portfolio across multiple portals and were very impressed with your inventory."
        
        stat1_label = "Active Listings"
        stat2_label = "Est. Value"
        stat3_label = "Average Price"
        
        models_label = "Your top models:"
        
        boat_analysis_title = "Specific Model Analysis"
        if specific_boat:
            boat_text = f"As an example of our analytical capabilities, we evaluated one of the models you currently have for sale: <b>{specific_boat['name']} ({specific_boat['year']})</b>."
            li_dep = f"<b>Estimated depreciation:</b> {specific_boat['depreciation']}% per year."
            li_liq = f"<b>Market liquidity:</b> {specific_boat['liquidity']} (sales velocity)."
            li_price = f"<b>European avg price:</b> {format_currency(specific_boat['avg_price'])}."
        else:
            boat_text = ""
            li_dep = ""
            li_liq = ""
            li_price = ""

        pitch_title = "What is Batoo Analytics? 🚀"
        pitch_text = "Our AI engine continuously monitors 90,000+ listings in the European yachting market, allowing you to:"
        point1 = "Instantly evaluate the correct market price and depreciation of any model before signing a mandate."
        point2 = "Monitor market liquidity and average selling times for your top brands."
        point3 = "Track real asking prices and competitor changes in real time."
        
        cta_intro = "To show you how this data can help you secure better mandates and close sales faster, I'd like to invite you for a quick 15-minute introductory call."
        cta_button = "Book a Demo"
        signoff = "Best regards,"
        signature = "Giorgio Rota<br>Founder, Batoo Analytics"

    boat_html = ""
    if specific_boat:
        boat_html = f"""
        <div class="boat-analysis">
            <div class="pitch-title">{boat_analysis_title}</div>
            <p>{boat_text}</p>
            <ul class="features">
                <li>{li_dep}</li>
                <li>{li_liq}</li>
                <li>{li_price}</li>
            </ul>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                background-color: #f4f5f7;
                margin: 0;
                padding: 0;
                -webkit-text-size-adjust: 100%;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}
            .header {{
                background-color: #0f172a;
                padding: 25px 20px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                margin: 0;
                font-size: 22px;
                font-weight: 600;
            }}
            .content {{
                padding: 30px 25px;
            }}
            .greeting {{
                font-size: 17px;
                font-weight: 600;
                margin-bottom: 15px;
                color: #1e293b;
            }}
            /* Stack on mobile, row on desktop */
            .stats-container {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin: 20px 0;
                display: block; /* Fallback for older clients */
            }}
            .stats-grid {{
                display: table;
                width: 100%;
                table-layout: fixed;
            }}
            .stat-box {{
                display: table-cell;
                text-align: center;
                padding: 15px 10px;
                vertical-align: middle;
            }}
            .stat-box.border-right {{
                border-right: 1px solid #cbd5e1;
            }}
            .stat-value {{
                font-size: 20px;
                font-weight: 700;
                color: #0ea5e9;
                margin-bottom: 4px;
            }}
            .stat-label {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #64748b;
                font-weight: 600;
            }}
            .models {{
                background: #f0fdf4;
                border-left: 4px solid #22c55e;
                padding: 15px;
                margin-bottom: 25px;
                border-radius: 0 4px 4px 0;
            }}
            .models-label {{
                font-weight: 600;
                color: #166534;
                margin-bottom: 4px;
                font-size: 13px;
            }}
            .models-text {{
                color: #15803d;
                font-size: 14px;
            }}
            .boat-analysis {{
                background-color: #fffbeb;
                border: 1px solid #fde68a;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 25px;
            }}
            .pitch-title {{
                font-size: 17px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 12px;
            }}
            .features {{
                padding-left: 20px;
                margin-bottom: 25px;
            }}
            .features li {{
                margin-bottom: 8px;
                color: #475569;
                font-size: 14px;
            }}
            .cta-section {{
                text-align: center;
                margin: 35px 0 20px 0;
            }}
            .cta-intro {{
                margin-bottom: 15px;
                color: #334155;
            }}
            .cta-btn {{
                display: inline-block;
                background-color: #2563eb;
                color: #ffffff !important;
                text-decoration: none;
                padding: 14px 28px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 15px;
            }}
            .footer {{
                margin-top: 35px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                color: #64748b;
                font-size: 14px;
            }}
            
            /* Responsive adjustments */
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
                <h1>{title}</h1>
            </div>
            <div class="content">
                <div class="greeting">Gentile team di {broker_name},</div>
                <p style="font-size: 15px;">{intro}</p>
                
                <div class="stats-container">
                    <div class="stats-grid">
                        <div class="stat-box border-right">
                            <div class="stat-value">{stats['listings_count']}</div>
                            <div class="stat-label">{stat1_label}</div>
                        </div>
                        <div class="stat-box border-right">
                            <div class="stat-value">{format_currency(stats['total_value'])}</div>
                            <div class="stat-label">{stat2_label}</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{format_currency(stats['avg_price'])}</div>
                            <div class="stat-label">{stat3_label}</div>
                        </div>
                    </div>
                </div>
                
                <div class="models">
                    <div class="models-label">{models_label}</div>
                    <div class="models-text">{top_models_str}</div>
                </div>

                {boat_html}

                <div class="pitch-title">{pitch_title}</div>
                <p style="font-size: 14px;">{pitch_text}</p>
                <ul class="features">
                    <li>{point1}</li>
                    <li>{point2}</li>
                    <li>{point3}</li>
                </ul>

                <div class="cta-section">
                    <p class="cta-intro"><b>{cta_intro}</b></p>
                    <a href="{calendly_link}" class="cta-btn">{cta_button}</a>
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
    
    # Text fallback
    plain_text = f"""{title}

Gentile team di {broker_name},

{intro}

STATISTICHE RILEVATE:
- {stat1_label}: {stats['listings_count']}
- {stat2_label}: {format_currency(stats['total_value'])}
- {stat3_label}: {format_currency(stats['avg_price'])}
- {models_label}: {top_models_str}

"""
    if specific_boat:
        plain_text += f"""{boat_analysis_title.upper()}
{boat_text.replace('<b>','').replace('</b>','')}
- Svalutazione: {specific_boat['depreciation']}% annuo
- Liquidita: {specific_boat['liquidity']}
- Prezzo medio: {format_currency(specific_boat['avg_price'])}

"""
    
    plain_text += f"""{pitch_title}
{pitch_text}
1. {point1}
2. {point2}
3. {point3}

{cta_intro}
Prenota qui: {calendly_link}

{signoff}
{signature.replace('<br>', ' ')}
"""
    
    return subject, plain_text, html

def send_test_email(to_email, smtp_user, smtp_pass):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Dati finti per il test
    stats = {
        'listings_count': 142,
        'total_value': 85400000,
        'avg_price': 601000,
        'top_models': ['Azimut 60', 'Ferretti 550', 'Sanlorenzo 72']
    }
    broker_name = "SuperYachts International"
    
    specific_boat = {
        "name": "Azimut 60",
        "year": 2018,
        "depreciation": 4.5,
        "liquidity": "Alta (Vendita in ~30 gg)",
        "avg_price": 950000
    }
    
    subject, plain_text, html_content = generate_html_email(broker_name, stats, specific_boat, lang='it')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email

    part1 = MIMEText(plain_text, 'plain')
    part2 = MIMEText(html_content, 'html')

    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email di test con nuovo layout inviata con successo a {to_email}")
        return True
    except Exception as e:
        print(f"❌ Errore durante l'invio dell'email: {e}")
        return False

if __name__ == "__main__":
    sender_email = "giorgio96rota@gmail.com"
    app_password = "itrjkodkvclwofzd"
    print("Pronto per inviare l'email di test HTML V2.")
    send_test_email(sender_email, sender_email, app_password)