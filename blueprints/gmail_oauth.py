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

import google.oauth2.credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
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
    # En producción usar la URL de Cloud Run
    if os.getenv('DATABASE_URL'):  # Estamos en producción
        return 'https://mi-agente-viajes-454542398872.us-east1.run.app/gmail-callback'
    else:  # Desarrollo local
        return 'http://localhost:5000/gmail/callback'


def create_oauth_flow():
    """Crea el flow de OAuth con la configuración correcta"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("GOOGLE_OAUTH_CLIENT_ID y GOOGLE_OAUTH_CLIENT_SECRET deben estar configurados")
    
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [get_redirect_uri()]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )
    
    return flow


# ============================================
# RUTAS OAUTH
# ============================================

@gmail_oauth_bp.route('/conectar-gmail')
@login_required
def conectar_gmail():
    """
    Inicia el flujo OAuth para conectar Gmail del usuario
    Redirige a Google para autorización
    Permite múltiples cuentas Gmail
    """
    try:
        flow = create_oauth_flow()
        
        # Generar URL de autorización
        authorization_url, state = flow.authorization_url(
            access_type='offline',  # Para obtener refresh_token
            include_granted_scopes='true',
            prompt='consent'  # Forzar pantalla de consentimiento para obtener refresh_token
        )
        
        # Guardar state en sesión para verificar después
        session['oauth_state'] = state
        
        return redirect(authorization_url)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error iniciando conexión: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@gmail_oauth_bp.route('/gmail-callback')
@login_required
def gmail_callback():
    """
    Callback de OAuth - recibe el código de autorización
    Intercambia por tokens y guarda en BD
    """
    # Verificar que no haya error
    if 'error' in request.args:
        error = request.args.get('error')
        flash(f'Error de autorización: {error}', 'error')
        return redirect(url_for('viajes.preferencias'))
    
    try:
        flow = create_oauth_flow()
        
        # Obtener el código de autorización
        code = request.args.get('code')
        if not code:
            flash('No se recibió código de autorización', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        # Intercambiar código por tokens (bypass scope validation)
        # Usamos fetch_token directo del oauth2session para evitar validación estricta
        token_response = flow.oauth2session.fetch_token(
            flow.client_config['token_uri'],
            code=code,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Crear credentials manualmente
        credentials = google.oauth2.credentials.Credentials(
            token=token_response['access_token'],
            refresh_token=token_response.get('refresh_token'),
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
        
        # Verificar si ya existe una conexión para este email específico
        existing = EmailConnection.query.filter_by(
            user_id=current_user.id,
            provider='gmail',
            email=gmail_email
        ).first()
        
        if existing:
            # Actualizar tokens existentes
            existing.access_token = credentials.token
            existing.refresh_token = credentials.refresh_token or existing.refresh_token
            existing.token_expiry = None  # No tenemos expiry directo del token_response
            existing.is_active = True
            existing.last_error = None
            existing.updated_at = datetime.utcnow()
            flash(f'Gmail reconectado: {gmail_email}', 'success')
        else:
            # Crear nueva conexión
            connection = EmailConnection(
                user_id=current_user.id,
                provider='gmail',
                email=gmail_email,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=None,
                is_active=True
            )
            db.session.add(connection)
            flash(f'Gmail conectado: {gmail_email}', 'success')
        
        db.session.commit()
        
        # Limpiar state de la sesión
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
    """
    Desconecta una cuenta Gmail específica por ID
    """
    try:
        # Buscar conexión por ID y verificar que pertenezca al usuario
        connection = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=current_user.id
        ).first()
        
        if not connection:
            flash('Conexión no encontrada', 'error')
            return redirect(url_for('viajes.preferencias'))
        
        email = connection.email
        
        # Intentar revocar token en Google (opcional, puede fallar)
        try:
            if connection.access_token:
                import requests
                requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': connection.access_token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
        except:
            pass  # Si falla la revocación, continuamos igual
        
        # Eliminar la conexión de la BD (hard delete)
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
    """
    Desconecta la primera cuenta Gmail activa del usuario
    (Mantener por compatibilidad)
    """
    try:
        # Buscar primera conexión activa
        connection = EmailConnection.query.filter_by(
            user_id=current_user.id,
            provider='gmail',
            is_active=True
        ).first()
        
        if not connection:
            flash('No tenés Gmail conectado', 'info')
            return redirect(url_for('viajes.preferencias'))
        
        # Usar la función por ID
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
    """
    Obtiene credenciales válidas de Gmail para un usuario
    Refresca el token si está expirado
    Returns: Credentials object o None
    """
    connection = EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).first()
    
    if not connection:
        return None
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return None
    
    # Crear objeto Credentials
    credentials = Credentials(
        token=connection.access_token,
        refresh_token=connection.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        expiry=connection.token_expiry
    )
    
    # Verificar si necesita refresh
    if credentials.expired and credentials.refresh_token:
        try:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            # Actualizar tokens en BD
            connection.access_token = credentials.token
            connection.token_expiry = credentials.expiry
            connection.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            # Token inválido, marcar conexión como error
            connection.last_error = str(e)
            connection.is_active = False
            db.session.commit()
            return None
    
    return credentials


def get_user_gmail_connections(user_id):
    """
    Obtiene todas las conexiones Gmail activas de un usuario
    Returns: Lista de EmailConnection
    """
    return EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).all()


def get_user_gmail_connection(user_id):
    """
    Obtiene la primera conexión Gmail activa de un usuario
    Returns: EmailConnection o None
    """
    return EmailConnection.query.filter_by(
        user_id=user_id,
        provider='gmail',
        is_active=True
    ).first()
