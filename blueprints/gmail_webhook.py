"""
Gmail Push Notifications - Mi Agente Viajes
MVP14c: Webhook para recibir notificaciones de Gmail via Pub/Sub
MVP14e: Soporte para custom senders
MVP14f: Fix multi-cuenta - setup_gmail_watch por email específico
MVP14g: Extracción de PDFs adjuntos + deduplicación por contenido
"""
import base64
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from googleapiclient.discovery import build

from models import db, EmailConnection, Viaje
from utils.gmail_scanner import (
    extract_body,
    extract_pdf_attachments,
    extract_text_from_pdf,
    check_duplicate,
    check_duplicate_by_content
)
from utils.claude import extraer_info_con_claude
from email_processor import email_parece_reserva
from utils.save_reservation import save_reservation, merge_reservation_data

gmail_webhook_bp = Blueprint('gmail_webhook', __name__)
PUBSUB_TOPIC = 'projects/mi-agente-viajes/topics/gmail-notifications'


def setup_gmail_watch(user_id, gmail_email=None):
    """
    Activa Gmail Push Notifications para una cuenta específica.
    
    Args:
        user_id: ID del usuario
        gmail_email: Email específico a activar (requerido si hay múltiples cuentas)
    """
    from blueprints.gmail_oauth import get_gmail_credentials
    
    # Buscar la conexión específica
    if gmail_email:
        connection = EmailConnection.query.filter_by(
            user_id=user_id, provider='gmail', email=gmail_email, is_active=True
        ).first()
    else:
        connection = EmailConnection.query.filter_by(
            user_id=user_id, provider='gmail', is_active=True
        ).first()
    
    if not connection:
        return {'success': False, 'error': 'No connection found'}
    
    credentials = get_gmail_credentials(user_id, gmail_email=connection.email)
    if not credentials:
        return {'success': False, 'error': 'No credentials'}
    
    try:
        service = build('gmail', 'v1', credentials=credentials)
        watch_response = service.users().watch(
            userId='me',
            body={'topicName': PUBSUB_TOPIC, 'labelIds': ['INBOX']}
        ).execute()
        
        history_id = watch_response.get('historyId')
        expiration = watch_response.get('expiration')
        
        # Actualizar LA MISMA conexión que usamos
        connection.history_id = history_id
        if expiration:
            connection.watch_expiration = datetime.fromtimestamp(int(expiration) / 1000)
        db.session.commit()
        
        print(f"Gmail watch activado user {user_id}, email {connection.email}")
        return {'success': True, 'history_id': history_id, 'email': connection.email}
        
    except Exception as e:
        print(f"Error watch: {e}")
        return {'success': False, 'error': str(e)}


def renew_expired_watches():
    """
    Renueva los Gmail watches que están por expirar (dentro de 24 horas).
    Debe ejecutarse desde un cron periódicamente.
    """
    from datetime import timedelta

    # Buscar conexiones Gmail con watch por expirar o ya expirado
    expiry_threshold = datetime.utcnow() + timedelta(hours=24)

    connections = EmailConnection.query.filter(
        EmailConnection.provider == 'gmail',
        EmailConnection.is_active == True,
        db.or_(
            EmailConnection.watch_expiration == None,
            EmailConnection.watch_expiration < expiry_threshold
        )
    ).all()

    renewed = 0
    errors = []

    for conn in connections:
        print(f"🔄 Renovando watch para {conn.email}...")
        result = setup_gmail_watch(conn.user_id, conn.email)
        if result.get('success'):
            renewed += 1
            print(f"  ✅ Watch renovado para {conn.email}")
        else:
            error = result.get('error', 'Unknown error')
            errors.append(f"{conn.email}: {error}")
            print(f"  ❌ Error renovando watch para {conn.email}: {error}")

    return {
        'total': len(connections),
        'renewed': renewed,
        'errors': errors
    }


def get_full_email_content(service, msg_id, payload, subject=''):
    """
    Extrae todo el contenido del email: body + PDFs adjuntos.
    
    Returns:
        str: Texto combinado listo para Claude
    """
    # Extraer body
    body_text = extract_body(payload)
    
    # Extraer texto de PDFs adjuntos
    pdf_texts = []
    attachments = extract_pdf_attachments(service, msg_id, payload)
    
    for att in attachments:
        pdf_text = extract_text_from_pdf(att['data'])
        if pdf_text:
            pdf_texts.append(pdf_text)
            print(f"    ✅ PDF procesado: {att['filename']} ({len(pdf_text)} chars)")
    
    # Combinar
    full_content = f"Subject: {subject}\n\n{body_text}"
    
    if pdf_texts:
        full_content += "\n\n--- CONTENIDO DE PDFs ADJUNTOS ---\n\n"
        full_content += "\n\n---\n\n".join(pdf_texts)
        print(f"    📄 Contenido total: body + {len(pdf_texts)} PDF(s)")
    
    return full_content[:15000]  # Limitar para Claude


def process_new_emails(connection, history_id):
    """Procesa emails nuevos desde el ultimo historyId."""
    from blueprints.gmail_oauth import get_gmail_credentials
    import uuid
    
    if not connection.history_id:
        print(f"Sin history_id para {connection.email}")
        return 0
    
    # Usar credenciales de la conexión específica
    credentials = get_gmail_credentials(connection.user_id, gmail_email=connection.email)
    if not credentials:
        print(f"Sin credenciales para {connection.email}")
        return 0
    
    try:
        service = build('gmail', 'v1', credentials=credentials)
        history_response = service.users().history().list(
            userId='me',
            startHistoryId=connection.history_id,
            historyTypes=['messageAdded'],
            labelId='INBOX'
        ).execute()
        
        viajes_creados = 0
        history_list = history_response.get('history', [])
        print(f"Procesando {len(history_list)} cambios para {connection.email}")
        
        for history in history_list:
            for msg_info in history.get('messagesAdded', []):
                msg_id = msg_info.get('message', {}).get('id')
                if not msg_id:
                    continue
                
                try:
                    msg = service.users().messages().get(
                        userId='me', id=msg_id, format='full'
                    ).execute()
                    
                    headers = msg.get('payload', {}).get('headers', [])
                    from_header = subject = None
                    
                    for h in headers:
                        if h['name'].lower() == 'from':
                            from_header = h['value']
                        elif h['name'].lower() == 'subject':
                            subject = h['value']
                    
                    # MVP14g: Extraer body para pre-filtro
                    payload = msg.get('payload', {})
                    body_preview = extract_body(payload)[:2000]

                    # Extraer nombres de adjuntos del payload (sin descargar contenido)
                    attachment_names = []
                    def get_attachment_names(parts):
                        for part in parts:
                            filename = part.get('filename', '')
                            if filename:
                                attachment_names.append(filename)
                            if 'parts' in part:
                                get_attachment_names(part['parts'])

                    if 'parts' in payload:
                        get_attachment_names(payload['parts'])

                    # Filtro por keywords (incluye nombres de adjuntos)
                    if not email_parece_reserva(subject or '', body_preview, attachment_names):
                        print(f"⏭️ Email descartado por pre-filtro (no parece reserva): {subject[:50] if subject else '(sin subject)'}")
                        continue

                    print(f"✅ Email parece reserva, procesando: {subject[:50] if subject else '(sin subject)'}")
                    
                    # MVP14g: Extraer body + PDFs adjuntos
                    full_content = get_full_email_content(
                        service, msg_id, msg.get('payload', {}), subject
                    )

                    # DEBUG: Log muestra del contenido para diagnóstico
                    print(f"📄 Contenido total: {len(full_content)} chars")
                    # Buscar años en el contenido
                    import re
                    years_found = set(re.findall(r'20[2-3][0-9]', full_content))
                    print(f"📅 Años encontrados en contenido: {sorted(years_found)}")

                    # Verificar si este email ya fue procesado
                    from models import ProcessedEmail
                    already_processed = ProcessedEmail.query.filter_by(
                        connection_id=connection.id,
                        message_id=msg_id
                    ).first()

                    if already_processed:
                        print(f"⏭️ Email ya procesado anteriormente: {subject[:50] if subject else '(sin subject)'}")
                        continue

                    # Procesar con Claude
                    vuelos = extraer_info_con_claude(full_content)

                    # Marcar email como procesado
                    try:
                        processed_record = ProcessedEmail(
                            connection_id=connection.id,
                            message_id=msg_id,
                            had_reservation=bool(vuelos)
                        )
                        db.session.add(processed_record)
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ Error guardando ProcessedEmail: {e}")
                        db.session.rollback()
                    
                    if not vuelos:
                        print(f"No se encontraron vuelos en: {subject}")
                        continue
                    
                    # MVP14g: Deduplicación mejorada - ahora con merge de datos
                    # 1. Por código de reserva - buscar TODOS los viajes (ida y vuelta)
                    codigo = vuelos[0].get('codigo_reserva')
                    if codigo:
                        existing_viajes = Viaje.query.filter_by(
                            user_id=connection.user_id,
                            codigo_reserva=codigo
                        ).all()
                        if existing_viajes:
                            # Intentar actualizar cada viaje existente con datos correspondientes
                            hubo_actualizacion = False
                            for existing in existing_viajes:
                                # Buscar vuelo correspondiente por fecha
                                fecha_existing = existing.fecha_salida
                                for vuelo in vuelos:
                                    fecha_vuelo = vuelo.get('fecha_salida')
                                    if fecha_existing and fecha_vuelo and str(fecha_existing.date()) == fecha_vuelo[:10]:
                                        if merge_reservation_data(existing, vuelo):
                                            hubo_actualizacion = True
                                            print(f"🔄 Reserva actualizada: {codigo} ({fecha_vuelo})")
                            if hubo_actualizacion:
                                db.session.commit()
                            else:
                                print(f"Duplicado sin cambios: {codigo}")
                            continue

                    # 2. Por contenido (vuelo + fecha + ruta)
                    primer_vuelo = vuelos[0]
                    existing_by_content = check_duplicate_by_content(
                        connection.user_id,
                        primer_vuelo.get('numero_vuelo'),
                        primer_vuelo.get('fecha_salida'),
                        primer_vuelo.get('origen'),
                        primer_vuelo.get('destino')
                    )
                    if existing_by_content:
                        # Hacer merge de datos (actualizar info adicional como pasajeros)
                        from utils.save_reservation import merge_reservation_data
                        if merge_reservation_data(existing_by_content, primer_vuelo):
                            db.session.commit()
                            print(f"🔄 Duplicado actualizado: {primer_vuelo.get('numero_vuelo')} {primer_vuelo.get('fecha_salida')}")
                        else:
                            print(f"Duplicado por contenido: {primer_vuelo.get('numero_vuelo')} {primer_vuelo.get('fecha_salida')}")
                        continue
                    
                    grupo = str(uuid.uuid4())[:8]

                    for v in vuelos:
                        # Truncar codigo_reserva si es muy largo
                        codigo = v.get('codigo_reserva', '')
                        if codigo and len(codigo) > 250:
                            print(f"⚠️ Código reserva muy largo ({len(codigo)} chars), truncando: {codigo[:50]}...")
                            v['codigo_reserva'] = codigo[:250]

                        try:
                            viaje = save_reservation(
                                user_id=connection.user_id,
                                datos_dict=v,
                                grupo_id=grupo,
                                nombre_viaje=None,
                                source='gmail'
                            )
                            viajes_creados += 1
                            print(f"✅ Viaje creado: {v.get('origen', '')} → {v.get('destino', '')}")
                        except ValueError as e:
                            print(f"⚠️ {e}")
                            continue
                    
                    db.session.commit()
                    
                except Exception as e:
                    print(f"Error procesando mensaje: {e}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()
        
        # Actualizar history_id para próxima vez
        new_history_id = history_response.get('historyId', history_id)
        connection.history_id = new_history_id
        connection.last_scan = datetime.utcnow()
        db.session.commit()
        print(f"history_id actualizado: {new_history_id}")
        
        return viajes_creados
        
    except Exception as e:
        print(f"Error history API: {e}")
        import traceback
        traceback.print_exc()
        return 0


@gmail_webhook_bp.route('/api/gmail-webhook', methods=['POST'])
def gmail_webhook():
    """Recibe notificaciones de Gmail via Pub/Sub."""
    try:
        envelope = request.get_json()
        if not envelope:
            print("Webhook: sin payload")
            return '', 200
        
        data_b64 = envelope.get('message', {}).get('data', '')
        if not data_b64:
            print("Webhook: sin data")
            return '', 200
        
        data = json.loads(base64.urlsafe_b64decode(data_b64).decode('utf-8'))
        email_address = data.get('emailAddress')
        history_id = data.get('historyId')
        
        print(f"📬 Notif Gmail: {email_address}, historyId: {history_id}")
        
        if not email_address:
            return '', 200
        
        connection = EmailConnection.query.filter_by(
            email=email_address, provider='gmail', is_active=True
        ).first()
        
        if connection:
            viajes = process_new_emails(connection, history_id)
            if viajes:
                print(f"🎉 Creados {viajes} viajes automáticamente")
        else:
            print(f"No se encontró conexión para: {email_address}")
        
        return '', 200
        
    except Exception as e:
        print(f"Error webhook: {e}")
        import traceback
        traceback.print_exc()
        return '', 200


@gmail_webhook_bp.route('/api/gmail-webhook', methods=['GET'])
def gmail_webhook_health():
    """Health check"""
    return jsonify({'status': 'ok'})
