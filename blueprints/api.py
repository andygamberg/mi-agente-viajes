"""
Blueprint de API - Mi Agente Viajes
Rutas: /api/*, /cron/*, /migrate-db, /assign-viajes-to-user
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, date
import json
import base64

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
