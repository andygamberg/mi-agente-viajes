import os
import json
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import re
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
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

def get_attachments(service, message_id, payload):
    """Extrae PDFs adjuntos del email"""
    attachments = []
    
    def process_parts(parts):
        for part in parts:
            filename = part.get('filename', '')
            mime_type = part.get('mimeType', '')
            
            # Si es PDF
            if mime_type == 'application/pdf' or filename.lower().endswith('.pdf'):
                if 'body' in part and 'attachmentId' in part['body']:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(
                        userId='me',
                        messageId=message_id,
                        id=att_id
                    ).execute()
                    
                    data = base64.urlsafe_b64decode(att['data'])
                    attachments.append({
                        'filename': filename,
                        'data': data
                    })
                    print(f'    �� PDF encontrado: {filename}')
            
            # Recursivo para parts anidados
            if 'parts' in part:
                process_parts(part['parts'])
    
    if 'parts' in payload:
        process_parts(payload['parts'])
    
    return attachments

def extract_text_from_pdf(pdf_data):
    """Extrae texto de un PDF en memoria"""
    try:
        import io
        # Intentar con PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(pdf_data))
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            return text
        except ImportError:
            # Intentar con pdfplumber
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() + '\n'
                return text
    except Exception as e:
        print(f'    ⚠️ Error extrayendo PDF: {e}')
        return ''

def fetch_emails_with_attachments():
    """Lee emails no leídos incluyendo PDFs adjuntos"""
    service = get_gmail_service()
    
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
        message = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()
        
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # Extraer body
        body = get_email_body(message['payload'])
        
        # Extraer PDFs adjuntos
        attachments = get_attachments(service, msg['id'], message['payload'])
        
        # Extraer texto de PDFs
        pdf_texts = []
        for att in attachments:
            pdf_text = extract_text_from_pdf(att['data'])
            if pdf_text:
                pdf_texts.append(pdf_text)
        
        # Combinar body + texto de PDFs
        full_content = body
        if pdf_texts:
            full_content += '\n\n--- CONTENIDO DE PDFs ADJUNTOS ---\n\n'
            full_content += '\n\n---\n\n'.join(pdf_texts)
        
        emails.append({
            'id': msg['id'],
            'subject': subject,
            'from': from_email,
            'date': date,
            'body': full_content,
            'has_attachments': len(attachments) > 0
        })
        
        att_info = f' (+ {len(attachments)} PDF)' if attachments else ''
        print(f'  ✉️  {subject[:50]}...{att_info}')
    
    return emails
