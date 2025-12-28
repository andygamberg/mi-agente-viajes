"""
Blueprint de API - Mi Agente Viajes
Rutas: /api/*, /cron/*, /migrate-db
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, date
import json
import base64
import logging
import os
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

from models import db, Viaje, User
from utils.claude import extraer_info_con_claude
from utils.save_reservation import save_reservation
from blueprints.push import send_flight_change_notification

api_bp = Blueprint('api', __name__)


# ============================================
# FUNCIONES HELPER DE AUTENTICACIÓN
# ============================================

def verificar_cron_auth():
    """Verifica que la request venga de Cloud Scheduler o admin autorizado"""
    # Cloud Scheduler envía este header cuando llama endpoints
    if request.headers.get('X-Appengine-Cron') == 'true':
        return True
    # También aceptar X-CloudScheduler-JobName (alternativa)
    if request.headers.get('X-CloudScheduler-JobName'):
        return True
    # Permitir testing manual con admin key
    if verificar_admin_auth():
        return True
    return False


def verificar_admin_auth():
    """Verifica header de admin para endpoints sensibles"""
    expected = os.getenv('ADMIN_SECRET_KEY', 'dev-secret-123')
    return request.headers.get('X-Admin-Key') == expected


# ============================================
# API ENDPOINTS
# ============================================

@api_bp.route('/api/viajes/count')
def viajes_count():
    hoy = date.today()
    count = Viaje.query.filter(Viaje.fecha_salida >= hoy).count()
    return {"count": count}


@api_bp.route('/api/guardar-nombre-pax', methods=['POST'])
@login_required
def guardar_nombre_pax():
    """Guarda nombre y apellido del pasajero para detección automática"""
    try:
        data = request.get_json()
        nombre_pax = data.get('nombre_pax', '').strip().title()
        apellido_pax = data.get('apellido_pax', '').strip().title()

        current_user.nombre_pax = nombre_pax
        current_user.apellido_pax = apellido_pax
        db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/api/test-extraction', methods=['GET', 'POST'])
@login_required
def test_extraction():
    """Endpoint de prueba para ver qué detecta Claude (no guarda en BD)"""
    if request.method == 'GET':
        return '''
        <html>
        <head><title>Test Extracción</title></head>
        <body style="font-family: system-ui; max-width: 800px; margin: 40px auto; padding: 20px;">
            <h1>🧪 Test Extracción Multi-Tipo</h1>
            <form method="POST" enctype="multipart/form-data">
                <p><strong>Subir PDF:</strong></p>
                <input type="file" name="pdf" accept=".pdf"><br><br>
                <p><strong>O pegar texto del email:</strong></p>
                <textarea name="email_text" rows="10" style="width:100%"></textarea><br><br>
                <button type="submit" style="padding: 10px 20px; font-size: 16px;">Analizar con Claude</button>
            </form>
        </body>
        </html>
        '''

    # POST - procesar
    email_text = ""

    # Intentar leer PDF
    if 'pdf' in request.files:
        pdf_file = request.files['pdf']
        if pdf_file.filename:
            try:
                pdf_bytes = pdf_file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    email_text += page.get_text()
                doc.close()
            except Exception as e:
                return f"<pre>Error leyendo PDF: {e}</pre>"

    # Si no hay PDF, usar texto
    if not email_text.strip():
        email_text = request.form.get('email_text', '')

    if not email_text.strip():
        return "<pre>No se proporcionó contenido</pre>"

    # Extraer con Claude
    try:
        reservas = extraer_info_con_claude(email_text)

        if not reservas:
            return "<pre>Claude no detectó reservas en este documento</pre>"

        # Mostrar resultado formateado
        resultado_html = f'''
        <html>
        <head><title>Resultado</title></head>
        <body style="font-family: system-ui; max-width: 900px; margin: 40px auto; padding: 20px;">
            <h1>✅ {len(reservas)} reserva(s) detectada(s)</h1>
            <a href="/api/test-extraction">← Probar otro</a>
            <hr>
        '''

        for i, r in enumerate(reservas):
            tipo = r.get('tipo', 'desconocido')
            desc = r.get('descripcion', 'Sin descripción')
            resultado_html += f'<h2>{i+1}. [{tipo.upper()}] {desc}</h2>'
            resultado_html += f'<pre style="background:#f5f5f5; padding:15px; overflow-x:auto;">{json.dumps(r, indent=2, ensure_ascii=False)}</pre>'

        resultado_html += '</body></html>'
        return resultado_html

    except Exception as e:
        import traceback
        return f"<pre>Error: {e}\n\n{traceback.format_exc()}</pre>"


# ============================================
# CRON ENDPOINTS
# ============================================

@api_bp.route('/cron/process-emails', methods=['GET', 'POST'])
def process_emails_cron():
    """Procesa emails de misviajes@gamberg.com.ar - llamado por Cloud Scheduler"""
    if not verificar_cron_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        from gmail_to_db import process_emails
        result = process_emails()
        return {'success': True, 'result': result}, 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


@api_bp.route('/cron/process-microsoft-emails', methods=['GET', 'POST'])
def process_microsoft_emails_cron():
    """Procesa emails de Microsoft/Exchange - llamado por Cloud Scheduler"""
    if not verificar_cron_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        from utils.microsoft_scanner import scan_and_create_viajes_microsoft
        from models import EmailConnection

        print("🔍 Microsoft scanner iniciado")

        # Obtener todos los usuarios con cuentas Microsoft activas
        connections = EmailConnection.query.filter_by(
            provider='microsoft', is_active=True
        ).all()

        if not connections:
            print("ℹ️ No hay cuentas Microsoft activas")
            return {'success': True, 'message': 'No hay cuentas Microsoft activas'}, 200

        # Agrupar por user_id para evitar procesar el mismo usuario múltiples veces
        user_ids = list(set([conn.user_id for conn in connections]))

        print(f"📧 Procesando {len(user_ids)} usuarios con cuentas Microsoft")

        total_results = {
            'usuarios_procesados': 0,
            'emails_encontrados': 0,
            'emails_procesados': 0,
            'viajes_creados': 0,
            'viajes_duplicados': 0,
            'errors': []
        }

        for user_id in user_ids:
            try:
                print(f"  👤 Usuario {user_id}...")
                result = scan_and_create_viajes_microsoft(user_id, days_back=30)

                total_results['usuarios_procesados'] += 1
                total_results['emails_encontrados'] += result.get('emails_encontrados', 0)
                total_results['emails_procesados'] += result.get('emails_procesados', 0)
                total_results['viajes_creados'] += result.get('viajes_creados', 0)
                total_results['viajes_duplicados'] += result.get('viajes_duplicados', 0)
                total_results['errors'].extend(result.get('errors', []))

                print(f"    ✅ {result.get('viajes_creados', 0)} viajes creados, {result.get('emails_procesados', 0)} procesados, {result.get('emails_encontrados', 0)} encontrados")

            except Exception as e:
                error_msg = f"Error procesando usuario {user_id}: {str(e)}"
                logger.error(f"    ❌ {error_msg}")
                total_results['errors'].append(error_msg)

        print(f"✅ Microsoft scanner completado: {total_results}")
        return {'success': True, 'result': total_results}, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error en Microsoft scanner: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@api_bp.route('/cron/check-flights', methods=['GET', 'POST'])
def cron_check_flights():
    """Chequea vuelos y envía notificaciones de cambios"""
    if not verificar_cron_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        from flight_monitor import check_all_upcoming_flights
        from email_processor import send_email
        from models import User
        from blueprints.gmail_webhook import renew_expired_watches

        # Renovar Gmail watches expirados
        watch_result = renew_expired_watches()
        print(f"📧 Gmail watches: {watch_result['renewed']}/{watch_result['total']} renovados")
        if watch_result['errors']:
            print(f"  ⚠️ Errores: {watch_result['errors']}")

        # Verificar conexiones OAuth por expirar (Microsoft 90 días)
        oauth_result = check_expiring_oauth_connections()
        print(f"🔐 OAuth check: {oauth_result['warnings_sent']} avisos enviados de {oauth_result['connections_checked']} conexiones")

        cambios = check_all_upcoming_flights(db.session)

        emails_enviados = 0

        for item in cambios:
            viaje_id = item.get('vuelo_id')
            if not viaje_id:
                continue

            viaje = Viaje.query.get(viaje_id)
            if not viaje or not viaje.user_id:
                continue

            user = User.query.get(viaje.user_id)
            if not user or not user.notif_email_master:
                continue

            # Verificar preferencias por tipo de cambio
            for cambio in item.get('cambios', []):
                tipo = cambio.get('tipo')

                # Verificar si usuario quiere este tipo de notificación
                if tipo == 'delay' and not user.notif_delay:
                    continue
                if tipo == 'cancelacion' and not user.notif_cancelacion:
                    continue
                if tipo == 'gate' and not user.notif_gate:
                    continue

                # Preparar email según tipo
                numero_vuelo = item.get('numero_vuelo', '')
                ruta = item.get('ruta', '')
                fecha = item.get('fecha_salida')
                fecha_str = fecha.strftime('%d %b %Y') if fecha else ''

                if tipo == 'delay':
                    emoji = '⏰'
                    titulo = f'Delay en tu vuelo {numero_vuelo}'
                    mensaje = f'Tu vuelo tiene un retraso de {cambio.get("valor_nuevo", "")}'
                    color = '#d97706'  # naranja
                elif tipo == 'cancelacion':
                    emoji = '❌'
                    titulo = f'Vuelo {numero_vuelo} cancelado'
                    mensaje = 'Tu vuelo ha sido cancelado. Contactá a la aerolínea.'
                    color = '#dc2626'  # rojo
                elif tipo == 'gate':
                    emoji = '🚪'
                    titulo = f'Cambio de gate: {numero_vuelo}'
                    mensaje = f'Nueva puerta de embarque: {cambio.get("valor_nuevo", "")}'
                    color = '#2563eb'  # azul
                else:
                    emoji = '✈️'
                    titulo = f'Cambio en vuelo {numero_vuelo}'
                    mensaje = f'{tipo}: {cambio.get("valor_anterior", "")} → {cambio.get("valor_nuevo", "")}'
                    color = '#6b7280'  # gris

                subject = f'{emoji} {titulo}'

                body_html = f'''
                <html>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background: #f5f5f7;">
                    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; border-left: 4px solid {color};">
                        <h1 style="color: #1d1d1f; font-size: 24px; margin: 0 0 8px 0;">{emoji} {titulo}</h1>
                        <p style="color: #6e6e73; font-size: 14px; margin: 0 0 24px 0;">{ruta} - {fecha_str}</p>

                        <div style="background: #f5f5f7; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                            <p style="color: #1d1d1f; font-size: 16px; margin: 0;">{mensaje}</p>
                        </div>

                        <p style="color: #6e6e73; font-size: 14px; margin: 0;">
                            Información obtenida de FlightRadar24. Verificá con tu aerolínea para confirmar.
                        </p>
                    </div>
                    <p style="text-align: center; color: #6e6e73; font-size: 12px; margin-top: 16px;">
                        Mis Viajes - Tu asistente de viajes personal
                    </p>
                </body>
                </html>
                '''

                send_email(user.email, subject, body_html)
                emails_enviados += 1
                print(f'📧 Notificación enviada a {user.email}: {titulo}')

                # Enviar push notification si el usuario tiene suscripción activa
                try:
                    push_result = send_flight_change_notification(
                        user_id=user.id,
                        flight_info={
                            'numero': numero_vuelo,
                            'nueva_hora': cambio.get('valor_nuevo', ''),
                            'nueva_puerta': cambio.get('valor_nuevo', ''),
                            'mensaje': mensaje,
                            'url': '/'
                        },
                        change_type=tipo
                    )
                    if push_result.get('sent', 0) > 0:
                        print(f'🔔 Push enviado a user {user.id}: {titulo}')
                except Exception as e:
                    print(f'⚠️ Error enviando push: {e}')

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'cambios_detectados': len(cambios),
            'emails_enviados': emails_enviados,
            'gmail_watches_renewed': watch_result['renewed'],
            'oauth_warnings_sent': oauth_result['warnings_sent']
        }, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


def check_expiring_oauth_connections():
    """
    Detecta conexiones OAuth de Microsoft que están por expirar (60+ días sin uso)
    y envía email de aviso al usuario para que renueve.

    Microsoft refresh tokens expiran después de 90 días de inactividad.
    Enviamos aviso a los 60 días para dar tiempo al usuario.
    """
    from datetime import timedelta
    from models import EmailConnection, User
    from email_processor import send_email

    # Conexiones Microsoft sin actividad en 60+ días
    inactivity_threshold = datetime.utcnow() - timedelta(days=60)
    warning_cooldown = timedelta(days=7)  # No enviar más de 1 aviso por semana

    connections = EmailConnection.query.filter(
        EmailConnection.provider == 'microsoft',
        EmailConnection.is_active == True,
        db.or_(
            EmailConnection.last_scan == None,
            EmailConnection.last_scan < inactivity_threshold
        )
    ).all()

    warnings_sent = 0
    for conn in connections:
        # Verificar cooldown de avisos
        if conn.last_expiry_warning and conn.last_expiry_warning > datetime.utcnow() - warning_cooldown:
            continue

        user = User.query.get(conn.user_id)
        if not user or not user.email:
            continue

        # Calcular días de inactividad
        last_activity = conn.last_scan or conn.connected_at
        days_inactive = (datetime.utcnow() - last_activity).days if last_activity else 999

        print(f"⚠️ Conexión Microsoft por expirar: {conn.email} ({days_inactive} días inactiva)")

        # Enviar email de aviso
        subject = f"⚠️ Tu conexión de {conn.email} necesita renovarse"
        body_html = f'''
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1d1d1f;">Tu conexión de email necesita renovarse</h2>

            <p>Hola {user.nombre or 'usuario'},</p>

            <p>Tu cuenta <strong>{conn.email}</strong> lleva <strong>{days_inactive} días</strong> sin actividad
            en Mis Viajes. Por políticas de Microsoft, las conexiones expiran después de 90 días sin uso.</p>

            <p>Para evitar perder la conexión y tener que volver a autorizarla, te pedimos que:</p>

            <div style="background: #f5f5f7; padding: 20px; border-radius: 12px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Opción 1:</strong> Entrá a <a href="https://mi-agente-viajes-454542398872.us-east1.run.app/preferencias">Mis Viajes → Preferencias</a>
                y hacé click en "Reconectar" en tu cuenta Microsoft.</p>

                <p style="margin: 16px 0 0 0;"><strong>Opción 2:</strong> Reenviá cualquier email de reserva a tu cuenta conectada
                para reactivar la conexión automáticamente.</p>
            </div>

            <p style="color: #6e6e73;">Si no renovás la conexión, tus próximas reservas de viaje no se cargarán automáticamente
            y tendrás que volver a conectar tu cuenta.</p>

            <p>Saludos,<br>El equipo de Mis Viajes</p>
        </body>
        </html>
        '''

        result = send_email(user.email, subject, body_html)
        if result:
            conn.last_expiry_warning = datetime.utcnow()
            db.session.commit()
            warnings_sent += 1
            print(f"  ✅ Aviso enviado a {user.email}")

    return {'connections_checked': len(connections), 'warnings_sent': warnings_sent}


@api_bp.route('/cron/checkin-reminders', methods=['GET', 'POST'])
def checkin_reminders_cron():
    """Envía recordatorios de check-in 24h antes - llamado por Cloud Scheduler"""
    if not verificar_cron_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    from datetime import timedelta
    from models import Viaje, User
    from email_processor import send_email

    try:
        ahora = datetime.now()
        # Ventana: vuelos entre 23 y 25 horas desde ahora
        desde = ahora + timedelta(hours=23)
        hasta = ahora + timedelta(hours=25)

        # Buscar vuelos en esa ventana
        vuelos = Viaje.query.filter(
            Viaje.tipo == 'vuelo',
            Viaje.fecha_salida >= desde.date(),
            Viaje.fecha_salida <= hasta.date()
        ).all()

        # Filtrar por hora exacta (fecha_salida + hora_salida)
        vuelos_24h = []
        for v in vuelos:
            if not v.hora_salida:
                continue
            try:
                hora = datetime.strptime(v.hora_salida, '%H:%M').time()
                dt_vuelo = datetime.combine(v.fecha_salida, hora)
                if desde <= dt_vuelo <= hasta:
                    vuelos_24h.append(v)
            except:
                continue

        enviados = 0
        for vuelo in vuelos_24h:
            user = User.query.get(vuelo.user_id)
            if not user or not user.notif_email_master:
                continue

            # Evitar enviar duplicados (verificar si ya se envió)
            # Por ahora simple: enviar siempre, Cloud Scheduler corre cada 15min
            # y la ventana de 2h evita duplicados

            datos = vuelo.datos or {}
            aerolinea = datos.get('aerolinea') or vuelo.proveedor or ''
            numero_vuelo = datos.get('numero_vuelo') or ''
            origen = datos.get('origen') or vuelo.origen or ''
            destino = datos.get('destino') or vuelo.destino or ''
            hora_salida = vuelo.hora_salida or ''
            codigo = datos.get('codigo_reserva') or vuelo.codigo_reserva or ''

            subject = f'⏰ Check-in abierto: {aerolinea} {numero_vuelo} mañana'

            body_html = f'''
            <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background: #f5f5f7;">
                <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px;">
                    <h1 style="color: #1d1d1f; font-size: 24px; margin: 0 0 8px 0;">✈️ Recordatorio de Check-in</h1>
                    <p style="color: #6e6e73; font-size: 14px; margin: 0 0 24px 0;">Tu vuelo sale en aproximadamente 24 horas</p>

                    <div style="background: #f5f5f7; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                        <div style="font-size: 20px; font-weight: 600; color: #1d1d1f; margin-bottom: 4px;">
                            {aerolinea} {numero_vuelo}
                        </div>
                        <div style="font-size: 16px; color: #1d1d1f; margin-bottom: 12px;">
                            {origen} → {destino}
                        </div>
                        <div style="font-size: 14px; color: #6e6e73;">
                            Salida: {vuelo.fecha_salida.strftime('%d %b %Y')} a las {hora_salida}
                        </div>
                        {f'<div style="font-size: 14px; color: #6e6e73; margin-top: 4px;">Código: {codigo}</div>' if codigo else ''}
                    </div>

                    <p style="color: #1d1d1f; font-size: 14px; line-height: 1.5; margin: 0;">
                        La mayoría de aerolíneas permiten hacer check-in online 24 horas antes del vuelo.
                        Visitá el sitio web de <strong>{aerolinea}</strong> para hacer tu check-in.
                    </p>
                </div>
                <p style="text-align: center; color: #6e6e73; font-size: 12px; margin-top: 16px;">
                    Mis Viajes - Tu asistente de viajes personal
                </p>
            </body>
            </html>
            '''

            send_email(user.email, subject, body_html)
            enviados += 1
            print(f'📧 Check-in reminder enviado a {user.email} para {aerolinea} {numero_vuelo}')

        return {'success': True, 'enviados': enviados, 'vuelos_encontrados': len(vuelos_24h)}, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


@api_bp.route('/api/check-flights', methods=['GET'])
def api_check_flights():
    """
    Endpoint para chequear estado de vuelos próximos
    Returns JSON con cambios detectados
    """
    try:
        from flight_monitor import check_all_upcoming_flights
        cambios = check_all_upcoming_flights(db.session)
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'vuelos_chequeados': len(cambios),
            'cambios': cambios
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }, 500


@api_bp.route('/check-flights-manual')
@login_required
def check_flights_manual():
    """Página para chequear vuelos manualmente (para testing)"""
    try:
        from flight_monitor import check_all_upcoming_flights
        cambios = check_all_upcoming_flights(db.session)

        return render_template('check_flights.html',
                             cambios=cambios,
                             timestamp=datetime.now())
    except Exception as e:
        from flask import flash
        flash(f'Error chequeando vuelos: {str(e)}', 'error')
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/debug/vuelos', methods=['GET'])
def debug_vuelos():
    """Debug: ver vuelos próximos en BD (requiere admin auth)"""
    if not verificar_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    from datetime import date

    # Buscar vuelo específico si se pasa query param
    numero = request.args.get('numero', '')

    query = Viaje.query.filter(Viaje.tipo == 'vuelo')

    if numero:
        # Buscar por número de vuelo en datos JSON o proveedor
        query = query.filter(
            db.or_(
                Viaje.datos['numero_vuelo'].astext.ilike(f'%{numero}%'),
                Viaje.proveedor.ilike(f'%{numero}%')
            )
        )
    else:
        # Solo vuelos futuros
        query = query.filter(Viaje.fecha_salida >= date.today())

    vuelos = query.order_by(Viaje.fecha_salida).limit(20).all()

    result = []
    for v in vuelos:
        # datos puede ser dict o string JSON
        if isinstance(v.datos, dict):
            datos = v.datos
        elif v.datos:
            datos = json.loads(v.datos)
        else:
            datos = {}
        result.append({
            'id': v.id,
            'user_id': v.user_id,
            'origen': v.origen,
            'destino': v.destino,
            'fecha_salida': str(v.fecha_salida),
            'hora_salida': v.hora_salida,
            'proveedor': v.proveedor,
            'numero_vuelo_col': v.numero_vuelo,  # Columna directa
            'numero_vuelo_datos': datos.get('numero_vuelo'),  # Desde JSON datos
            'codigo_reserva': v.codigo_reserva or datos.get('codigo_reserva'),
            'aerolinea': datos.get('aerolinea'),
            'status_fr24': v.status_fr24,
            'delay_minutos': v.delay_minutos,
            'ultima_actualizacion_fr24': str(v.ultima_actualizacion_fr24) if v.ultima_actualizacion_fr24 else None,
            'source': v.source,
            'created_at': str(v.creado) if v.creado else None
        })

    return jsonify({
        'count': len(result),
        'query': numero or 'próximos',
        'vuelos': result
    })


@api_bp.route('/api/debug/fix-vuelo/<int:vuelo_id>', methods=['POST'])
def fix_vuelo(vuelo_id):
    """Fix: resetear datos FR24 de un vuelo para re-monitoreo"""
    if not verificar_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    viaje = Viaje.query.get(vuelo_id)
    if not viaje:
        return jsonify({'error': 'Vuelo no encontrado'}), 404

    # Guardar valores anteriores
    old_data = {
        'fecha_salida': str(viaje.fecha_salida),
        'hora_salida': viaje.hora_salida,
        'status_fr24': viaje.status_fr24,
        'delay_minutos': viaje.delay_minutos
    }

    # Obtener nueva fecha del body si se proporciona
    data = request.get_json() or {}
    if 'fecha_salida' in data:
        from datetime import datetime as dt
        viaje.fecha_salida = dt.fromisoformat(data['fecha_salida'])
    if 'hora_salida' in data:
        viaje.hora_salida = data['hora_salida']

    # Resetear datos FR24 para que se vuelva a monitorear
    viaje.status_fr24 = None
    viaje.delay_minutos = None
    viaje.ultima_actualizacion_fr24 = None

    db.session.commit()

    return jsonify({
        'success': True,
        'vuelo_id': vuelo_id,
        'old': old_data,
        'new': {
            'fecha_salida': str(viaje.fecha_salida),
            'hora_salida': viaje.hora_salida,
            'status_fr24': viaje.status_fr24
        }
    })


@api_bp.route('/api/debug/delete-vuelo/<int:vuelo_id>', methods=['DELETE'])
def delete_vuelo(vuelo_id):
    """Eliminar vuelo duplicado (admin only)"""
    if not verificar_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    viaje = Viaje.query.get(vuelo_id)
    if not viaje:
        return jsonify({'error': 'Vuelo no encontrado'}), 404

    info = {
        'id': viaje.id,
        'numero_vuelo': viaje.numero_vuelo,
        'origen': viaje.origen,
        'destino': viaje.destino,
        'fecha_salida': str(viaje.fecha_salida)
    }

    db.session.delete(viaje)
    db.session.commit()

    return jsonify({'success': True, 'deleted': info})


# ============================================
# MIGRACIÓN Y ADMINISTRACIÓN
# ============================================

@api_bp.route('/migrate-db')
def migrate_db():
    """Endpoint para migración de BD - requiere autenticación"""
    if not verificar_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        with db.engine.connect() as conn:
            # ========================================
            # Migraciones existentes
            # ========================================
            
            # Tabla viaje
            conn.execute(db.text("ALTER TABLE viaje ADD COLUMN IF NOT EXISTS user_id INTEGER"))
            
            # Tabla user - campos básicos
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS nombre_pax VARCHAR(50)"))
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS apellido_pax VARCHAR(50)"))
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS calendar_token VARCHAR(36)"))
            
            # MVP11: Campo para toggle de combinación de vuelos
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS combinar_vuelos BOOLEAN DEFAULT TRUE"))

            # MVP13: Campos de notificaciones
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS notif_email_master BOOLEAN DEFAULT TRUE"))
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS notif_delay BOOLEAN DEFAULT TRUE"))
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS notif_cancelacion BOOLEAN DEFAULT TRUE"))
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS notif_gate BOOLEAN DEFAULT TRUE"))

            # ========================================
            # MVP14: Gmail Integration
            # ========================================
            
            # Campo custom_senders en user (whitelist personal)
            conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS custom_senders TEXT"))
            
            # Crear tabla email_connection si no existe
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS email_connection (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id),
                    provider VARCHAR(20) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expiry TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_scan TIMESTAMP,
                    last_error TEXT,
                    emails_processed INTEGER DEFAULT 0,
                    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Índice para búsqueda rápida por user_id
            conn.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_email_connection_user_id
                ON email_connection(user_id)
            """))

            # MVP14c: Campos para Gmail Push
            conn.execute(db.text("ALTER TABLE email_connection ADD COLUMN IF NOT EXISTS history_id VARCHAR(50)"))
            conn.execute(db.text("ALTER TABLE email_connection ADD COLUMN IF NOT EXISTS watch_expiration TIMESTAMP"))

            # MVP16: Campo para tracking de avisos de expiración OAuth
            conn.execute(db.text("ALTER TABLE email_connection ADD COLUMN IF NOT EXISTS last_expiry_warning TIMESTAMP"))

            # MVP15: Aumentar límite de codigo_reserva para expediciones/charters
            conn.execute(db.text("ALTER TABLE viaje ALTER COLUMN codigo_reserva TYPE VARCHAR(255)"))

            # Campos FR24 para monitoreo de vuelos
            conn.execute(db.text("ALTER TABLE viaje ADD COLUMN IF NOT EXISTS ultima_actualizacion_fr24 TIMESTAMP"))
            conn.execute(db.text("ALTER TABLE viaje ADD COLUMN IF NOT EXISTS status_fr24 VARCHAR(50)"))
            conn.execute(db.text("ALTER TABLE viaje ADD COLUMN IF NOT EXISTS delay_minutos INTEGER"))

            # Códigos alternativos de reserva (para detectar duplicados con múltiples códigos)
            conn.execute(db.text("ALTER TABLE viaje ADD COLUMN IF NOT EXISTS codigos_alternativos TEXT"))

            conn.commit()
        
        # ========================================
        # Actualizar datos existentes
        # ========================================
        
        # Generar tokens para usuarios existentes que no tienen
        users_sin_token = User.query.filter(User.calendar_token.is_(None)).all()
        for user in users_sin_token:
            user.regenerate_calendar_token()
        
        # MVP11: Setear combinar_vuelos=True para usuarios existentes que tengan NULL
        users_sin_combinar = User.query.filter(User.combinar_vuelos.is_(None)).all()
        for user in users_sin_combinar:
            user.combinar_vuelos = True

        # MVP13: Setear notificaciones activas para usuarios existentes
        users_sin_notif = User.query.filter(User.notif_email_master.is_(None)).all()
        for user in users_sin_notif:
            user.notif_email_master = True
            user.notif_delay = True
            user.notif_cancelacion = True
            user.notif_gate = True

        db.session.commit()

        return {
            'success': True,
            'message': 'Migración completada (incluye MVP14: EmailConnection)',
            'tokens_generados': len(users_sin_token),
            'combinar_vuelos_seteados': len(users_sin_combinar),
            'notificaciones_seteadas': len(users_sin_notif)
        }, 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


@api_bp.route('/migrate-multi-type')
def migrate_multi_type():
    """Ejecuta migración para campos multi-tipo"""
    try:
        from sqlalchemy import text
        columns_to_add = [
            ("ubicacion", "VARCHAR(500)"),
            ("proveedor", "VARCHAR(200)"),
            ("precio", "VARCHAR(100)"),
            ("raw_data", "TEXT"),
        ]

        results = []
        for col_name, col_type in columns_to_add:
            try:
                db.session.execute(text(f"ALTER TABLE viaje ADD COLUMN {col_name} {col_type}"))
                results.append(f"✅ {col_name} agregada")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    results.append(f"ℹ️ {col_name} ya existe")
                else:
                    results.append(f"❌ {col_name}: {e}")

        db.session.commit()
        return {"status": "ok", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
