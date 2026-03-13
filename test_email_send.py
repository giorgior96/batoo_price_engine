import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
import sys

SENDER_EMAIL = "giorgio@batoo.it"
SENDER_NAME = "Giorgio Rota"

def main():
    print(f"--- TEST INVIO EMAIL (MICROSOFT O365) ---")
    print(f"Mittente: {SENDER_EMAIL}")
    
    password = getpass.getpass(prompt='Inserisci la password (o App Password) per giorgio@batoo.it: ')
    
    if not password:
        print("Password vuota. Uscita.")
        sys.exit(1)
        
    try:
        print("Connessione a smtp.office365.com (Porta 587)...")
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.set_debuglevel(1) # Mostra i log di comunicazione per debug
        server.starttls()
        
        print("Tentativo di login...")
        server.login(SENDER_EMAIL, password)
        print("Login effettuato con successo!")
        
        subject = "TEST: Batoo Price Engine - Email di verifica"
        body = "Questa è un'email di test inviata dallo script Python per verificare la configurazione SMTP di Microsoft Office 365.\n\nSe ricevi questa mail, la configurazione è corretta!"
        
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = SENDER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Invio email di test a {SENDER_EMAIL}...")
        server.send_message(msg)
        print("Email inviata con successo! Controlla la tua casella di posta (anche lo spam).")
        
        server.quit()
    except Exception as e:
        print(f"\nERRORE DURANTE L'INVIO: {e}")
        print("\nNote per risolvere:")
        print("- Verifica che la password (o App Password) sia corretta.")
        print("- Assicurati che l'opzione 'SMTP Autenticato' sia abilitata per la tua utenza nel pannello Admin di Microsoft 365.")

if __name__ == "__main__":
    main()
