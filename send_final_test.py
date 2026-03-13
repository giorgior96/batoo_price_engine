import json
import requests
import time
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

# CONFIGURAZIONE TEST
API_URL = 'http://localhost:8000/evaluate'
SENDER_EMAIL = "giorgio96rota@gmail.com"
SENDER_NAME = "Giorgio Rota"
TEST_RECIPIENT = "giorgio@batoo.it"
PASSWORD_APP = "itrjkodkvclwofzd"

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

def generate_test_email():
    name = "Test Broker (Timone Yachts)"
    builder_clean = "Custom Line"
    model_clean = "Navetta 33"
    price = 11990000
    year_clean = 2019
    
    query_str = f'{builder_clean} {model_clean}'
    res = requests.get(f'{API_URL}?q={urllib.parse.quote(query_str)}')
    api_data = res.json()
    
    val = api_data.get('valuation', {})
    depreciation_percent = round(val.get('depreciation_percent', 0), 1)
    liquidity_status_it = val.get('liquidity_status', 'Normale')
    liquidity_status_en = translate_liquidity_en(liquidity_status_it)
    
    countries = val.get('market_share_countries', [])
    best_country_name_full_it = "Grecia"
    best_country_name_full_en = "Greece"
    best_country_price = 10900000
    
    price_formatted = f'€ {price:,.0f}'.replace(',', '.')
    best_price_formatted = f'€ {best_country_price:,.0f}'.replace(',', '.')
    
    subject = f'TEST HTML: Analisi di mercato per il tuo {builder_clean} {model_clean}'
    
    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #334155;">
        <p>Buongiorno {name},</p>
        
        <p>in quanto partner Navisnet stiamo monitorando il posizionamento dei vostri annunci. In particolare, abbiamo analizzato il vostro <b>{builder_clean} {model_clean}</b> del {year_clean} a <b>{price_formatted}</b>.</p>
        
        <p>Abbiamo confrontato questo posizionamento con oltre 90.000 annunci attivi in Europa. Dal report emergono due metriche chiave per la trattativa:</p>
        
        <ul style="list-style-type: none; padding-left: 5px;">
            <li style="margin-bottom: 10px;">🔹 <b>Indice di svalutazione:</b> {depreciation_percent}% annuo.</li>
            <li style="margin-bottom: 10px;">🔹 <b>Liquidità:</b> E' un mercato classificato come <b>"{liquidity_status_it}"</b>.</li>
            <li style="margin-bottom: 10px;">🔹 <b>Opportunità Estera:</b> In <b>{best_country_name_full_it}</b> la richiesta per questo modello ha un prezzo medio di <b>{best_price_formatted}</b>.</li>
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
            <li style="margin-bottom: 10px;">🔹 <b>International Opportunity:</b> In <b>{best_country_name_full_en}</b>, demand for this model shows an average asking price of <b>{best_price_formatted}</b>.</li>
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

def send_test():
    subject, html_body = generate_test_email()
    msg = MIMEMultipart()
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = TEST_RECIPIENT
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, PASSWORD_APP)
        server.send_message(msg)
        server.quit()
        print(f"Email di test inviata con successo a {TEST_RECIPIENT}")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    send_test()
