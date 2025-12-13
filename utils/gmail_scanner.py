"""
Gmail Scanner - Mi Agente Viajes
MVP14: Escaneo de emails de viajes
MVP14e: Custom senders whitelist
MVP14g: Extracción de PDFs adjuntos + deduplicación por contenido
"""
import base64
import re
import io
from datetime import datetime, timedelta

from models import db, EmailConnection, Viaje

# Whitelist de dominios de aerolíneas y OTAs
WHITELIST_DOMAINS = [
    # Aerolíneas principales
    'latam.com', 'lan.com', 'tam.com.br',
    'aerolineas.com.ar', 'aerolineas.com',
    'americanairlines.com', 'aa.com',
    'united.com', 'delta.com', 'southwest.com',
    'aircanada.com', 'westjet.com',
    'iberia.com', 'vueling.com', 'aireuropa.com',
    'airfrance.com', 'klm.com', 'lufthansa.com',
    'britishairways.com', 'swiss.com', 'austrian.com',
    'emirates.com', 'qatarairways.com', 'etihad.com',
    'singaporeair.com', 'cathaypacific.com',
    'qantas.com', 'airnewzealand.co.nz',
    'avianca.com', 'copa.com', 'aeromexico.com',
    'jetsmart.com', 'flybondi.com', 'skyairline.com',
    'gol.com.br', 'azul.com.br',
    # Aerolíneas adicionales
    'norwegian.com', 'ryanair.com', 'easyjet.com',
    'volaris.com', 'viva.aero', 'wingo.com',
    'jetblue.com', 'alaskaair.com', 'spirit.com', 'frontier.com',
    'turkishairlines.com', 'saudia.com',
    # OTAs y agencias
    'despegar.com', 'decolar.com',
    'booking.com', 'expedia.com', 'kayak.com',
    'skyscanner.com', 'google.com',
    'almundo.com', 'avantrip.com',
    'tripadvisor.com', 'priceline.com',
    'orbitz.com', 'travelocity.com',
    'cheaptickets.com', 'hotwire.com',
    'momondo.com', 'kiwi.com',
    # Agencias Argentina/Latam
    'asatej.com.ar', 'tije.com.ar', 'juliatours.com.ar',
    'ola.com.ar',
    # Trenes/otros transportes
    'renfe.com', 'eurostar.com', 'amtrak.com',
    'busbud.com', 'omio.com', 'rome2rio.com',
    # Hoteles
    'hilton.com', 'marriott.com', 'ihg.com',
    'hyatt.com', 'accor.com', 'wyndham.com',
    # Más OTAs y hoteles
    'hotels.com', 'agoda.com', 'hostelworld.com',
    'vrbo.com', 'airbnb.com',
    # Corporate travel
    'concur.com', 'egencia.com', 'navan.com',
    'travelperk.com', 'brex.com',
    # Otros
    'sabre.com', 'amadeus.com', 'travelport.com',
    'checkmytrip.com', 'tripit.com', 'tripcase.com',
    'flightaware.com', 'flightstats.com',

    # ===========================================
    # NUEVOS TIPOS (14-EXT)
    # ===========================================

    # Cruceros y Ferries
    'buquebus.com', 'buquebus.com.ar',
    'msccruceros.com', 'msc.com', 'msccruises.com',
    'royalcaribbean.com', 'rccl.com',
    'carnival.com', 'ncl.com',
    'costacruises.com', 'princess.com',
    'hollandamerica.com', 'cunard.com',
    'directferries.com', 'ferryscanner.com',
    'aferry.com', 'ferries.com',

    # Rental de Autos
    'hertz.com', 'avis.com', 'enterprise.com',
    'budget.com', 'nationalcar.com', 'alamo.com',
    'sixt.com', 'europcar.com', 'dollar.com', 'thrifty.com',
    'localiza.com', 'movida.com.br',
    'rentcars.com', 'rentalcars.com', 'autoeurope.com',

    # Restaurantes
    'opentable.com', 'thefork.com', 'tenedor.com', 'lafourchette.com',
    'resy.com', 'yelp.com', 'restorando.com',
    'covermanager.com', 'dimmi.com.au',

    # Espectáculos y Entradas
    'ticketmaster.com', 'ticketmaster.com.ar', 'ticketmaster.com.mx',
    'eventbrite.com', 'eventbrite.com.ar',
    'allaccess.com.ar', 'ticketek.com.ar', 'tuentrada.com',
    'stubhub.com', 'vividseats.com', 'seatgeek.com',
    'dice.fm', 'songkick.com', 'bandsintown.com',
    'teleticket.com.pe', 'puntoticket.com',

    # Teatros (principales)
    'fenice.it', 'teatrocolon.org.ar', 'metopera.org',
    'royaloperahouse.org', 'operadeparis.fr',

    # Actividades y Tours
    'civitatis.com', 'getyourguide.com', 'viator.com',
    'klook.com', 'tiqets.com', 'musement.com',
    'withlocals.com', 'toursbylocals.com',

    # Hoteles adicionales
    'direct-book.com',
    'trivago.com', 'hotelbeds.com',
    'bestwestern.com', 'radissonhotels.com',
    'choicehotels.com', 'fourseasons.com',
    'ritzcarlton.com', 'starwoodhotels.com',
    'lhw.com', 'slh.com', 'preferredhotels.com',
    'melia.com', 'nh-hotels.com', 'barcelo.com',

    # Trenes adicionales
    'trenitalia.com', 'italotreno.it',
    'sncf.com', 'oui.sncf', 'ouigo.com',
    'bahn.de', 'deutschebahn.com',
    'thetrainline.com', 'raileurope.com',
    'ave.com', 'iryo.eu',
    'flixbus.com', 'blablacar.com',
]

MAX_EMAILS_PER_SCAN = 5


def is_whitelisted_sender(email_from, user_id=None):
    """
    Verifica si el remitente está en la whitelist global o en los custom senders del usuario.
    
    Args:
        email_from: Header "From" del email
        user_id: ID del usuario para chequear custom senders (opcional)
    
    Returns:
        bool: True si el remitente está permitido
    """
    from models import User
    
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


def extract_body(payload):
    """Extrae texto del body del email"""
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


def extract_pdf_attachments(service, message_id, payload):
    """
    Extrae PDFs adjuntos del email.
    
    Returns:
        list: Lista de dicts con 'filename' y 'data' (bytes)
    """
    attachments = []
    
    def process_parts(parts):
        for part in parts:
            filename = part.get('filename', '')
            mime_type = part.get('mimeType', '')
            
            # Si es PDF
            if mime_type == 'application/pdf' or filename.lower().endswith('.pdf'):
                if 'body' in part and 'attachmentId' in part['body']:
                    try:
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
                        print(f"    📎 PDF encontrado: {filename}")
                    except Exception as e:
                        print(f"    ⚠️ Error descargando PDF {filename}: {e}")
            
            # Recursivo para parts anidados
            if 'parts' in part:
                process_parts(part['parts'])
    
    if 'parts' in payload:
        process_parts(payload['parts'])
    
    return attachments


def extract_text_from_pdf(pdf_data):
    """
    Extrae texto de un PDF en memoria usando PyMuPDF (fitz).
    
    Args:
        pdf_data: bytes del PDF
    
    Returns:
        str: Texto extraído
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text.strip()
    except ImportError:
        print("    ⚠️ PyMuPDF no instalado, intentando PyPDF2...")
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(pdf_data))
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            return text.strip()
        except Exception as e:
            print(f"    ⚠️ Error extrayendo PDF: {e}")
            return ''
    except Exception as e:
        print(f"    ⚠️ Error extrayendo PDF: {e}")
        return ''


def get_full_email_content(service, message_id, payload, subject=''):
    """
    Extrae todo el contenido del email: body + PDFs adjuntos.
    
    Returns:
        str: Texto combinado
    """
    # Extraer body
    body_text = extract_body(payload)
    
    # Extraer texto de PDFs adjuntos
    pdf_texts = []
    attachments = extract_pdf_attachments(service, message_id, payload)
    
    for att in attachments:
        pdf_text = extract_text_from_pdf(att['data'])
        if pdf_text:
            pdf_texts.append(pdf_text)
    
    # Combinar
    full_content = f"Subject: {subject}\n\n{body_text}"
    
    if pdf_texts:
        full_content += "\n\n--- CONTENIDO DE PDFs ADJUNTOS ---\n\n"
        full_content += "\n\n---\n\n".join(pdf_texts)
    
    return full_content[:15000]  # Limitar para Claude


def check_duplicate(codigo, user_id):
    """Verifica duplicado por código reserva"""
    if not codigo:
        return False
    return Viaje.query.filter_by(user_id=user_id, codigo_reserva=codigo).first() is not None


def check_duplicate_by_content(user_id, numero_vuelo, fecha_salida, origen, destino):
    """
    Verifica duplicado por contenido cuando no hay código de reserva.
    
    Args:
        user_id: ID del usuario
        numero_vuelo: Número de vuelo (ej: "IB5550")
        fecha_salida: Fecha como string "YYYY-MM-DD" o datetime
        origen: Código aeropuerto origen
        destino: Código aeropuerto destino
    
    Returns:
        bool: True si ya existe un viaje con estos datos
    """
    if not numero_vuelo or not fecha_salida:
        return False
    
    # Normalizar fecha
    if isinstance(fecha_salida, str):
        try:
            fecha = datetime.strptime(fecha_salida.split()[0], '%Y-%m-%d').date()
        except:
            return False
    else:
        fecha = fecha_salida.date() if hasattr(fecha_salida, 'date') else fecha_salida
    
    # Buscar viaje con mismo vuelo, fecha, origen y destino
    existing = Viaje.query.filter(
        Viaje.user_id == user_id,
        Viaje.numero_vuelo == numero_vuelo,
        db.func.date(Viaje.fecha_salida) == fecha
    ).first()
    
    if existing:
        # Verificar también origen/destino para mayor precisión
        if existing.origen == origen and existing.destino == destino:
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


def scan_and_create_viajes(user_id, days_back=30):
    """Escanea Gmail y crea viajes (máx 5 emails por scan)"""
    from blueprints.gmail_oauth import get_gmail_credentials
    from googleapiclient.discovery import build
    from utils.claude import extraer_info_con_claude
    import uuid
    import logging

    logger = logging.getLogger(__name__)

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
            # Detectar primera conexión para backfill
            is_first_scan = conn.last_scan is None or conn.emails_processed == 0
            scan_days = 180 if is_first_scan else days_back

            if is_first_scan:
                logger.info(f"🆕 Primera conexión Gmail detectada: {conn.email} - Backfill de {scan_days} días")

            creds = get_gmail_credentials(user_id, gmail_email=conn.email)
            if not creds:
                continue

            service = build('gmail', 'v1', credentials=creds)
            msg_ids = search_travel_emails(service, scan_days)
            results['emails_encontrados'] += len(msg_ids)

            emails_processed_count = 0

            # Limitar para evitar timeout
            for msg_id in msg_ids[:MAX_EMAILS_PER_SCAN]:
                try:
                    email = get_email_content(service, msg_id)
                    if not email or not is_whitelisted_sender(email.get('from'), user_id):
                        continue

                    results['emails_procesados'] += 1
                    emails_processed_count += 1
                    
                    # Extraer con Claude
                    text = f"Subject: {email.get('subject', '')}\n\n{email.get('body', '')}"
                    vuelos = extraer_info_con_claude(text)
                    
                    if not vuelos:
                        continue
                    
                    # Verificar duplicado por código
                    codigo = vuelos[0].get('codigo_reserva')
                    if codigo and check_duplicate(codigo, user_id):
                        results['viajes_duplicados'] += 1
                        continue
                    
                    # Verificar duplicado por contenido
                    primer_vuelo = vuelos[0]
                    if check_duplicate_by_content(
                        user_id,
                        primer_vuelo.get('numero_vuelo'),
                        primer_vuelo.get('fecha_salida'),
                        primer_vuelo.get('origen'),
                        primer_vuelo.get('destino')
                    ):
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

                        # En backfill, solo procesar vuelos futuros
                        if is_first_scan and fecha.date() < datetime.utcnow().date():
                            logger.info(f"⏭️ Saltando vuelo pasado en backfill: {fecha_str}")
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
                            codigo_reserva=codigo or '',
                            pasajeros='[]',
                            grupo_viaje=grupo
                        )
                        db.session.add(viaje)
                        results['viajes_creados'] += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    results['errors'].append(str(e))
                    db.session.rollback()

            # Actualizar tracking de la conexión
            conn.last_scan = datetime.utcnow()
            conn.emails_processed = (conn.emails_processed or 0) + emails_processed_count
            db.session.commit()
            logger.info(f"✅ Conexión Gmail actualizada: last_scan={conn.last_scan}, total_emails={conn.emails_processed}")

        except Exception as e:
            results['errors'].append(f"Error con {conn.email}: {str(e)}")
    
    return results
