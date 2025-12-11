"""
Blueprint de Gmail OAuth - Mi Agente Viajes
MVP14: Conexión OAuth para leer emails del usuario
Rutas: /conectar-gmail, /gmail-callback, /desconectar-gmail, /desconectar-gmail/<id>
"""
from flask import Blueprint, redirect, url_for, flash, request, session
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

# Scopes mínimos: solo lectura de emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# Credenciales OAuth desde variables de entorno (REQUERIDO)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

def get_redirect_uri():
    """Genera redirect URI según el entorno"""
    if os.getenv('DATABASE_URL'):  # Producción
        return 'https://mi-agente-viajes-454542398872.us-east1.run.app/gmail-callback'
    else:  # Desarrollo local
        return 'http://localhost:5000/gmail/callback'


# ============================================
# RUTAS OAUTH
# ============================================

@gmail_oauth_bp.route('/conectar-gmail')
@login_required
def conectar_gmail():
    """
    Inicia el flujo OAuth para conectar Gmail del usuario
    Construye la URL de autorización manualmente
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Error: Credenciales OAuth no configuradas', 'error')
        return redirect(url_for('viajes.preferencias'))
    
    try:
        # Construir URL de autorización manualmente
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
    """
    Callback de OAuth - intercambia código por tokens manualmente
    Sin validación de scopes
    """
    if 'error' in request.args:
        error = request.args.get('error')
        flash(f'Error de autorización: {error}', 'error')
        return redirect(url_for('viajes.preferencias'))
    
    try:
        code = request.args.get('code')
        if not code:
            flash('No se recibió código de autorización', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        # Intercambiar código por tokens usando requests directamente
        # Esto evita toda validación de scopes de las bibliotecas de Google
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
        
        # Crear credentials para obtener info del usuario
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Obtener email del usuario de Google
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        gmail_email = user_info.get('email')
        
        if not gmail_email:
            flash('No se pudo obtener el email de la cuenta', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        # Verificar si ya existe una conexión para este email
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
        
        return redirect(url_for('viajes.preferencias'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error conectando Gmail: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@gmail_oauth_bp.route('/desconectar-gmail/<int:connection_id>', methods=['POST'])
@login_required
def desconectar_gmail_by_id(connection_id):
    """Desconecta una cuenta Gmail específica por ID"""
    try:
        connection = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=current_user.id
        ).first()
        
        if not connection:
            flash('Conexión no encontrada', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        email = connection.email
        
        # Intentar revocar token en Google
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
    """Desconecta la primera cuenta Gmail activa (compatibilidad)"""
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
    """Obtiene todas las conexiones Gmail activas de un usuario"""
    return EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).all()


def get_user_gmail_connection(user_id):
    """Obtiene la primera conexión Gmail activa de un usuario"""
    return EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).first()
