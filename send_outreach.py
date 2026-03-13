import json
import requests
import time
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

# CONFIGURAZIONE
API_URL = 'http://localhost:8000/evaluate'
DATA_FILE = 'all_navisnet_brokers_full.json'
TRACKING_FILE = 'outreach_tracking.json'
SENDER_EMAIL = "giorgio96rota@gmail.com"
SENDER_NAME = "Giorgio Rota"
LIMIT_TODAY = 50 

COUNTRY_MAP = {
    'AL': 'Albania', 'AD': 'Andorra', 'AG': 'Antigua e Barbuda', 'AR': 'Argentina', 'AU': 'Australia',
    'AT': 'Austria', 'BS': 'Bahamas', 'BE': 'Belgio', 'BZ': 'Belize', 'BR': 'Brasile', 'BG': 'Bulgaria',
    'CA': 'Canada', 'CL': 'Cile', 'CN': 'Cina', 'CY': 'Cipro', 'CO': 'Colombia', 'CR': 'Costa Rica',
    'HR': 'Croazia', 'CU': 'Cuba', 'DK': 'Danimarca', 'EC': 'Ecuador', 'EG': 'Egitto', 'AE': 'Emirati Arabi Uniti',
    'EE': 'Estonia', 'FJ': 'Fiji', 'PH': 'Filippine', 'FI': 'Finlandia', 'FR': 'Francia', 'DE': 'Germania',
    'JP': 'Giappone', 'GI': 'Gibilterra', 'GR': 'Grecia', 'HK': 'Hong Kong', 'ID': 'Indonesia', 'IE': 'Irlanda',
    'IL': 'Israele', 'IT': 'Italia', 'JM': 'Giamaica', 'KW': 'Kuwait', 'LV': 'Lettonia', 'LB': 'Libano',
    'LT': 'Lituania', 'LU': 'Lussemburgo', 'MT': 'Malta', 'MA': 'Marocco', 'MX': 'Messico', 'MC': 'Monaco',
    'ME': 'Montenegro', 'NL': 'Olanda', 'NO': 'Norvegia', 'NZ': 'Nuova Zelanda', 'PA': 'Panama', 'PY': 'Paraguay',
    'PE': 'Peru', 'PL': 'Polonia', 'PT': 'Portogallo', 'PR': 'Porto Rico', 'QA': 'Qatar', 'GB': 'Regno Unito',
    'CZ': 'Repubblica Ceca', 'DO': 'Repubblica Dominicana', 'RO': 'Romania', 'RU': 'Russia', 'SC': 'Seychelles',
    'SG': 'Singapore', 'SK': 'Slovacchia', 'SI': 'Slovenia', 'ES': 'Spagna', 'US': 'Stati Uniti', 'ZA': 'Sudafrica',
    'SE': 'Svezia', 'CH': 'Svizzera', 'TH': 'Thailandia', 'TN': 'Tunisia', 'TR': 'Turchia', 'UA': 'Ucraina',
    'HU': 'Ungheria', 'UY': 'Uruguay', 'VG': 'Isole Vergini Britanniche', 'VI': 'Isole Vergini Americane'
}

COUNTRY_MAP_EN = {
    'AL': 'Albania', 'AD': 'Andorra', 'AG': 'Antigua and Barbuda', 'AR': 'Argentina', 'AU': 'Australia',
    'AT': 'Austria', 'BS': 'Bahamas', 'BE': 'Belgium', 'BZ': 'Belize', 'BR': 'Brazil', 'BG': 'Bulgaria',
    'CA': 'Canada', 'CL': 'Chile', 'CN': 'China', 'CY': 'Cyprus', 'CO': 'Colombia', 'CR': 'Costa Rica',
    'HR': 'Croatia', 'CU': 'Cuba', 'DK': 'Denmark', 'EC': 'Ecuador', 'EG': 'Egypt', 'AE': 'United Arab Emirates',
    'EE': 'Estonia', 'FJ': 'Fiji', 'PH': 'Philippines', 'FI': 'Finland', 'FR': 'France', 'DE': 'Germany',
    'JP': 'Japan', 'GI': 'Gibraltar', 'GR': 'Greece', 'HK': 'Hong Kong', 'ID': 'Indonesia', 'IE': 'Ireland',
    'IL': 'Israel', 'IT': 'Italy', 'JM': 'Jamaica', 'KW': 'Kuwait', 'LV': 'Latvia', 'LB': 'Lebanon',
    'LT': 'Lithuania', 'LU': 'Luxembourg', 'MT': 'Malta', 'MA': 'Morocco', 'MX': 'Mexico', 'MC': 'Monaco',
    'ME': 'Montenegro', 'NL': 'Netherlands', 'NO': 'Norway', 'NZ': 'New Zealand', 'PA': 'Panama', 'PY': 'Paraguay',
    'PE': 'Peru', 'PL': 'Poland', 'PT': 'Portugal', 'PR': 'Puerto Rico', 'QA': 'Qatar', 'GB': 'United Kingdom',
    'CZ': 'Czech Republic', 'DO': 'Dominican Republic', 'RO': 'Romania', 'RU': 'Russia', 'SC': 'Seychelles',
    'SG': 'Singapore', 'SK': 'Slovakia', 'SI': 'Slovenia', 'ES': 'Spain', 'US': 'United States', 'ZA': 'South Africa',
    'SE': 'Sweden', 'CH': 'Switzerland', 'TH': 'Thailand', 'TN': 'Tunisia', 'TR': 'Turkey', 'UA': 'Ukraine',
    'HU': 'Hungary', 'UY': 'Uruguay', 'VG': 'British Virgin Islands', 'VI': 'US Virgin Islands'
}

def translate_liquidity_en(status_it):
    mapping = {
        'Scarsità Estrema': 'Extreme Scarcity',
        'Bassa (Mercato Esclusivo)': 'Low (Exclusive Market)',
        'Normale (Buona Scambiabilità)': 'Normal (Good Tradability)',
        'Alta (Mercato Liquido)': 'High (Liquid Market)'
    }
    return mapping.get(status_it, status_it)

def get_best_valuation(boats):
    """Itera le barche del broker e restituisce la prima che ha dati di mercato solidi e 'sexy' per l'outreach."""
    best_fallback = None
    best_fallback_data = None
    for boat in boats:
        builder = boat['builder']
        model = boat['model']
        query_str = f"{builder} {model}"
        
        try:
            res = requests.get(f'{API_URL}?q={urllib.parse.quote(query_str)}', timeout=5)
            if res.status_code == 200:
                data = res.json()
                sample_size = data.get('sample_size', 0)
                val = data.get('valuation', {})
                depreciation = val.get('depreciation_percent', 0)
                
                # Cerchiamo la nazione estera
                countries = val.get('market_share_countries', [])
                has_foreign_opp = False
                if countries:
                    foreign = [c for c in countries if c['name'].upper() != 'IT' and c.get('avg_price', 0) > 0]
                    if foreign:
                        has_foreign_opp = True
                
                # CRITERI DI QUALITA' STRINGENTI
                # 1. Almeno 12 campioni (abbastanza liquido)
                # 2. Svalutazione > 0.5% (dato non nullo e interessante)
                # 3. Deve esserci un'opportunità estera da citare
                if sample_size >= 12 and depreciation > 0.5 and has_foreign_opp:
                    return boat, data
                
                if sample_size >= 5 and best_fallback is None:
                    best_fallback = boat
                    best_fallback_data = data
                
        except:
            continue
    return best_fallback, best_fallback_data

def generate_email_content(name, boat, api_data):
    builder_clean = str(boat['builder']).title().strip()
    model_clean = str(boat['model']).title().strip()
    price = boat['price']
    year = boat['year']
    
    val = api_data.get('valuation', {})
    depreciation_percent = round(val.get('depreciation_percent', 0), 1)
    liquidity_status_it = val.get('liquidity_status', 'Normale')
    liquidity_status_en = translate_liquidity_en(liquidity_status_it)
    
    countries = val.get('market_share_countries', [])
    best_country_name_full_it = None
    best_country_name_full_en = None
    best_country_price = 0
    
    if countries:
        # Filtriamo l'Italia per l'opportunità estera
        foreign_countries = [c for c in countries if c['name'].upper() != 'IT']
        if foreign_countries:
            best_country = sorted(foreign_countries, key=lambda x: x.get('avg_price', 0), reverse=True)[0]
            best_country_name = best_country['name']
            best_country_price = best_country['avg_price']
            best_country_name_full_it = COUNTRY_MAP.get(best_country_name.upper(), best_country_name)
            best_country_name_full_en = COUNTRY_MAP_EN.get(best_country_name.upper(), best_country_name)
    
    price_formatted = f'€ {price:,.0f}'.replace(',', '.')
    best_price_formatted = f'€ {best_country_price:,.0f}'.replace(',', '.')
    year_clean = int(year) if isinstance(year, float) else year
    
    subject = f'Analisi di mercato per il tuo {builder_clean} {model_clean} / Market analysis for your {builder_clean} {model_clean}'
    
    # HTML BODY
    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #334155;">
        <p>Buongiorno {name},</p>
        
        <p>in quanto partner Navisnet stiamo monitorando il posizionamento dei vostri annunci. In particolare, abbiamo analizzato il vostro <b>{builder_clean} {model_clean}</b> del {year_clean} a <b>{price_formatted}</b>.</p>
        
        <p>Abbiamo confrontato questo posizionamento con oltre 90.000 annunci attivi in Europa. Dal report emergono due metriche chiave per la trattativa:</p>
        
        <ul style="list-style-type: none; padding-left: 5px;">
            <li style="margin-bottom: 10px;">🔹 <b>Indice di svalutazione:</b> {depreciation_percent}% annuo.</li>
            <li style="margin-bottom: 10px;">🔹 <b>Liquidità:</b> E' un mercato classificato come <b>"{liquidity_status_it}"</b>.</li>
    """
    
    if best_country_name_full_it and best_country_price > 0:
        html_body += f'<li style="margin-bottom: 10px;">🔹 <b>Opportunità Estera:</b> In <b>{best_country_name_full_it}</b> la richiesta per questo modello ha un prezzo medio di <b>{best_price_formatted}</b>.</li>'
        
    html_body += f"""
        </ul>
        
        <p>Sappiamo bene che il problema principale per un broker è ridurre il tempo sul mercato e fornire all'armatore dati oggettivi per allineare le sue aspettative.</p>
        
        <p>Se volete accelerare la vendita con report matematici in tempo reale, <b>rispondete "Sì"</b> a questa email (o scrivetemi su WhatsApp al <b>+39 3454590116</b>) e vi invio gratuitamente il PDF con l'analisi completa dei competitor diretti per la vostra barca.</p>
        
        <p>Vi ricordo inoltre che, come nostri partner su Navisnet, i vostri annunci sono già visibili anche sul nostro marketplace europeo: <a href="https://www.batoo.it" style="color: #3b82f6; text-decoration: none; font-weight: bold;">www.batoo.it</a></p>
        
        <p>Un saluto,<br>
        <b>{SENDER_NAME}</b><br>
        Founder, Batoo</p>
        
        <br>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
        <br>
        
        <p style="color: #64748b;"><i>Dear {name},</i></p>
        
        <p style="color: #64748b;"><i>as a Navisnet partner we are monitoring the positioning of your listings. Specifically, we analyzed your <b>{year_clean} {builder_clean} {model_clean}</b> listed at <b>{price_formatted}</b>.</i></p>
        
        <p style="color: #64748b;"><i>We compared this positioning against over 90,000 active listings across Europe. The report highlights two key metrics for negotiations:</i></p>
        
        <ul style="list-style-type: none; padding-left: 5px; color: #64748b;">
            <li style="margin-bottom: 10px;">🔹 <b>Depreciation rate:</b> {depreciation_percent}% per year.</li>
            <li style="margin-bottom: 10px;">🔹 <b>Liquidity:</b> Classified as a <b>"{liquidity_status_en}"</b> market.</li>
    """

    if best_country_name_full_en and best_country_price > 0:
        html_body += f'<li style="margin-bottom: 10px;">🔹 <b>International Opportunity:</b> In <b>{best_country_name_full_en}</b>, demand for this model shows an average asking price of <b>{best_price_formatted}</b>.</li>'
        
    html_body += f"""
        </ul>
        
        <p style="color: #64748b;"><i>We know the main challenge for brokers is reducing time-on-market and providing owners with objective data to align their price expectations.</i></p>
        
        <p style="color: #64748b;"><i>If you want to speed up the sale using real-time mathematical reports, <b>simply reply "Yes"</b> to this email (or message me on WhatsApp at <b>+39 3454590116</b>), and I will send you a free PDF with the complete competitor analysis for your boat.</i></p>
        
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
        print("Uso: python send_outreach.py <app_password>")
        sys.exit(1)
    
    password = sys.argv[1]
    
    with open(DATA_FILE, 'r') as f:
        all_brokers = json.load(f)
    
    tracking = load_tracking()
    pending_brokers = {k: v for k, v in all_brokers.items() if k not in tracking or tracking[k]['status'] != 'sent'}
    
    if not pending_brokers:
        print("Tutte le email sono già state inviate!")
        return

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, password)
        print("Login Gmail OK!")
    except Exception as e:
        print(f"Errore Login: {e}")
        return

    sent_count = 0
    for name, data in pending_brokers.items():
        if sent_count >= LIMIT_TODAY:
            break
            
        print(f"[{sent_count+1}/{LIMIT_TODAY}] Ricerca barca ideale per {name}...")
        
        # Cerchiamo tra tutte le sue barche quella che restituisce i dati migliori
        boat, api_data = get_best_valuation(data['boats'])
        
        if boat and api_data:
            subject, body = generate_email_content(name, boat, api_data)
            try:
                send_email(server, data['email'], subject, body)
                tracking[name] = {
                    "email": data['email'],
                    "boat": f"{boat['builder']} {boat['model']}",
                    "sent_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "sent"
                }
                save_tracking(tracking)
                print(f" -> Email inviata usando: {boat['builder']} {boat['model']}")
                sent_count += 1
                if sent_count < LIMIT_TODAY:
                    time.sleep(30)
            except Exception as e:
                print(f" -> Errore invio: {e}")
        else:
            print(f" -> Saltato: Nessuna barca di questo broker ha dati sufficienti in DB.")
            tracking[name] = {"status": "skipped", "reason": "no_rich_data"}
            save_tracking(tracking)

    server.quit()
    print(f"Sessione completata. Inviate {sent_count} email.")

if __name__ == "__main__":
    main()
