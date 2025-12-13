"""
Blueprint de API - Mi Agente Viajes
Rutas: /api/*, /cron/*, /migrate-db, /assign-viajes-to-user
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, date
import json
import base64
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

from models import db, Viaje, User
from utils.claude import extraer_info_con_claude

api_bp = Blueprint('api', __name__)


# ============================================
# API ENDPOINTS
# ============================================

@api_bp.route('/api/viajes/count')
def viajes_count():
    hoy = date.today()
    count = Viaje.query.filter(Viaje.fecha_salida >= hoy).count()
    return {"count": count}


@api_bp.route('/api/process-email-text', methods=['POST'])
def api_process_email_text():
    try:
        data = request.get_json()
        email_text = data.get("email_text", "")
        if not email_text:
            return {"success": False, "error": "No email text provided"}, 400
        
        vuelos = extraer_info_con_claude(email_text)
        if not vuelos:
            return {"success": True, "vuelos_creados": 0}, 200
        
        vuelos_creados = 0
        for vuelo_data in vuelos:
            viaje = Viaje(
                tipo="vuelo",
                descripcion=f"{vuelo_data.get('origen')} -> {vuelo_data.get('destino')}",
                origen=vuelo_data.get("origen"),
                destino=vuelo_data.get("destino"),
                fecha_salida=vuelo_data.get("fecha_salida"),
                hora_salida=vuelo_data.get("hora_salida"),
                aerolinea=vuelo_data.get("aerolinea"),
                numero_vuelo=vuelo_data.get("numero_vuelo")
            )
            db.session.add(viaje)
            vuelos_creados += 1
        
        db.session.commit()
        return {"success": True, "vuelos_creados": vuelos_creados}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@api_bp.route('/api/auto-process', methods=['POST'])
def api_auto_process():
    """API endpoint para procesamiento automático de emails (sin confirmación)"""
    try:
        data = request.get_json()
        email_text = data.get('email_text', '')
        pdf_base64 = data.get('pdf_base64', '')
        
        texto_a_procesar = email_text
        
        if pdf_base64:
            import fitz
            pdf_bytes = base64.b64decode(pdf_base64)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texto_pdf = ""
            for page in doc:
                texto_pdf += page.get_text()
            doc.close()
            texto_a_procesar = texto_pdf if texto_pdf.strip() else email_text
        
        if not texto_a_procesar:
            return jsonify({'success': False, 'error': 'No hay texto'}), 400
        
        vuelos = extraer_info_con_claude(texto_a_procesar)
        
        if not vuelos:
            return jsonify({'success': True, 'vuelos_creados': 0}), 200
        
        vuelos_creados = 0
        for v in vuelos:
            viaje = Viaje(
                tipo='vuelo',
                descripcion=v.get('descripcion', f"{v.get('origen','')} → {v.get('destino','')}"),
                origen=v.get('origen'),
                destino=v.get('destino'),
                fecha_salida=v.get('fecha_salida'),
                hora_salida=v.get('hora_salida'),
                aerolinea=v.get('aerolinea'),
                numero_vuelo=v.get('numero_vuelo'),
                codigo_reserva=v.get('codigo_reserva')
            )
            db.session.add(viaje)
            vuelos_creados += 1
        
        db.session.commit()
        return jsonify({'success': True, 'vuelos_creados': vuelos_creados}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


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
    try:
        from utils.microsoft_scanner import scan_and_create_viajes_microsoft
        from models import EmailConnection

        logger.info("🔍 Microsoft scanner iniciado")

        # Obtener todos los usuarios con cuentas Microsoft activas
        connections = EmailConnection.query.filter_by(
            provider='microsoft', is_active=True
        ).all()

        if not connections:
            logger.info("ℹ️ No hay cuentas Microsoft activas")
            return {'success': True, 'message': 'No hay cuentas Microsoft activas'}, 200

        # Agrupar por user_id para evitar procesar el mismo usuario múltiples veces
        user_ids = list(set([conn.user_id for conn in connections]))

        logger.info(f"📧 Procesando {len(user_ids)} usuarios con cuentas Microsoft")

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
                logger.info(f"  👤 Usuario {user_id}...")
                result = scan_and_create_viajes_microsoft(user_id, days_back=30)

                total_results['usuarios_procesados'] += 1
                total_results['emails_encontrados'] += result.get('emails_encontrados', 0)
                total_results['emails_procesados'] += result.get('emails_procesados', 0)
                total_results['viajes_creados'] += result.get('viajes_creados', 0)
                total_results['viajes_duplicados'] += result.get('viajes_duplicados', 0)
                total_results['errors'].extend(result.get('errors', []))

                logger.info(f"    ✅ {result.get('viajes_creados', 0)} viajes creados, {result.get('emails_procesados', 0)} procesados, {result.get('emails_encontrados', 0)} encontrados")

            except Exception as e:
                error_msg = f"Error procesando usuario {user_id}: {str(e)}"
                logger.error(f"    ❌ {error_msg}")
                total_results['errors'].append(error_msg)

        logger.info(f"✅ Microsoft scanner completado: {total_results}")
        return {'success': True, 'result': total_results}, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error en Microsoft scanner: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@api_bp.route('/cron/check-flights', methods=['GET', 'POST'])
def cron_check_flights():
    return api_check_flights()


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


# ============================================
# MIGRACIÓN Y ADMINISTRACIÓN
# ============================================

@api_bp.route('/migrate-db')
def migrate_db():
    """Endpoint para migración de BD"""
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


@api_bp.route('/assign-viajes-to-user/<int:user_id>')
def assign_viajes(user_id):
    """Endpoint temporal para asignar viajes huérfanos a un usuario"""
    try:
        viajes_sin_user = Viaje.query.filter(Viaje.user_id.is_(None)).all()
        count = 0
        for v in viajes_sin_user:
            v.user_id = user_id
            count += 1
        db.session.commit()
        return {'success': True, 'viajes_asignados': count}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500
