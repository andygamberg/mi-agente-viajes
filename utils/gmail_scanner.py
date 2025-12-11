"""
Gmail Scanner - Mi Agente Viajes
MVP14b: Escanea emails de aerolíneas/agencias y extrae reservas
MVP14e: Custom senders por usuario
"""
import base64
import re
import uuid
import json as json_lib
from datetime import datetime, timedelta
from googleapiclient.discovery import build

from models import db, Viaje, EmailConnection, User
from utils.claude import extraer_info_con_claude
from blueprints.gmail_oauth import get_gmail_credentials

# Máximo emails por scan (evita timeout de 60s)
MAX_EMAILS_PER_SCAN = 5

# ============================================
# WHITELIST (~150 dominios)
# ============================================

WHITELIST_DOMAINS = [
    # Sudamérica
    'latam.com', 'lan.com', 'tam.com.br', 'aerolineas.com.ar',
    'gol.com.br', 'azul.com.br', 'avianca.com', 'copa.com',
    'jetsmart.com', 'flybondi.com', 'skyairline.com', 'wingo.com',
    # Norteamérica
    'aa.com', 'americanairlines.com', 'united.com', 'delta.com',
    'southwest.com', 'jetblue.com', 'alaskaair.com', 'spirit.com',
    'aircanada.com', 'westjet.com', 'aeromexico.com', 'volaris.com',
    # Europa
    'iberia.com', 'aireuropa.com', 'vueling.com', 'airfrance.com',
    'lufthansa.com', 'swiss.com', 'austrian.com', 'britishairways.com',
    'ba.com', 'virginatlantic.com', 'klm.com', 'brusselsairlines.com',
    'flytap.com', 'tapportugal.com', 'flysas.com', 'finnair.com',
    'norwegian.com', 'icelandair.com', 'lot.com', 'aegeanair.com',
    'turkishairlines.com', 'thy.com', 'aeroflot.com', 'aerlingus.com',
    # Low cost Europa
    'ryanair.com', 'easyjet.com', 'wizzair.com', 'eurowings.com',
    'volotea.com', 'transavia.com', 'level.com', 'condor.com',
    # Asia/Medio Oriente
    'emirates.com', 'etihad.com', 'qatarairways.com', 'saudia.com',
    'flydubai.com', 'egyptair.com', 'ethiopianairlines.com',
    'airindia.com', 'singaporeair.com', 'thaiairways.com',
    'malaysiaairlines.com', 'cathaypacific.com', 'airasia.com',
    'ana.co.jp', 'jal.co.jp', 'koreanair.com', 'airchina.com',
    'qantas.com', 'virginaustralia.com', 'airnewzealand.com',
    # OTAs
    'booking.com', 'expedia.com', 'kayak.com', 'skyscanner.com',
    'tripadvisor.com', 'priceline.com', 'hotels.com', 'agoda.com',
    'trip.com', 'kiwi.com', 'momondo.com', 'opodo.com', 'edreams.com',
    'despegar.com', 'decolar.com', 'almundo.com', 'avantrip.com',
    'turismocity.com', 'bestday.com', 'atrapalo.com', 'rumbo.es',
]


def is_whitelisted_sender(email_from, user_id=None):
    """
    Verifica si remitente está en whitelist global o custom del usuario.
    
    Args:
        email_from: Header "From" del email
        user_id: ID del usuario para chequear custom senders (opcional)
    
    Returns:
        bool: True si el remitente está permitido
    """
    if not email_from:
        return False
    
    email_from_lower = email_from.lower()
    
    # Extraer email y dominio
    match = re.search(r'[\w\.-]+@([\w\.-]+)', email_from_lower)
    if not match:
        return False
    
    full_email = match.group(0)  # email completo
    domain = match.group(1)       # solo dominio
    
    # 1. Chequear whitelist global por dominio
    if any(domain.endswith(w) for w in WHITELIST_DOMAINS):
        return True
    
    # 2. Chequear custom senders del usuario
    if user_id:
        user = User.query.get(user_id)
        if user:
            custom_senders = user.get_custom_senders()
            for sender in custom_senders:
                sender = sender.strip().lower()
                if not sender:
                    continue
                # Si empieza con @, es un dominio
                if sender.startswith('@'):
                    if domain.endswith(sender[1:]):
                        return True
                # Si no, es un email completo
                elif full_email == sender:
                    return True
    
    return False


def search_travel_emails(service, days_back=30):
    """Busca emails de viajes"""
    top_domains = WHITELIST_DOMAINS[:20]
    query = f"({' OR '.join(f'from:@{d}' for d in top_domains)})"
    after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    query += f" after:{after}"
    
    try:
        results = service.users().messages().list(
            userId='me', q=query, maxResults=30
        ).execute()
        return [m['id'] for m in results.get('messages', [])]
    except Exception as e:
        print(f"Error searching: {e}")
        return []


def get_email_content(service, msg_id):
    """Obtiene contenido de email"""
    try:
        msg = service.users().messages().get(
            userId='me', id=msg_id, format='full'
        ).execute()
        
        headers = msg.get('payload', {}).get('headers', [])
        data = {'id': msg_id, 'from': None, 'subject': None, 'body': ''}
        
        for h in headers:
            if h['name'].lower() == 'from':
                data['from'] = h['value']
            elif h['name'].lower() == 'subject':
                data['subject'] = h['value']
        
        data['body'] = extract_body(msg.get('payload', {}))[:8000]
        return data
    except:
        return None


def extract_body(payload):
    """Extrae texto del body"""
    text = ''
    if payload.get('body', {}).get('data'):
        text = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    
    for part in payload.get('parts', []):
        mime = part.get('mimeType', '')
        if mime == 'text/plain' and part.get('body', {}).get('data'):
            text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        elif mime == 'text/html' and not text and part.get('body', {}).get('data'):
            html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            text = re.sub(r'<[^>]+>', ' ', html)
        elif mime.startswith('multipart/'):
            text += extract_body(part)
    return text.strip()


def check_duplicate(codigo, user_id):
    """Verifica duplicado por código reserva"""
    if not codigo:
        return False
    return Viaje.query.filter_by(user_id=user_id, codigo_reserva=codigo).first() is not None


def scan_and_create_viajes(user_id, days_back=30):
    """Escanea Gmail y crea viajes (máx 5 emails por scan)"""
    
    results = {
        'emails_encontrados': 0,
        'emails_procesados': 0,
        'viajes_creados': 0,
        'viajes_duplicados': 0,
        'errors': []
    }
    
    connections = EmailConnection.query.filter_by(
        user_id=user_id, provider='gmail', is_active=True
    ).all()
    
    if not connections:
        results['errors'].append('No hay cuentas Gmail conectadas')
        return results
    
    for conn in connections:
        try:
            creds = get_gmail_credentials(user_id)
            if not creds:
                continue
            
            service = build('gmail', 'v1', credentials=creds)
            msg_ids = search_travel_emails(service, days_back)
            results['emails_encontrados'] += len(msg_ids)
            
            # Limitar para evitar timeout
            for msg_id in msg_ids[:MAX_EMAILS_PER_SCAN]:
                try:
                    email = get_email_content(service, msg_id)
                    if not email or not is_whitelisted_sender(email.get('from'), user_id):
                        continue
                    
                    results['emails_procesados'] += 1
                    
                    # Extraer con Claude
                    text = f"Subject: {email.get('subject', '')}\n\n{email.get('body', '')}"
                    vuelos = extraer_info_con_claude(text)
                    
                    if not vuelos:
                        continue
                    
                    # Verificar duplicado
                    codigo = vuelos[0].get('codigo_reserva')
                    if codigo and check_duplicate(codigo, user_id):
                        results['viajes_duplicados'] += 1
                        continue
                    
                    # Crear viajes
                    grupo = str(uuid.uuid4())[:8]
                    for v in vuelos:
                        fecha_str = v.get('fecha_salida')
                        hora = v.get('hora_salida', '')
                        if not fecha_str:
                            continue
                        
                        try:
                            if hora:
                                fecha = datetime.strptime(f"{fecha_str} {hora}", '%Y-%m-%d %H:%M')
                            else:
                                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                        except:
                            continue
                        
                        viaje = Viaje(
                            user_id=user_id,
                            tipo='vuelo',
                            descripcion='',
                            origen=v.get('origen', ''),
                            destino=v.get('destino', ''),
                            fecha_salida=fecha,
                            hora_salida=hora,
                            aerolinea=v.get('aerolinea', ''),
                            numero_vuelo=v.get('numero_vuelo', ''),
                            codigo_reserva=v.get('codigo_reserva', ''),
                            pasajeros=json_lib.dumps(v.get('pasajeros', [])),
                            grupo_viaje=grupo
                        )
                        db.session.add(viaje)
                        results['viajes_creados'] += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    results['errors'].append(str(e))
                    db.session.rollback()
        
        except Exception as e:
            results['errors'].append(f"Error conexión {conn.email}: {str(e)}")
    
    return results
