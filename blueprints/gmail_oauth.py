"""
Blueprint de Gmail OAuth - Mi Agente Viajes
MVP14: Conexión OAuth + Escaneo de emails
MVP14f: Fix multi-cuenta - credentials y watch por email específico
Rutas: /conectar-gmail, /gmail-callback, /desconectar-gmail
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
        return redirect(url_for('viajes.perfil'))
    
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
        return redirect(url_for('viajes.perfil'))


@gmail_oauth_bp.route('/gmail-callback')
@login_required
def gmail_callback():
    """Callback de OAuth - intercambia código por tokens"""
    if 'error' in request.args:
        error = request.args.get('error')
        flash(f'Error de autorización: {error}', 'error')
        return redirect(url_for('viajes.perfil'))
    
    try:
        code = request.args.get('code')
        if not code:
            flash('No se recibió código de autorización', 'error')
            return redirect(url_for('viajes.perfil'))
        
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
            return redirect(url_for('viajes.perfil'))
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        if not access_token:
            flash('No se recibió access token', 'error')
            return redirect(url_for('viajes.perfil'))
        
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
            return redirect(url_for('viajes.perfil'))
        
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

        # MVP14f: Activar watch para LA CUENTA ESPECÍFICA recién conectada
        from blueprints.gmail_webhook import setup_gmail_watch
        watch_result = setup_gmail_watch(current_user.id, gmail_email=gmail_email)
        if watch_result.get('success'):
            print(f"✅ Watch activado para {gmail_email}")
        else:
            print(f"⚠️ Error activando watch para {gmail_email}: {watch_result.get('error')}")

        return redirect(url_for('viajes.perfil'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error conectando Gmail: {str(e)}', 'error')
        return redirect(url_for('viajes.perfil'))


@gmail_oauth_bp.route('/desconectar-gmail/<int:connection_id>', methods=['POST'])
@login_required
def desconectar_gmail_by_id(connection_id):
    """Desconecta OAuth de Gmail (usado por toggle) - el email queda en la lista"""
    try:
        connection = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=current_user.id
        ).first()

        if not connection:
            flash('Conexión no encontrada', 'error')
            return redirect(url_for('viajes.perfil'))

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

        # Solo eliminar conexión OAuth
        db.session.delete(connection)
        db.session.commit()

        flash(f'Gmail desconectado: {email}', 'success')
        return redirect(url_for('viajes.perfil'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error desconectando: {str(e)}', 'error')
        return redirect(url_for('viajes.perfil'))


@gmail_oauth_bp.route('/quitar-email-gmail/<int:connection_id>', methods=['POST'])
@login_required
def quitar_email_gmail(connection_id):
    """Elimina email completo (usado por botón Quitar) - desconecta OAuth y quita de lista"""
    try:
        connection = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=current_user.id
        ).first()

        if not connection:
            flash('Conexión no encontrada', 'error')
            return redirect(url_for('viajes.perfil'))

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

        # Eliminar conexión OAuth
        db.session.delete(connection)

        # También eliminar UserEmail si existe
        from models import UserEmail
        user_email = UserEmail.query.filter_by(
            user_id=current_user.id,
            email=email
        ).first()
        if user_email:
            db.session.delete(user_email)

        db.session.commit()

        flash(f'Email eliminado: {email}', 'success')
        return redirect(url_for('viajes.perfil'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error eliminando email: {str(e)}', 'error')
        return redirect(url_for('viajes.perfil'))


@gmail_oauth_bp.route('/desconectar-gmail', methods=['POST'])
@login_required
def desconectar_gmail():
    """Desconecta la primera cuenta Gmail activa (legacy)"""
    try:
        connection = EmailConnection.query.filter_by(
            user_id=current_user.id,
            provider='gmail',
            is_active=True
        ).first()
        
        if not connection:
            flash('No tenés Gmail conectado', 'info')
            return redirect(url_for('viajes.perfil'))
        
        return desconectar_gmail_by_id(connection.id)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error desconectando: {str(e)}', 'error')
        return redirect(url_for('viajes.perfil'))


# ============================================
# HELPERS - Multi-cuenta ready
# ============================================

def get_gmail_credentials(user_id, gmail_email=None, connection_id=None):
    """
    Obtiene credenciales válidas de Gmail para una cuenta específica.
    
    Args:
        user_id: ID del usuario
        gmail_email: Email específico (preferido)
        connection_id: ID de conexión alternativo
    
    Returns:
        Credentials object o None
    
    Nota: Para multi-proveedor futuro (Outlook, Apple), crear funciones similares
    o generalizar con get_email_credentials(user_id, provider, email)
    """
    # Buscar conexión específica
    if connection_id:
        connection = EmailConnection.query.filter_by(
            id=connection_id, user_id=user_id, is_active=True
        ).first()
    elif gmail_email:
        connection = EmailConnection.query.filter_by(
            user_id=user_id, provider='gmail', email=gmail_email, is_active=True
        ).first()
    else:
        # Fallback legacy - primera conexión (evitar en código nuevo)
        connection = EmailConnection.query.filter_by(
            user_id=user_id, provider='gmail', is_active=True
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
            print(f"🔄 Refrescando token expirado para {connection.email}...")
            credentials.refresh(Request())
            connection.access_token = credentials.token
            connection.token_expiry = credentials.expiry
            connection.updated_at = datetime.utcnow()
            connection.last_error = None  # Limpiar error anterior
            db.session.commit()
            print(f"✅ Token refrescado exitosamente para {connection.email}")
        except Exception as e:
            error_msg = f"Error refrescando token: {str(e)}"
            print(f"❌ {error_msg} para {connection.email}")
            import traceback
            traceback.print_exc()
            connection.last_error = error_msg
            connection.is_active = False
            db.session.commit()
            return None
    
    return credentials


def get_user_gmail_connections(user_id):
    """Obtiene todas las conexiones Gmail activas de un usuario"""
    return EmailConnection.query.filter_by(
        user_id=user_id, provider='gmail', is_active=True
    ).all()


def get_user_email_connections(user_id, provider=None):
    """
    Obtiene conexiones de email de un usuario.
    
    Args:
        user_id: ID del usuario
        provider: 'gmail', 'outlook', 'apple' o None para todos
    
    Returns:
        Lista de EmailConnection
    """
    query = EmailConnection.query.filter_by(user_id=user_id, is_active=True)
    if provider:
        query = query.filter_by(provider=provider)
    return query.all()
