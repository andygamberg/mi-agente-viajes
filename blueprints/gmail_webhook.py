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
    is_whitelisted_sender, 
    extract_body,
    extract_pdf_attachments,
    extract_text_from_pdf,
    check_duplicate,
    check_duplicate_by_content
)
from utils.claude import extraer_info_con_claude

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
                    
                    # MVP14e: Pasar user_id para chequear custom senders
                    if not is_whitelisted_sender(from_header, connection.user_id):
                        print(f"Remitente no whitelisted: {from_header}")
                        continue
                    
                    print(f"✅ Email de remitente confiable: {subject}")
                    
                    # MVP14g: Extraer body + PDFs adjuntos
                    full_content = get_full_email_content(
                        service, msg_id, msg.get('payload', {}), subject
                    )
                    
                    # Procesar con Claude
                    vuelos = extraer_info_con_claude(full_content)
                    
                    if not vuelos:
                        print(f"No se encontraron vuelos en: {subject}")
                        continue
                    
                    # MVP14g: Deduplicación mejorada
                    # 1. Por código de reserva
                    codigo = vuelos[0].get('codigo_reserva')
                    if codigo and check_duplicate(codigo, connection.user_id):
                        print(f"Duplicado por código: {codigo}")
                        continue
                    
                    # 2. Por contenido (vuelo + fecha + ruta)
                    primer_vuelo = vuelos[0]
                    if check_duplicate_by_content(
                        connection.user_id,
                        primer_vuelo.get('numero_vuelo'),
                        primer_vuelo.get('fecha_salida'),
                        primer_vuelo.get('origen'),
                        primer_vuelo.get('destino')
                    ):
                        print(f"Duplicado por contenido: {primer_vuelo.get('numero_vuelo')} {primer_vuelo.get('fecha_salida')}")
                        continue
                    
                    grupo = str(uuid.uuid4())[:8]

                    for v in vuelos:
                        # Validar datos mínimos antes de crear viaje
                        fecha_str = v.get('fecha_salida') or v.get('fecha_embarque') or v.get('fecha') or v.get('fecha_checkin') or v.get('fecha_retiro')

                        if not fecha_str:
                            print(f"⚠️ Reserva sin fecha, ignorando: {v.get('descripcion', 'Sin descripción')}")
                            continue

                        # Truncar codigo_reserva si es muy largo
                        codigo = v.get('codigo_reserva', '')
                        if len(codigo) > 250:
                            print(f"⚠️ Código reserva muy largo ({len(codigo)} chars), truncando: {codigo[:50]}...")
                            v['codigo_reserva'] = codigo[:250]

                        hora = v.get('hora_salida', '')
                        
                        try:
                            if hora:
                                fecha = datetime.strptime(f"{fecha_str} {hora}", '%Y-%m-%d %H:%M')
                            else:
                                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                        except:
                            continue

                        # Detectar tipo y mapear campos
                        tipo = v.get('tipo', 'vuelo')
                        proveedor = None
                        ubicacion = None
                        precio = v.get('precio_total')

                        if tipo == 'vuelo':
                            proveedor = v.get('aerolinea')
                        elif tipo == 'hotel':
                            proveedor = v.get('nombre_propiedad')
                            ubicacion = v.get('direccion')
                        elif tipo == 'crucero':
                            proveedor = v.get('compania') or v.get('embarcacion')
                        elif tipo == 'auto':
                            proveedor = v.get('empresa')
                        elif tipo == 'restaurante':
                            proveedor = v.get('nombre')
                            ubicacion = v.get('direccion')
                        elif tipo == 'espectaculo':
                            proveedor = v.get('evento')
                            ubicacion = v.get('venue')
                        elif tipo == 'actividad':
                            proveedor = v.get('proveedor') or v.get('nombre')
                            ubicacion = v.get('punto_encuentro')
                        elif tipo == 'tren':
                            proveedor = v.get('operador')
                        elif tipo == 'transfer':
                            proveedor = v.get('empresa')

                        viaje = Viaje(
                            user_id=connection.user_id,
                            tipo=tipo,
                            descripcion=v.get('descripcion', ''),
                            origen=v.get('origen', ''),
                            destino=v.get('destino', ''),
                            fecha_salida=fecha,
                            hora_salida=hora,
                            aerolinea=v.get('aerolinea', '') if tipo == 'vuelo' else None,
                            numero_vuelo=v.get('numero_vuelo', '') if tipo == 'vuelo' else None,
                            codigo_reserva=v.get('codigo_reserva', ''),
                            pasajeros=json.dumps(v.get('pasajeros', [])) if v.get('pasajeros') else None,
                            grupo_viaje=grupo,
                            # Nuevos campos multi-tipo
                            proveedor=proveedor,
                            ubicacion=ubicacion,
                            precio=precio,
                            raw_data=json.dumps(v, ensure_ascii=False)
                        )
                        db.session.add(viaje)
                        viajes_creados += 1
                        print(f"✅ Viaje creado: {v.get('origen')} → {v.get('destino')}")
                    
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
