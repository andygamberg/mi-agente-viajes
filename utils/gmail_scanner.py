"""
Gmail Scanner - Mi Agente Viajes
MVP14b: Escanea emails de aerolíneas/agencias y extrae reservas
"""
import base64
import re
from datetime import datetime, timedelta
from googleapiclient.discovery import build

from models import db, Viaje, EmailConnection
from utils.claude import extraer_info_con_claude
from blueprints.gmail_oauth import get_gmail_credentials

# ============================================
# WHITELIST DE REMITENTES
# ============================================

# Dominios de aerolíneas
AIRLINE_DOMAINS = [
    'latam.com',
    'lan.com',
    'aerolineas.com.ar',
    'aa.com',
    'americanairlines.com',
    'united.com',
    'delta.com',
    'avianca.com',
    'copa.com',
    'gol.com.br',
    'azul.com.br',
    'jetsmart.com',
    'flybondi.com',
    'aireuropa.com',
    'iberia.com',
    'airfrance.com',
    'klm.com',
    'lufthansa.com',
    'british-airways.com',
    'emirates.com',
    'qatar.com',
    'tam.com.br',
]

# Dominios de OTAs y agencias
OTA_DOMAINS = [
    'despegar.com',
    'booking.com',
    'expedia.com',
    'kayak.com',
    'skyscanner.com',
    'decolar.com',
    'almundo.com',
    'avantrip.com',
    'vuelos.com',
    'turismocity.com',
    'priceline.com',
    'orbitz.com',
    'travelocity.com',
    'cheaptickets.com',
    'hotwire.com',
    'tripadvisor.com',
]

# Combinar todos los dominios
WHITELIST_DOMAINS = AIRLINE_DOMAINS + OTA_DOMAINS

def is_whitelisted_sender(email_from):
    """
    Verifica si un remitente está en la whitelist
    Args:
        email_from: String del campo From del email
    Returns:
        True si el dominio está en whitelist
    """
    if not email_from:
        return False
    
    # Extraer dominio del email
    email_match = re.search(r'[\w\.-]+@([\w\.-]+)', email_from.lower())
    if not email_match:
        return False
    
    domain = email_match.group(1)
    
    # Verificar contra whitelist
    for whitelisted in WHITELIST_DOMAINS:
        if domain.endswith(whitelisted):
            return True
    
    return False


# ============================================
# GMAIL API FUNCTIONS
# ============================================

def get_gmail_service(user_id):
    """
    Crea un servicio de Gmail API para un usuario
    Returns: Gmail service o None si no hay credenciales válidas
    """
    credentials = get_gmail_credentials(user_id)
    if not credentials:
        return None
    
    try:
        service = build('gmail', 'v1', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error creating Gmail service: {e}")
        return None


def search_travel_emails(service, days_back=30, max_results=50):
    """
    Busca emails de viajes en el inbox
    Args:
        service: Gmail API service
        days_back: Cuántos días hacia atrás buscar
        max_results: Máximo de emails a retornar
    Returns:
        Lista de message IDs
    """
    # Construir query para buscar emails de remitentes en whitelist
    # Gmail query: from:(@latam.com OR @despegar.com OR ...)
    domain_queries = [f'from:@{domain}' for domain in WHITELIST_DOMAINS[:20]]  # Limitar para no exceder query length
    query = f"({' OR '.join(domain_queries)})"
    
    # Agregar filtro de fecha
    after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    query += f" after:{after_date}"
    
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        return [msg['id'] for msg in messages]
    except Exception as e:
        print(f"Error searching emails: {e}")
        return []


def get_email_content(service, message_id):
    """
    Obtiene el contenido de un email específico
    Returns:
        Dict con 'from', 'subject', 'date', 'body' o None si error
    """
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        headers = message.get('payload', {}).get('headers', [])
        
        # Extraer headers
        email_data = {
            'id': message_id,
            'from': None,
            'subject': None,
            'date': None,
            'body': ''
        }
        
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            if name == 'from':
                email_data['from'] = value
            elif name == 'subject':
                email_data['subject'] = value
            elif name == 'date':
                email_data['date'] = value
        
        # Extraer body
        email_data['body'] = extract_email_body(message.get('payload', {}))
        
        return email_data
    except Exception as e:
        print(f"Error getting email {message_id}: {e}")
        return None


def extract_email_body(payload):
    """
    Extrae el texto del body de un email (maneja multipart)
    """
    body_text = ''
    
    # Caso simple: body directo
    if 'body' in payload and payload['body'].get('data'):
        body_text = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    
    # Caso multipart
    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                if part.get('body', {}).get('data'):
                    body_text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            elif mime_type == 'text/html' and not body_text:
                # Solo usar HTML si no hay texto plano
                if part.get('body', {}).get('data'):
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    # Limpiar HTML básico
                    body_text = re.sub(r'<[^>]+>', ' ', html)
                    body_text = re.sub(r'\s+', ' ', body_text)
            elif mime_type.startswith('multipart/'):
                # Recursivo para multipart anidado
                body_text += extract_email_body(part)
    
    return body_text.strip()


# ============================================
# PROCESAMIENTO DE EMAILS
# ============================================

def process_email_for_travel(email_data, user_id):
    """
    Procesa un email y extrae información de viaje si existe
    Args:
        email_data: Dict con from, subject, body
        user_id: ID del usuario
    Returns:
        Dict con resultado del procesamiento
    """
    # Verificar whitelist
    if not is_whitelisted_sender(email_data.get('from', '')):
        return {'status': 'skipped', 'reason': 'not_whitelisted'}
    
    # Preparar texto para Claude
    email_text = f"""
Subject: {email_data.get('subject', '')}
From: {email_data.get('from', '')}
Date: {email_data.get('date', '')}

{email_data.get('body', '')}
"""
    
    # Extraer info con Claude
    try:
        vuelos = extraer_info_con_claude(email_text)
        
        if not vuelos:
            return {'status': 'no_flights', 'reason': 'claude_no_extraction'}
        
        return {
            'status': 'found',
            'vuelos': vuelos,
            'email_subject': email_data.get('subject', '')
        }
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}


def check_duplicate_reservation(codigo_reserva, user_id):
    """
    Verifica si ya existe una reserva con este código para el usuario
    """
    if not codigo_reserva:
        return False
    
    existing = Viaje.query.filter_by(
        user_id=user_id,
        codigo_reserva=codigo_reserva
    ).first()
    
    return existing is not None


# ============================================
# FUNCIÓN PRINCIPAL DE ESCANEO
# ============================================

def scan_gmail_for_user(user_id, days_back=30, connection_id=None):
    """
    Escanea Gmail de un usuario buscando emails de viajes
    Args:
        user_id: ID del usuario
        days_back: Días hacia atrás para buscar
        connection_id: ID específico de conexión (o None para todas)
    Returns:
        Dict con resultados del escaneo
    """
    results = {
        'emails_scanned': 0,
        'emails_processed': 0,
        'vuelos_encontrados': 0,
        'vuelos_nuevos': 0,
        'vuelos_duplicados': 0,
        'errors': []
    }
    
    # Obtener conexiones activas
    if connection_id:
        connections = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=user_id,
            is_active=True
        ).all()
    else:
        connections = EmailConnection.query.filter_by(
            user_id=user_id,
            provider='gmail',
            is_active=True
        ).all()
    
    if not connections:
        results['errors'].append('No hay cuentas Gmail conectadas')
        return results
    
    for connection in connections:
        try:
            # Obtener servicio Gmail para esta conexión
            credentials = get_gmail_credentials(user_id)
            if not credentials:
                results['errors'].append(f'Credenciales inválidas para {connection.email}')
                continue
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Buscar emails
            message_ids = search_travel_emails(service, days_back=days_back)
            results['emails_scanned'] += len(message_ids)
            
            # Procesar cada email
            for msg_id in message_ids:
                email_data = get_email_content(service, msg_id)
                if not email_data:
                    continue
                
                # Verificar whitelist
                if not is_whitelisted_sender(email_data.get('from', '')):
                    continue
                
                results['emails_processed'] += 1
                
                # Procesar con Claude
                process_result = process_email_for_travel(email_data, user_id)
                
                if process_result['status'] == 'found':
                    for vuelo_data in process_result.get('vuelos', []):
                        results['vuelos_encontrados'] += 1
                        
                        # Verificar duplicado
                        codigo = vuelo_data.get('codigo_reserva')
                        if check_duplicate_reservation(codigo, user_id):
                            results['vuelos_duplicados'] += 1
                            continue
                        
                        # Crear viaje (sin guardar aún - retornar para confirmación)
                        results['vuelos_nuevos'] += 1
            
            # Actualizar last_scan
            connection.last_scan = datetime.utcnow()
            connection.emails_processed = (connection.emails_processed or 0) + results['emails_processed']
            db.session.commit()
            
        except Exception as e:
            results['errors'].append(f'Error escaneando {connection.email}: {str(e)}')
    
    return results


def scan_and_create_viajes(user_id, days_back=30):
    """
    Escanea Gmail y crea viajes automáticamente (sin confirmación)
    Returns:
        Dict con resultados incluyendo viajes creados
    """
    import uuid
    from datetime import datetime as dt
    
    results = {
        'emails_scanned': 0,
        'viajes_creados': 0,
        'viajes_duplicados': 0,
        'errors': []
    }
    
    connections = EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).all()
    
    if not connections:
        results['errors'].append('No hay cuentas Gmail conectadas')
        return results
    
    for connection in connections:
        try:
            credentials = get_gmail_credentials(user_id)
            if not credentials:
                continue
            
            service = build('gmail', 'v1', credentials=credentials)
            message_ids = search_travel_emails(service, days_back=days_back)
            results['emails_scanned'] += len(message_ids)
            
            for msg_id in message_ids:
                email_data = get_email_content(service, msg_id)
                if not email_data or not is_whitelisted_sender(email_data.get('from', '')):
                    continue
                
                # Preparar texto
                email_text = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
                
                try:
                    vuelos = extraer_info_con_claude(email_text)
                    if not vuelos:
                        continue
                    
                    # Verificar duplicado por código de reserva
                    primer_vuelo = vuelos[0]
                    codigo = primer_vuelo.get('codigo_reserva')
                    if codigo and check_duplicate_reservation(codigo, user_id):
                        results['viajes_duplicados'] += 1
                        continue
                    
                    # Crear grupo para todos los vuelos de esta reserva
                    grupo_id = str(uuid.uuid4())[:8]
                    
                    for vuelo_data in vuelos:
                        # Parsear fechas
                        fecha_salida_str = vuelo_data.get('fecha_salida')
                        hora_salida = vuelo_data.get('hora_salida', '')
                        
                        if not fecha_salida_str:
                            continue
                        
                        try:
                            if hora_salida:
                                fecha_salida = dt.strptime(f"{fecha_salida_str} {hora_salida}", '%Y-%m-%d %H:%M')
                            else:
                                fecha_salida = dt.strptime(fecha_salida_str, '%Y-%m-%d')
                        except:
                            continue
                        
                        # Crear viaje
                        import json as json_lib
                        nuevo_viaje = Viaje(
                            user_id=user_id,
                            tipo='vuelo',
                            origen=vuelo_data.get('origen', ''),
                            destino=vuelo_data.get('destino', ''),
                            fecha_salida=fecha_salida,
                            hora_salida=hora_salida,
                            aerolinea=vuelo_data.get('aerolinea', ''),
                            numero_vuelo=vuelo_data.get('numero_vuelo', ''),
                            codigo_reserva=vuelo_data.get('codigo_reserva', ''),
                            pasajeros=json_lib.dumps(vuelo_data.get('pasajeros', [])),
                            grupo_viaje=grupo_id
                        )
                        db.session.add(nuevo_viaje)
                        results['viajes_creados'] += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    results['errors'].append(f'Error procesando email: {str(e)}')
            
            # Actualizar conexión
            connection.last_scan = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            results['errors'].append(f'Error con {connection.email}: {str(e)}')
    
    return results
