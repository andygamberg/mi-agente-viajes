import os
import json
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import re
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SERVICE_ACCOUNT_FILE = 'gmail-credentials.json'
DELEGATED_EMAIL = 'misviajes@gamberg.com.ar'

def get_gmail_service():
    """Crea servicio Gmail con service account"""
    creds_json = os.getenv("GMAIL_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        credentials = service_account.Credentials.from_service_account_file("gmail-credentials.json", scopes=SCOPES)
    delegated_credentials = credentials.with_subject(DELEGATED_EMAIL)
    service = build("gmail", "v1", credentials=delegated_credentials)
    return service

def fetch_unread_emails():
    """Lee emails no leídos del inbox"""
    service = get_gmail_service()
    
    # Buscar emails no leídos
    results = service.users().messages().list(
        userId='me',
        q='is:unread',
        maxResults=10
    ).execute()
    
    messages = results.get('messages', [])
    
    if not messages:
        print('No hay emails nuevos')
        return []
    
    print(f'📧 Encontrados {len(messages)} emails nuevos')
    
    emails = []
    for msg in messages:
        # Obtener email completo
        message = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()
        
        # Extraer info
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # Extraer body
        body = get_email_body(message['payload'])
        
        emails.append({
            'id': msg['id'],
            'subject': subject,
            'from': from_email,
            'date': date,
            'body': body
        })
        
        print(f'  ✉️  {subject[:50]}... from {from_email}')
    
    return emails

def get_email_body(payload):
    """Extrae el texto del email"""
    body = ''
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif 'parts' in part:
                body = get_email_body(part)
                if body:
                    break
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    
    return body

def mark_as_read(email_id):
    """Marca email como leído"""
    service = get_gmail_service()
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()
    print(f'✅ Email {email_id} marcado como leído')

if __name__ == '__main__':
    print('🔍 Buscando emails nuevos en misviajes@gamberg.com.ar...')
    emails = fetch_unread_emails()
    
    if emails:
        print(f'\n📊 Resumen:')
        for email in emails:
            print(f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            print(f'Asunto: {email["subject"]}')
            print(f'De: {email["from"]}')
            print(f'Body (primeros 200 chars):')
            print(email["body"][:200])
