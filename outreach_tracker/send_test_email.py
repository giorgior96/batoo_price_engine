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

def generate_html_email(broker_name, stats, lang='it'):
    top_models_str = ", ".join(stats['top_models'][:3])
    
    if lang == 'it':
        subject = f"Analisi portafoglio barche per {broker_name} 📊"
        title = f"Analisi Portafoglio: {broker_name}"
        intro = f"Abbiamo analizzato il vostro portafoglio di imbarcazioni online (aggregando i dati da vari portali) e siamo rimasti impressionati."
        
        stat1_label = "Annunci Attivi"
        stat2_label = "Valore Portafoglio"
        stat3_label = "Prezzo Medio"
        
        models_label = "Modelli più frequenti:"
        
        pitch_title = "Scopri Batoo Analytics 🚀"
        pitch_text = "Abbiamo sviluppato un motore di intelligenza artificiale che monitora costantemente il mercato nautico europeo. Il nostro strumento vi permette di:"
        point1 = "Valutare istantaneamente il corretto prezzo di mercato (e la svalutazione) di qualsiasi modello."
        point2 = "Monitorare la liquidità di mercato e il tempo medio di vendita dei vostri top brand."
        point3 = "Scoprire le variazioni di prezzo dei vostri competitor in tempo reale."
        
        cta_text = "Sareste aperti a fare una veloce demo di 10 minuti la prossima settimana per mostrarvi come questo tool può aiutarvi ad acquisire mandati al giusto prezzo e chiudere vendite più velocemente?"
        signoff = "Un cordiale saluto,"
        signature = "Giorgio<br>Team Batoo Analytics"
    else:
        subject = f"Yacht portfolio analysis for {broker_name} 📊"
        title = f"Portfolio Analysis: {broker_name}"
        intro = f"We analyzed your online yacht portfolio across multiple portals and were very impressed."
        
        stat1_label = "Active Listings"
        stat2_label = "Est. Portfolio Value"
        stat3_label = "Average Price"
        
        models_label = "Top models in portfolio:"
        
        pitch_title = "Discover Batoo Analytics 🚀"
        pitch_text = "We have developed an AI-driven software that constantly monitors the European yachting market. Our tool allows you to:"
        point1 = "Instantly evaluate the correct market price (and depreciation) of any model."
        point2 = "Monitor market liquidity and average selling times for your top brands."
        point3 = "Track your competitors' price changes in real time."
        
        cta_text = "Would you be open to a quick 10-minute demo next week to see how this tool can help you secure mandates at the right price and close sales faster?"
        signoff = "Best regards,"
        signature = "Giorgio<br>Batoo Analytics Team"

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
                background-color: #f9fafa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            .header {{
                background-color: #0f172a;
                padding: 30px 40px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                margin: 0;
                font-size: 24px;
                font-weight: 600;
                letter-spacing: -0.5px;
            }}
            .content {{
                padding: 40px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #1e293b;
            }}
            .stats-grid {{
                display: flex;
                justify-content: space-between;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin: 25px 0;
            }}
            .stat-box {{
                text-align: center;
                flex: 1;
            }}
            .stat-box:not(:last-child) {{
                border-right: 1px solid #cbd5e1;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: 700;
                color: #0284c7;
                margin-bottom: 5px;
            }}
            .stat-label {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #64748b;
                font-weight: 600;
            }}
            .models {{
                background: #f0fdf4;
                border-left: 4px solid #22c55e;
                padding: 15px 20px;
                margin-bottom: 30px;
                border-radius: 0 4px 4px 0;
            }}
            .models-label {{
                font-weight: 600;
                color: #166534;
                margin-bottom: 5px;
                font-size: 14px;
            }}
            .models-text {{
                color: #15803d;
                font-size: 15px;
            }}
            .pitch-title {{
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 15px;
            }}
            .features {{
                padding-left: 20px;
                margin-bottom: 30px;
            }}
            .features li {{
                margin-bottom: 10px;
                color: #475569;
            }}
            .cta {{
                background-color: #f1f5f9;
                padding: 20px;
                border-radius: 8px;
                font-weight: 500;
                color: #334155;
                margin-bottom: 30px;
                border: 1px solid #e2e8f0;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                color: #64748b;
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
                <p>{intro}</p>
                
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-value">{stats['listings_count']}</div>
                        <div class="stat-label">{stat1_label}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{format_currency(stats['total_value'])}</div>
                        <div class="stat-label">{stat2_label}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{format_currency(stats['avg_price'])}</div>
                        <div class="stat-label">{stat3_label}</div>
                    </div>
                </div>
                
                <div class="models">
                    <div class="models-label">{models_label}</div>
                    <div class="models-text">{top_models_str}</div>
                </div>

                <div class="pitch-title">{pitch_title}</div>
                <p>{pitch_text}</p>
                <ul class="features">
                    <li>{point1}</li>
                    <li>{point2}</li>
                    <li>{point3}</li>
                </ul>

                <div class="cta">
                    {cta_text}
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
    
    # We also return a plain text version for email clients that don't support HTML
    plain_text = f"""{title}

Gentile team di {broker_name},

{intro}

STATISTICHE RILEVATE:
- {stat1_label}: {stats['listings_count']}
- {stat2_label}: {format_currency(stats['total_value'])}
- {stat3_label}: {format_currency(stats['avg_price'])}
- {models_label}: {top_models_str}

{pitch_title}
{pitch_text}
1. {point1}
2. {point2}
3. {point3}

{cta_text}

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
    
    subject, plain_text, html_content = generate_html_email(broker_name, stats, lang='it')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email

    # Mettiamo prima il testo e poi l'HTML
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
        print(f"✅ Email di test inviata con successo a {to_email}")
        return True
    except Exception as e:
        print(f"❌ Errore durante l'invio dell'email: {e}")
        return False

if __name__ == "__main__":
    sender_email = "giorgio96rota@gmail.com"
    app_password = "itrjkodkvclwofzd" # Found in send_final_test.py
    
    print("Pronto per inviare l'email di test HTML.")
    send_test_email(sender_email, sender_email, app_password)
