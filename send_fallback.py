import json
import requests
import time
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

API_URL = 'http://localhost:8000/evaluate'
DATA_FILE = 'all_navisnet_brokers_full.json'
TRACKING_FILE = 'outreach_tracking.json'
SENDER_EMAIL = "giorgio96rota@gmail.com"
SENDER_NAME = "Giorgio Rota"

def generate_fallback_email_content(name, api_data):
    val = api_data.get('valuation', {})
    depreciation_percent = round(val.get('depreciation_percent', 0), 1)
    liquidity_status_it = val.get('liquidity_status', 'Normale')
    
    mapping = {
        'Scarsità Estrema': 'Extreme Scarcity',
        'Bassa (Mercato Esclusivo)': 'Low (Exclusive Market)',
        'Normale (Buona Scambiabilità)': 'Normal (Good Tradability)',
        'Alta (Mercato Liquido)': 'High (Liquid Market)'
    }
    liquidity_status_en = mapping.get(liquidity_status_it, liquidity_status_it)
    
    best_country_name_full_it = "Germania"
    best_country_name_full_en = "Germany"
    best_country_price = 268227
    best_price_formatted = f'€ {best_country_price:,.0f}'.replace(',', '.')
    
    subject = f'Esempio di Analisi di mercato: Axopar 37 / Market analysis example'
    
    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #334155;">
        <p>Buongiorno {name},</p>
        
        <p>in quanto partner Navisnet, supportiamo i broker fornendo dati di mercato oggettivi per allineare le aspettative degli armatori e ridurre il tempo di vendita.</p>
        
        <p>Per farvi un esempio di cosa possiamo estrapolare dal nostro algoritmo che scansiona oltre 95.000 annunci in tutta Europa, abbiamo analizzato uno dei modelli più richiesti sul mercato: l'<b>Axopar 37</b>.</p>
        
        <p>Ecco le metriche chiave che emergono dal nostro database in tempo reale:</p>
        
        <ul style="list-style-type: none; padding-left: 5px;">
            <li style="margin-bottom: 10px;">🔹 <b>Indice di svalutazione:</b> {depreciation_percent}% annuo.</li>
            <li style="margin-bottom: 10px;">🔹 <b>Liquidità:</b> E' un mercato classificato come <b>"{liquidity_status_it}"</b>.</li>
            <li style="margin-bottom: 10px;">🔹 <b>Opportunità Estera:</b> In <b>{best_country_name_full_it}</b> la richiesta per questo modello ha un prezzo medio di <b>{best_price_formatted}</b>.</li>
        </ul>
        
        <p>Sappiamo bene che il problema principale per un broker è avere argomentazioni matematiche durante le trattative o in fase di acquisizione mandato.</p>
        
        <p>Se vi interessa ricevere gratuitamente un report PDF di questo tipo <b>su una specifica barca che avete a listino (o che state acquisendo)</b>, rispondete "Sì" a questa email indicandomi cantiere e modello, o scrivetemi su WhatsApp al <b>+39 3454590116</b>.</p>
        
        <p>Vi ricordo inoltre che, come nostri partner su Navisnet, i vostri annunci sono già visibili anche sul nostro marketplace europeo: <a href="https://www.batoo.it" style="color: #3b82f6; text-decoration: none; font-weight: bold;">www.batoo.it</a></p>
        
        <p>Un saluto,<br>
        <b>{SENDER_NAME}</b><br>
        Founder, Batoo</p>
        
        <br>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
        <br>
        
        <p style="color: #64748b;"><i>Dear {name},</i></p>
        
        <p style="color: #64748b;"><i>as a Navisnet partner, we support brokers by providing objective market data to align owner expectations and reduce time-on-market.</i></p>
        
        <p style="color: #64748b;"><i>To give you an example of what our algorithm can extract by scanning over 95,000 active listings across Europe, we analyzed one of the most requested models: the <b>Axopar 37</b>.</i></p>
        
        <p style="color: #64748b;"><i>Here are the key metrics emerging from our real-time database:</i></p>
        
        <ul style="list-style-type: none; padding-left: 5px; color: #64748b;">
            <li style="margin-bottom: 10px;">🔹 <b>Depreciation rate:</b> {depreciation_percent}% per year.</li>
            <li style="margin-bottom: 10px;">🔹 <b>Liquidity:</b> Classified as a <b>"{liquidity_status_en}"</b> market.</li>
            <li style="margin-bottom: 10px;">🔹 <b>International Opportunity:</b> In <b>{best_country_name_full_en}</b>, demand for this model shows an average asking price of <b>{best_price_formatted}</b>.</li>
        </ul>
        
        <p style="color: #64748b;"><i>We know the main challenge for brokers is having mathematical arguments during negotiations or when acquiring new listings.</i></p>
        
        <p style="color: #64748b;"><i>If you want to receive a free PDF report like this <b>for a specific boat you have listed (or are acquiring)</b>, simply reply "Yes" to this email with the builder and model, or message me on WhatsApp at <b>+39 3454590116</b>.</i></p>
        
        <p style="color: #64748b;"><i>I also want to remind you that, as our partner on Navisnet, your listings are already visible on our European marketplace: <a href="https://www.batoo.it" style="color: #3b82f6; text-decoration: none; font-weight: bold;">www.batoo.it</a></i></p>
        
        <p style="color: #64748b;"><i>Best regards,<br>
        <b>{SENDER_NAME}</b><br>
        Founder, Batoo</i></p>
    </body>
    </html>
    """
    return subject, html_body

def send_email(server, recipient_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    server.send_message(msg)

def load_tracking():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tracking(tracking):
    with open(TRACKING_FILE, 'w') as f:
        json.dump(tracking, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Uso: python send_fallback.py <app_password>")
        sys.exit(1)
    
    password = sys.argv[1]
    
    with open(DATA_FILE, 'r') as f:
        all_brokers = json.load(f)
    
    tracking = load_tracking()
    
    # Selezioniamo SOLO i broker che sono nel tracking con status "skipped"
    skipped_brokers = {k: all_brokers[k] for k, v in tracking.items() if v.get('status') == 'skipped' and k in all_brokers}
    
    if not skipped_brokers:
        print("Nessun broker da contattare con email di fallback.")
        return

    # Recuperiamo i dati dell'Axopar 37 una volta sola
    print("Recupero dati Axopar 37 dall'API...")
    try:
        res = requests.get(f'{API_URL}?q=Axopar%2037', timeout=5)
        api_data = res.json()
    except Exception as e:
        print(f"Errore API: {e}")
        return

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, password)
        print("Login Gmail OK!")
    except Exception as e:
        print(f"Errore Login: {e}")
        return

    sent_count = 0
    for name, data in skipped_brokers.items():
        print(f"Invio email fallback (Axopar 37) a {name}...")
        
        subject, body = generate_fallback_email_content(name, api_data)
        try:
            send_email(server, data['email'], subject, body)
            tracking[name] = {
                "email": data['email'],
                "boat": "Axopar 37 (Fallback)",
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "fallback_sent"
            }
            save_tracking(tracking)
            print(" -> Inviata con successo!")
            sent_count += 1
            time.sleep(30) # Pausa tra un invio e l'altro per non farci bloccare da Gmail
        except Exception as e:
            print(f" -> Errore invio: {e}")

    server.quit()
    print(f"Sessione completata. Inviate {sent_count} email di fallback.")

if __name__ == "__main__":
    main()
