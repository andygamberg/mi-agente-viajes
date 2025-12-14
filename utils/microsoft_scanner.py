"""
Microsoft Scanner - Mi Agente Viajes
MVP14h: Escaneo de emails de viajes usando Microsoft Graph API
"""
import base64
import re
import io
from datetime import datetime, timedelta
import requests as http_requests
import logging

logger = logging.getLogger(__name__)

from models import db, EmailConnection, Viaje
from utils.gmail_scanner import (
    WHITELIST_DOMAINS,
    is_whitelisted_sender,
    extract_text_from_pdf,
    check_duplicate,
    check_duplicate_by_content,
    MAX_EMAILS_PER_SCAN
)


def extract_body_microsoft(message):
    """
    Extrae texto del body de un mensaje de Microsoft Graph API.

    Args:
        message: dict del mensaje desde Graph API

    Returns:
        str: Texto del body
    """
    body = message.get('body', {})
    content = body.get('content', '')
    content_type = body.get('contentType', 'text')

    if content_type == 'html':
        # Limpiar HTML básico
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    return content.strip()


def extract_pdf_attachments_microsoft(access_token, message_id):
    """
    Extrae PDFs adjuntos de un email usando Graph API.

    Args:
        access_token: Token de acceso válido
        message_id: ID del mensaje

    Returns:
        list: Lista de dicts con 'filename' y 'data' (bytes)
    """
    attachments = []

    try:
        # Listar attachments
        response = http_requests.get(
            f'https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if response.status_code != 200:
            return attachments

        att_list = response.json().get('value', [])

        for att in att_list:
            filename = att.get('name', '')
            content_type = att.get('contentType', '')

            # Si es PDF
            if content_type == 'application/pdf' or filename.lower().endswith('.pdf'):
                content_bytes = att.get('contentBytes')
                if content_bytes:
                    try:
                        data = base64.b64decode(content_bytes)
                        attachments.append({
                            'filename': filename,
                            'data': data
                        })
                        print(f"    📎 PDF encontrado: {filename}")
                    except Exception as e:
                        print(f"    ⚠️ Error decodificando PDF {filename}: {e}")

    except Exception as e:
        print(f"    ⚠️ Error obteniendo attachments: {e}")

    return attachments


def get_full_email_content_microsoft(access_token, message):
    """
    Extrae todo el contenido del email: body + PDFs adjuntos.

    Args:
        access_token: Token de acceso válido
        message: dict del mensaje desde Graph API

    Returns:
        str: Texto combinado
    """
    subject = message.get('subject', '')
    body_text = extract_body_microsoft(message)
    message_id = message.get('id')

    # Extraer texto de PDFs adjuntos
    pdf_texts = []
    if message.get('hasAttachments'):
        attachments = extract_pdf_attachments_microsoft(access_token, message_id)

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


def search_travel_emails_microsoft(access_token, days_back=30):
    """
    Busca emails de viajes usando Microsoft Graph API.

    Args:
        access_token: Token de acceso válido
        days_back: Días hacia atrás para buscar

    Returns:
        list: Lista de mensajes
    """
    # Construir filtro para dominios principales
    top_domains = WHITELIST_DOMAINS[:20]

    # Graph API usa filtro OData
    # Formato: from/emailAddress/address eq 'x@domain.com'
    # Para OR múltiples: (cond1) or (cond2) or ...
    filters = []
    for domain in top_domains:
        # Nota: Graph API no soporta wildcards en filtros de texto
        # Alternativa: buscar sin filtro y filtrar en Python
        pass

    # Fecha límite
    date_limit = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        # Sin filtro de dominio en la query (lo hacemos después)
        # Ordenar por fecha descendente
        response = http_requests.get(
            'https://graph.microsoft.com/v1.0/me/messages',
            headers={'Authorization': f'Bearer {access_token}'},
            params={
                '$filter': f'receivedDateTime ge {date_limit}',
                '$orderby': 'receivedDateTime desc',
                '$top': 50,  # Máximo por request
                '$select': 'id,subject,from,receivedDateTime,hasAttachments,body'
            }
        )

        if response.status_code != 200:
            print(f"Error buscando emails: {response.status_code}")
            return []

        messages = response.json().get('value', [])
        return messages

    except Exception as e:
        print(f"Error searching Microsoft: {e}")
        return []


def scan_and_create_viajes_microsoft(user_id, days_back=30):
    """
    Escanea Microsoft emails y crea viajes (máx 5 emails por scan).

    Args:
        user_id: ID del usuario
        days_back: Días hacia atrás para buscar (30 por defecto, 180 en backfill)

    Returns:
        dict: Estadísticas del escaneo
    """
    from blueprints.microsoft_oauth import get_microsoft_credentials
    from utils.claude import extraer_info_con_claude
    import uuid

    print(f"    🔍 Microsoft scanner: user_id={user_id}, days_back={days_back}")

    results = {
        'emails_encontrados': 0,
        'emails_procesados': 0,
        'viajes_creados': 0,
        'viajes_duplicados': 0,
        'errors': []
    }

    connections = EmailConnection.query.filter_by(
        user_id=user_id, provider='microsoft', is_active=True
    ).all()

    if not connections:
        print(f"    ⚠️ No hay cuentas Microsoft conectadas para user {user_id}")
        results['errors'].append('No hay cuentas Microsoft conectadas')
        return results

    print(f"    📧 Encontradas {len(connections)} conexiones Microsoft")

    for conn in connections:
        try:
            # Detectar primera conexión para backfill
            is_first_scan = conn.last_scan is None or conn.emails_processed == 0
            scan_days = 180 if is_first_scan else days_back

            if is_first_scan:
                print(f"      🆕 Primera conexión detectada: {conn.email} - Backfill de {scan_days} días")
            else:
                print(f"      📬 Procesando cuenta: {conn.email} - Últimos {scan_days} días")

            creds = get_microsoft_credentials(user_id, email=conn.email)
            if not creds:
                print(f"      ⚠️ No se pudieron obtener credenciales para {conn.email}")
                continue

            access_token = creds['access_token']
            messages = search_travel_emails_microsoft(access_token, scan_days)
            print(f"      📥 {len(messages)} emails encontrados en {conn.email}")

            # Filtrar por remitentes whitelistados
            filtered_messages = []
            for msg in messages:
                from_email = msg.get('from', {}).get('emailAddress', {}).get('address', '')
                from_name = msg.get('from', {}).get('emailAddress', {}).get('name', '')
                subject = msg.get('subject', '')

                if is_whitelisted_sender(from_email, user_id):
                    filtered_messages.append(msg)
                    print(f"      ✅ Whitelisted: {from_name} <{from_email}> - {subject[:50]}")
                else:
                    print(f"      ⏭️ Remitente no whitelisted: {from_name} <{from_email}>")

            results['emails_encontrados'] += len(filtered_messages)
            print(f"      🎯 {len(filtered_messages)} emails whitelistados para procesar")

            emails_processed_count = 0

            # Limitar para evitar timeout
            for message in filtered_messages[:MAX_EMAILS_PER_SCAN]:
                try:
                    results['emails_procesados'] += 1
                    emails_processed_count += 1

                    # Obtener contenido completo
                    full_content = get_full_email_content_microsoft(access_token, message)

                    # Extraer con Claude
                    vuelos = extraer_info_con_claude(full_content)

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
                            print(f"        ⏭️ Saltando vuelo pasado en backfill: {fecha_str}")
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
            print(f"      ✅ Conexión actualizada: last_scan={conn.last_scan}, total_emails={conn.emails_processed}")

        except Exception as e:
            results['errors'].append(f"Error con {conn.email}: {str(e)}")

    return results
