"""
Blueprint de Gmail OAuth - Mi Agente Viajes
MVP14: Conexión OAuth + Escaneo de emails
Rutas: /conectar-gmail, /gmail-callback, /desconectar-gmail, /escanear-gmail
"""
from flask import Blueprint, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os
import json
import requests as http_requests

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from models import db, EmailConnection

gmail_oauth_bp = Blueprint('gmail_oauth', __name__)

# ============================================
# CONFIGURACIÓN OAUTH
# ============================================

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

def get_redirect_uri():
    if os.getenv('DATABASE_URL'):
        return 'https://mi-agente-viajes-454542398872.us-east1.run.app/gmail-callback'
    else:
        return 'http://localhost:5000/gmail/callback'


# ============================================
# RUTAS OAUTH
# ============================================

@gmail_oauth_bp.route('/conectar-gmail')
@login_required
def conectar_gmail():
    """Inicia el flujo OAuth para conectar Gmail"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Error: Credenciales OAuth no configuradas', 'error')
        return redirect(url_for('viajes.preferencias'))
    
    try:
        import secrets
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        params = {
            'client_id': GOOGLE_CLIENT_ID,
            'redirect_uri': get_redirect_uri(),
            'response_type': 'code',
            'scope': ' '.join(SCOPES),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        
        auth_url = 'https://accounts.google.com/o/oauth2/auth?' + '&'.join(
            f'{k}={v}' for k, v in params.items()
        )
        
        return redirect(auth_url)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error iniciando conexión: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@gmail_oauth_bp.route('/gmail-callback')
@login_required
def gmail_callback():
    """Callback de OAuth - intercambia código por tokens"""
    if 'error' in request.args:
        error = request.args.get('error')
        flash(f'Error de autorización: {error}', 'error')
        return redirect(url_for('viajes.preferencias'))
    
    try:
        code = request.args.get('code')
        if not code:
            flash('No se recibió código de autorización', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        # Token exchange manual
        token_response = http_requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': get_redirect_uri(),
                'grant_type': 'authorization_code'
            }
        )
        
        if token_response.status_code != 200:
            error_data = token_response.json()
            flash(f'Error obteniendo token: {error_data.get("error_description", "Unknown")}', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        if not access_token:
            flash('No se recibió access token', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        gmail_email = user_info.get('email')
        
        if not gmail_email:
            flash('No se pudo obtener el email de la cuenta', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        existing = EmailConnection.query.filter_by(
            user_id=current_user.id,
            provider='gmail',
            email=gmail_email
        ).first()
        
        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.token_expiry = None
            existing.is_active = True
            existing.last_error = None
            existing.updated_at = datetime.utcnow()
            flash(f'Gmail reconectado: {gmail_email}', 'success')
        else:
            connection = EmailConnection(
                user_id=current_user.id,
                provider='gmail',
                email=gmail_email,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=None,
                is_active=True
            )
            db.session.add(connection)
            flash(f'Gmail conectado: {gmail_email}', 'success')
        
        db.session.commit()
        session.pop('oauth_state', None)

        # MVP14c: Activar Gmail Push Notifications
        from blueprints.gmail_webhook import setup_gmail_watch
        watch_result = setup_gmail_watch(current_user.id)
        if watch_result.get('success'):
            print(f"✅ Watch activado para {current_user.email}")

        return redirect(url_for('viajes.preferencias'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error conectando Gmail: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@gmail_oauth_bp.route('/desconectar-gmail/<int:connection_id>', methods=['POST'])
@login_required
def desconectar_gmail_by_id(connection_id):
    """Desconecta una cuenta Gmail específica"""
    try:
        connection = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=current_user.id
        ).first()
        
        if not connection:
            flash('Conexión no encontrada', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        email = connection.email
        
        try:
            if connection.access_token:
                http_requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': connection.access_token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
        except:
            pass
        
        db.session.delete(connection)
        db.session.commit()
        
        flash(f'Gmail desconectado: {email}', 'success')
        return redirect(url_for('viajes.preferencias'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error desconectando: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@gmail_oauth_bp.route('/desconectar-gmail', methods=['POST'])
@login_required
def desconectar_gmail():
    """Desconecta la primera cuenta Gmail activa"""
    try:
        connection = EmailConnection.query.filter_by(
            user_id=current_user.id,
            provider='gmail',
            is_active=True
        ).first()
        
        if not connection:
            flash('No tenés Gmail conectado', 'info')
            return redirect(url_for('viajes.preferencias'))
        
        return desconectar_gmail_by_id(connection.id)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error desconectando: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


# ============================================
# ESCANEO DE EMAILS (MVP14b)
# ============================================

@gmail_oauth_bp.route('/escanear-gmail', methods=['POST'])
@login_required
def escanear_gmail():
    """
    Escanea emails de las cuentas Gmail conectadas
    Busca confirmaciones de viaje y las procesa
    """
    try:
        from utils.gmail_scanner import scan_and_create_viajes
        
        # Obtener parámetros
        days_back = request.form.get('days_back', 30, type=int)
        if days_back > 90:
            days_back = 90  # Límite máximo
        
        # Ejecutar escaneo
        results = scan_and_create_viajes(current_user.id, days_back=days_back)
        
        # Mostrar resultados
        if results['viajes_creados'] > 0:
            flash(f"✓ {results['viajes_creados']} viaje(s) encontrado(s) y agregado(s)", 'success')
        elif results['viajes_duplicados'] > 0:
            flash(f"No se encontraron viajes nuevos ({results['viajes_duplicados']} ya existían)", 'info')
        else:
            flash('No se encontraron emails de viajes', 'info')
        
        if results['errors']:
            for error in results['errors'][:3]:  # Mostrar máximo 3 errores
                flash(f"Error: {error}", 'error')
        
        return redirect(url_for('viajes.preferencias'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error escaneando: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@gmail_oauth_bp.route('/api/escanear-gmail', methods=['POST'])
@login_required
def api_escanear_gmail():
    """
    API endpoint para escaneo (retorna JSON)
    Útil para llamadas AJAX desde frontend
    """
    try:
        from utils.gmail_scanner import scan_and_create_viajes
        
        data = request.get_json() or {}
        days_back = min(data.get('days_back', 30), 90)
        
        results = scan_and_create_viajes(current_user.id, days_back=days_back)
        
        return jsonify({
            'success': True,
            'emails_scanned': results.get('emails_scanned', 0),
            'viajes_creados': results.get('viajes_creados', 0),
            'viajes_duplicados': results.get('viajes_duplicados', 0),
            'errors': results.get('errors', [])
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# HELPERS
# ============================================

def get_gmail_credentials(user_id):
    """Obtiene credenciales válidas de Gmail para un usuario"""
    connection = EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).first()
    
    if not connection or not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return None
    
    credentials = Credentials(
        token=connection.access_token,
        refresh_token=connection.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        expiry=connection.token_expiry
    )
    
    if credentials.expired and credentials.refresh_token:
        try:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            connection.access_token = credentials.token
            connection.token_expiry = credentials.expiry
            connection.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            connection.last_error = str(e)
            connection.is_active = False
            db.session.commit()
            return None
    
    return credentials


def get_user_gmail_connections(user_id):
    """Obtiene todas las conexiones Gmail activas"""
    return EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).all()


def get_user_gmail_connection(user_id):
    """Obtiene la primera conexión Gmail activa"""
    return EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).first()
