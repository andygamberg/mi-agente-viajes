import os
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
DELEGATED_EMAIL = 'misviajes@gamberg.com.ar'

def get_gmail_service():
    # Leer credenciales desde variable de entorno o archivo
    creds_json = os.getenv('GMAIL_CREDENTIALS')
    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
    else:
        credentials = service_account.Credentials.from_service_account_file(
            'gmail-credentials.json',
            scopes=SCOPES
        )
    
    delegated_credentials = credentials.with_subject(DELEGATED_EMAIL)
    service = build('gmail', 'v1', credentials=delegated_credentials)
    return service
    emails = fetch_unread_emails()
    
    if emails:
        print(f'\n📊 Resumen:')
        for email in emails:
            print(f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            print(f'Asunto: {email["subject"]}')
            print(f'De: {email["from"]}')
            print(f'Body (primeros 200 chars):')
            print(email["body"][:200])
