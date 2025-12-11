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
# WHITELIST DE REMITENTES (150+ dominios)
# ============================================

# Aerolíneas - Sudamérica
AIRLINES_SOUTH_AMERICA = [
    'latam.com', 'lan.com', 'tam.com.br',
    'aerolineas.com.ar',
    'gol.com.br', 'voegol.com.br',
    'azul.com.br', 'voeazul.com.br',
    'avianca.com',
    'copa.com', 'copaair.com',
    'jetsmart.com',
    'flybondi.com',
    'skyairline.com',
    'wingo.com',
    'voepass.com.br',
    'boliviana.bo', 'boa.bo',
    'amaszonas.com',
    'paranair.com',
    'plusultra.com',
]

# Aerolíneas - Norteamérica
AIRLINES_NORTH_AMERICA = [
    'aa.com', 'americanairlines.com',
    'united.com',
    'delta.com',
    'southwest.com', 'southwestairlines.com',
    'jetblue.com',
    'alaskaair.com', 'alaskaairlines.com',
    'spirit.com',
    'frontierairlines.com', 'flyfrontier.com',
    'aircanada.com',
    'westjet.com',
    'aeromexico.com',
    'volaris.com',
    'vivaaerobus.com',
    'hawaiianairlines.com',
    'suncountry.com',
    'allegiantair.com',
    'porterairlines.com',
    'flair.com', 'flairair.com',
    'breeze.com', 'breezeairways.com',
]

# Aerolíneas - Europa
AIRLINES_EUROPE = [
    # España
    'iberia.com', 'iberia.es',
    'aireuropa.com',
    'vueling.com',
    'iberiaexpress.com',
    'airnostrum.es',
    # Francia
    'airfrance.com', 'airfrance.fr',
    'transavia.com',
    'corsair.fr',
    'frenchbee.com',
    # Alemania/Austria/Suiza
    'lufthansa.com',
    'swiss.com',
    'austrian.com',
    'eurowings.com',
    'condor.com',
    'tuifly.com',
    # UK/Irlanda
    'britishairways.com', 'british-airways.com', 'ba.com',
    'virginatlantic.com',
    'aerlingus.com',
    'jet2.com',
    'tui.co.uk',
    # Benelux
    'klm.com', 'klm.nl',
    'brusselsairlines.com', 'brussels-airlines.com',
    # Italia
    'ita-airways.com', 'itaspa.com',
    'alitalia.com',
    'neos.it',
    # Portugal
    'flytap.com', 'tapportugal.com',
    'sata.pt',
    # Escandinavia
    'flysas.com', 'sas.se',
    'finnair.com',
    'norwegian.com', 'norwegian.no',
    'icelandair.com',
    'wideroe.no',
    # Europa del Este
    'lot.com',
    'czechairlines.com',
    'tarom.ro',
    'airserbia.com',
    'croatiaairlines.com',
    'aegeanair.com',
    'olympicair.com',
    'airmalta.com',
    'airbaltic.com',
    # Turquía
    'turkishairlines.com', 'thy.com',
    'pegasus.com', 'flypgs.com',
    'sunexpress.com',
    # Rusia/CIS
    'aeroflot.com', 'aeroflot.ru',
    's7.ru', 's7airlines.com',
    'utair.ru',
    'airastana.com',
    'uzbekistanairways.com',
]

# Low Cost Europa
AIRLINES_LOWCOST_EUROPE = [
    'ryanair.com',
    'easyjet.com',
    'wizzair.com', 'wizzair.hu',
    'volotea.com',
    'vueling.com',
    'eurowings.com',
    'norwegian.com',
    'transavia.com',
    'corendon.com',
    'smartwings.com',
    'playwings.com',
    'level.com', 'flylevel.com',
    'lauda.com', 'laudamotion.com',
]

# Aerolíneas - Asia
AIRLINES_ASIA = [
    # Medio Oriente
    'emirates.com',
    'etihad.com',
    'qatarairways.com', 'qatar.com',
    'saudia.com',
    'royaljordanian.com',
    'omanair.com',
    'gulfair.com',
    'kuwaitairways.com',
    'flynas.com',
    'flydubai.com',
    'flyegypt.com',
    'egyptair.com',
    'royalmaroc.com',
    'tunisair.com',
    'algerieairlines.com', 'airalgerie.dz',
    'ethiopianairlines.com',
    'kenya-airways.com',
    'flysaa.com',
    'rwandair.com',
    # Asia del Sur
    'airindia.com',
    'goindigo.in', 'indigo.in',
    'spicejet.com',
    'goair.in',
    'airvistara.com',
    'srilankan.com',
    'bfrairbangladesh.com',
    'pakistanairlines.com', 'piac.com.pk',
    # Sudeste Asiático
    'singaporeair.com',
    'thaiairways.com', 'thai.com',
    'malaysiaairlines.com', 'mas.com.my',
    'garuda-indonesia.com',
    'philippineairlines.com',
    'vietnamairlines.com',
    'cathaypacific.com',
    'airasia.com',
    'scoot.com',
    'jetstar.com',
    'lionair.co.id',
    'cebuair.com', 'cebupacificair.com',
    'bangkokair.com',
    'tigerair.com',
    # Asia del Este
    'ana.co.jp',
    'jal.co.jp', 'jal.com',
    'koreanair.com',
    'asiana.com',
    'jejuair.net',
    'airchina.com',
    'chinaeastern.com', 'ceair.com',
    'csair.com',
    'hainanairlines.com',
    'xiamenair.com',
    'shenzhenair.com',
    'springairlines.com',
    'evaair.com',
    'china-airlines.com',
    'starflyer.jp',
    'peach-air.co.jp',
    'skymark.co.jp',
    # Oceanía
    'qantas.com',
    'virginaustralia.com',
    'airnewzealand.com', 'airnz.com',
    'fijiairways.com',
]

# OTAs y Agencias
OTA_DOMAINS = [
    # Globales
    'booking.com',
    'expedia.com', 'expedia.com.ar',
    'kayak.com', 'kayak.com.ar',
    'skyscanner.com', 'skyscanner.net',
    'tripadvisor.com',
    'priceline.com',
    'orbitz.com',
    'travelocity.com',
    'cheaptickets.com',
    'hotwire.com',
    'hotels.com',
    'agoda.com',
    'trip.com', 'ctrip.com',
    'kiwi.com',
    'momondo.com',
    'opodo.com',
    'edreams.com',
    'lastminute.com',
    'travelgenio.com',
    'travelstart.com',
    'flightcentre.com',
    'webjet.com.au',
    # Latinoamérica
    'despegar.com', 'despegar.com.ar',
    'decolar.com',
    'almundo.com', 'almundo.com.ar',
    'avantrip.com',
    'vuelos.com',
    'turismocity.com',
    'viajanet.com.br',
    'maxmilhas.com.br',
    'voopter.com.br',
    'submarino.com.br',
    'bestday.com',
    'pricetravel.com',
    'clickbus.com',
    # Europa
    'bravofly.com',
    'govoyages.com',
    'liligo.com',
    'trabber.com',
    'rumbo.es',
    'logitravel.com',
    'atrápalo.com', 'atrapalo.com',
    'budgetair.com',
    'flightnetwork.com',
    'jetcost.com',
    'volagratis.com',
    'gotogate.com',
]

# Combinar todos los dominios
WHITELIST_DOMAINS = (
    AIRLINES_SOUTH_AMERICA +
    AIRLINES_NORTH_AMERICA +
    AIRLINES_EUROPE +
    AIRLINES_LOWCOST_EUROPE +
    AIRLINES_ASIA +
    OTA_DOMAINS
)

def is_whitelisted_sender(email_from):
    """Verifica si un remitente está en la whitelist"""
    if not email_from:
        return False
    
    email_match = re.search(r'[\w\.-]+@([\w\.-]+)', email_from.lower())
    if not email_match:
        return False
    
    domain = email_match.group(1)
    
    for whitelisted in WHITELIST_DOMAINS:
        if domain.endswith(whitelisted):
            return True
    
    return False


# ============================================
# GMAIL API FUNCTIONS
# ============================================

def get_gmail_service(user_id):
    """Crea un servicio de Gmail API para un usuario"""
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
    """Busca emails de viajes en el inbox"""
    # Gmail tiene límite de query, usar los dominios más comunes
    top_domains = WHITELIST_DOMAINS[:25]
    domain_queries = [f'from:@{domain}' for domain in top_domains]
    query = f"({' OR '.join(domain_queries)})"
    
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
    """Obtiene el contenido de un email específico"""
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        headers = message.get('payload', {}).get('headers', [])
        
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
        
        email_data['body'] = extract_email_body(message.get('payload', {}))
        
        return email_data
    except Exception as e:
        print(f"Error getting email {message_id}: {e}")
        return None


def extract_email_body(payload):
    """Extrae el texto del body de un email (maneja multipart)"""
    body_text = ''
    
    if 'body' in payload and payload['body'].get('data'):
        body_text = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    
    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                if part.get('body', {}).get('data'):
                    body_text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            elif mime_type == 'text/html' and not body_text:
                if part.get('body', {}).get('data'):
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    body_text = re.sub(r'<[^>]+>', ' ', html)
                    body_text = re.sub(r'\s+', ' ', body_text)
            elif mime_type.startswith('multipart/'):
                body_text += extract_email_body(part)
    
    return body_text.strip()


# ============================================
# PROCESAMIENTO
# ============================================

def check_duplicate_reservation(codigo_reserva, user_id):
    """Verifica si ya existe una reserva con este código"""
    if not codigo_reserva:
        return False
    
    existing = Viaje.query.filter_by(
        user_id=user_id,
        codigo_reserva=codigo_reserva
    ).first()
    
    return existing is not None


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def scan_and_create_viajes(user_id, days_back=30):
    """
    Escanea Gmail y crea viajes automáticamente
    """
    import uuid
    import json as json_lib
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
                results['errors'].append(f'Credenciales inválidas para {connection.email}')
                continue
            
            service = build('gmail', 'v1', credentials=credentials)
            message_ids = search_travel_emails(service, days_back=days_back)
            results['emails_scanned'] += len(message_ids)
            
            for msg_id in message_ids:
                try:
                    email_data = get_email_content(service, msg_id)
                    if not email_data or not is_whitelisted_sender(email_data.get('from', '')):
                        continue
                    
                    # Preparar texto para Claude
                    email_text = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
                    
                    # Limitar tamaño del texto
                    if len(email_text) > 15000:
                        email_text = email_text[:15000]
                    
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
                        
                        # Crear viaje con todos los campos requeridos
                        nuevo_viaje = Viaje(
                            user_id=user_id,
                            tipo='vuelo',
                            descripcion='',  # FIX: Campo requerido
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
                    db.session.rollback()  # FIX: Limpiar transacción fallida
                    results['errors'].append(f'Error en email: {str(e)[:100]}')
            
            # Actualizar conexión
            connection.last_scan = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()  # FIX: Limpiar transacción fallida
            results['errors'].append(f'Error con {connection.email}: {str(e)[:100]}')
    
    return results
