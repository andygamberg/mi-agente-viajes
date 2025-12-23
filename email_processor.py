import os
import json
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import re
from email.mime.text import MIMEText

# ACTUALIZADO: Agregado gmail.send para enviar emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]
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


def send_email(to_email, subject, body_html):
    """
    Envía un email usando Gmail API
    
    Args:
        to_email: Dirección destino
        subject: Asunto del email
        body_html: Contenido HTML del email
    
    Returns:
        dict con resultado o None si falla
    """
    try:
        service = get_gmail_service()
        
        # Crear mensaje MIME
        message = MIMEText(body_html, 'html')
        message['to'] = to_email
        message['from'] = f'Mis Viajes <{DELEGATED_EMAIL}>'
        message['subject'] = subject
        
        # Encodear en base64
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Enviar
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        
        print(f'✅ Email enviado a {to_email}: {result.get("id")}')
        return result
        
    except Exception as e:
        print(f'❌ Error enviando email a {to_email}: {e}')
        import traceback
        traceback.print_exc()
        return None


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
                    print(f'    📎 PDF encontrado: {filename}')
            
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

# Keywords que indican que un email puede contener reservas de viaje
TRAVEL_KEYWORDS = [
    # Confirmaciones genéricas
    'confirmation', 'confirmación', 'confirma', 'booking', 'reservation', 'reserva',
    'itinerary', 'itinerario', 'e-ticket', 'eticket', 'receipt', 'recibo',
    # Vuelos
    'vuelo', 'flight', 'boarding', 'embarque', 'check-in', 'checkin',
    'aeropuerto', 'airport', 'airline', 'aerolinea',
    # Hoteles
    'hotel', 'hospedaje', 'alojamiento', 'habitación', 'room', 'checkout', 'check-out',
    # Otros transportes
    'crucero', 'cruise', 'ferry', 'tren', 'train', 'bus', 'transfer',
    # Autos
    'rental', 'alquiler', 'car rental', 'rent a car',
    # Códigos de reserva (patrones comunes)
    'PNR', 'locator', 'localizador', 'código de reserva', 'booking reference',
]

# Keywords que indican que NO es una reserva (para filtrar falsos positivos)
EXCLUDE_KEYWORDS = [
    'unsubscribe', 'newsletter', 'promoción', 'oferta especial', 'password reset',
    'verify your email', 'confirma tu email', 'account created',
]


def email_parece_reserva(subject, body, attachment_names=None):
    """
    Pre-filtro local para determinar si un email parece contener una reserva.
    Retorna True si vale la pena enviarlo a Claude.

    Args:
        subject: Asunto del email
        body: Cuerpo del email (primeros 2000 chars)
        attachment_names: Lista opcional de nombres de archivos adjuntos
    """
    contenido = (subject + ' ' + body[:2000]).lower()

    # Incluir nombres de adjuntos si están disponibles
    if attachment_names:
        contenido += ' ' + ' '.join(attachment_names).lower()

    # Excluir si tiene keywords de exclusión
    for kw in EXCLUDE_KEYWORDS:
        if kw.lower() in contenido:
            return False

    # Incluir si tiene keywords de viaje
    for kw in TRAVEL_KEYWORDS:
        if kw.lower() in contenido:
            return True

    return False


def fetch_emails_with_attachments():
    """Lee emails no leídos incluyendo PDFs adjuntos"""
    service = get_gmail_service()

    # Query con keywords de viaje para capturar reenvíos
    # Esto es más amplio que filtrar por remitente
    keyword_query = ' OR '.join([f'"{kw}"' for kw in [
        'confirmation', 'booking', 'itinerary', 'vuelo', 'flight',
        'hotel', 'reserva', 'e-ticket', 'check-in', 'crucero', 'cruise'
    ]])
    query = f'is:unread ({keyword_query})'

    results = service.users().messages().list(
        userId='me',
        q=query,
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
