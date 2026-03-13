import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
import sys

SENDER_EMAIL = "giorgio96rota@gmail.com"
SENDER_NAME = "Giorgio Rota"

def main():
    print(f"--- TEST INVIO EMAIL (GMAIL) ---")
    print(f"Mittente: {SENDER_EMAIL}")
    
    password = getpass.getpass(prompt='Inserisci la Password per le app (16 lettere): ')
    
    if not password:
        print("Password vuota. Uscita.")
        sys.exit(1)
        
    try:
        print("Connessione a smtp.gmail.com (Porta 465)...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        
        print("Tentativo di login...")
        server.login(SENDER_EMAIL, password)
        print("Login effettuato con successo!")
        
        subject = "TEST: Batoo Price Engine - Verifica Gmail"
        body = "Questa è un'email di test inviata dallo script Python per verificare la configurazione SMTP di Gmail.\n\nSe ricevi questa mail, siamo pronti!"
        
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = SENDER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Invio email di test a {SENDER_EMAIL}...")
        server.send_message(msg)
        print("Email inviata con successo! Controlla la tua casella di posta.")
        
        server.quit()
    except Exception as e:
        print(f"\nERRORE DURANTE L'INVIO: {e}")
        print("\nNote per risolvere:")
        print("- Assicurati di usare la Password per le app (16 caratteri) e non la tua password normale.")
        print("- Verifica che la 'Verifica in due passaggi' sia attiva sul tuo account Google.")

if __name__ == "__main__":
    main()
