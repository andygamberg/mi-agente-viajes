"""
Blueprint de Microsoft OAuth - Mi Agente Viajes
MVP14h: Conexión OAuth + Escaneo de emails (Outlook, Hotmail, Exchange 365)
Rutas: /conectar-microsoft, /microsoft-callback, /desconectar-microsoft
"""
from flask import Blueprint, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from datetime import datetime
import os
import requests as http_requests
import logging

logger = logging.getLogger(__name__)

from models import db, EmailConnection

microsoft_oauth_bp = Blueprint('microsoft_oauth', __name__)

# ============================================
# CONFIGURACIÓN OAUTH
# ============================================

SCOPES = [
    'openid',
    'profile',
    'email',
    'User.Read',
    'Mail.Read',
    'offline_access'
]

MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')

def get_redirect_uri():
    if os.getenv('DATABASE_URL'):
        return 'https://mi-agente-viajes-454542398872.us-east1.run.app/microsoft-callback'
    else:
        return 'http://localhost:5000/microsoft-callback'


# ============================================
# RUTAS OAUTH
# ============================================

@microsoft_oauth_bp.route('/conectar-microsoft')
@login_required
def conectar_microsoft():
    """Inicia el flujo OAuth para conectar Microsoft (Outlook/365)"""
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        flash('Error: Credenciales OAuth no configuradas', 'error')
        return redirect(url_for('viajes.preferencias'))

    try:
        import secrets
        state = secrets.token_urlsafe(32)
        session['ms_oauth_state'] = state

        params = {
            'client_id': MICROSOFT_CLIENT_ID,
            'redirect_uri': get_redirect_uri(),
            'response_type': 'code',
            'scope': ' '.join(SCOPES),
            'response_mode': 'query',
            'state': state
        }

        auth_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?' + '&'.join(
            f'{k}={v}' for k, v in params.items()
        )

        # Guardar origen para redirect post-OAuth
        if request.args.get('from_wizard'):
            session['from_wizard'] = True

        return redirect(auth_url)

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error iniciando conexión: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@microsoft_oauth_bp.route('/microsoft-callback')
@login_required
def microsoft_callback():
    """Callback de OAuth - intercambia código por tokens"""
    if 'error' in request.args:
        error = request.args.get('error')
        error_description = request.args.get('error_description', '')

        # Detectar error AADSTS65004: User declined consent or admin approval required
        if 'AADSTS65004' in error_description or 'AADSTS65001' in error_description:
            flash('Autorización pendiente: Tu administrador de IT debe aprobar la app. Una vez aprobada, volvé a hacer click en "Conectar Microsoft".', 'warning')
        elif error == 'access_denied':
            flash('Cancelaste la autorización. Podés volver a intentar cuando quieras.', 'info')
        else:
            flash(f'Error de autorización: {error_description or error}', 'error')

        return redirect(url_for('viajes.preferencias'))

    try:
        code = request.args.get('code')
        if not code:
            flash('No se recibió código de autorización', 'error')
            return redirect(url_for('viajes.preferencias'))

        # Token exchange
        token_response = http_requests.post(
            'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            data={
                'code': code,
                'client_id': MICROSOFT_CLIENT_ID,
                'client_secret': MICROSOFT_CLIENT_SECRET,
                'redirect_uri': get_redirect_uri(),
                'grant_type': 'authorization_code',
                'scope': ' '.join(SCOPES)
            }
        )

        if token_response.status_code != 200:
            error_data = token_response.json()
            logger.error(f"MS OAuth token error: status={token_response.status_code}, response={error_data}")
            flash(f'Error obteniendo token: {error_data.get("error_description", "Unknown")}', 'error')
            return redirect(url_for('viajes.preferencias'))

        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        logger.info(f"MS OAuth token received: has_access={bool(access_token)}, has_refresh={bool(refresh_token)}")

        if not access_token:
            logger.error("MS OAuth: No access token in response")
            flash('No se recibió access token', 'error')
            return redirect(url_for('viajes.preferencias'))

        # Obtener info del usuario con Graph API
        logger.info("MS OAuth: Calling Graph API /me endpoint")
        user_info_response = http_requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if user_info_response.status_code != 200:
            logger.error(f"MS Graph API error: status={user_info_response.status_code}, response={user_info_response.text}")
            flash('No se pudo obtener información de la cuenta', 'error')
            return redirect(url_for('viajes.preferencias'))

        user_info = user_info_response.json()
        logger.info(f"MS Graph API response: {user_info}")
        microsoft_email = user_info.get('mail') or user_info.get('userPrincipalName')

        if not microsoft_email:
            logger.error(f"MS OAuth: No email in user_info: {user_info}")
            flash('No se pudo obtener el email de la cuenta', 'error')
            return redirect(url_for('viajes.preferencias'))

        # Verificar si ya existe conexión
        existing = EmailConnection.query.filter_by(
            user_id=current_user.id,
            provider='microsoft',
            email=microsoft_email
        ).first()

        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.token_expiry = None
            existing.is_active = True
            existing.last_error = None
            existing.updated_at = datetime.utcnow()
            flash(f'Microsoft reconectado: {microsoft_email}', 'success')
        else:
            connection = EmailConnection(
                user_id=current_user.id,
                provider='microsoft',
                email=microsoft_email,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=None,
                is_active=True
            )
            db.session.add(connection)
            flash(f'Microsoft conectado: {microsoft_email}', 'success')

        db.session.commit()
        session.pop('ms_oauth_state', None)

        # Si viene del wizard, volver ahí
        if session.pop('from_wizard', False):
            return redirect(url_for('viajes.bienvenida'))
        return redirect(url_for('viajes.preferencias'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error conectando Microsoft: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@microsoft_oauth_bp.route('/desconectar-microsoft/<int:connection_id>', methods=['POST'])
@login_required
def desconectar_microsoft_by_id(connection_id):
    """Desconecta OAuth de Microsoft (usado por toggle) - el email queda en la lista"""
    try:
        connection = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=current_user.id
        ).first()

        if not connection:
            flash('Conexión no encontrada', 'error')
            return redirect(url_for('viajes.preferencias'))

        email = connection.email

        # Intentar revocar token (Microsoft no siempre lo requiere)
        try:
            if connection.access_token:
                http_requests.post(
                    'https://login.microsoftonline.com/common/oauth2/v2.0/logout',
                    params={'post_logout_redirect_uri': get_redirect_uri()},
                    headers={'Authorization': f'Bearer {connection.access_token}'}
                )
        except:
            pass

        # Solo eliminar conexión OAuth
        db.session.delete(connection)
        db.session.commit()

        flash(f'Microsoft desconectado: {email}', 'success')
        return redirect(url_for('viajes.preferencias'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error desconectando: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


@microsoft_oauth_bp.route('/quitar-email-microsoft/<int:connection_id>', methods=['POST'])
@login_required
def quitar_email_microsoft(connection_id):
    """Elimina email completo (usado por botón Quitar) - desconecta OAuth y quita de lista"""
    try:
        connection = EmailConnection.query.filter_by(
            id=connection_id,
            user_id=current_user.id
        ).first()

        if not connection:
            flash('Conexión no encontrada', 'error')
            return redirect(url_for('viajes.preferencias'))

        email = connection.email

        # Intentar revocar token
        try:
            if connection.access_token:
                http_requests.post(
                    'https://login.microsoftonline.com/common/oauth2/v2.0/logout',
                    params={'post_logout_redirect_uri': get_redirect_uri()},
                    headers={'Authorization': f'Bearer {connection.access_token}'}
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
        return redirect(url_for('viajes.preferencias'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error eliminando email: {str(e)}', 'error')
        return redirect(url_for('viajes.preferencias'))


# ============================================
# HELPERS - Multi-cuenta ready
# ============================================

def get_microsoft_credentials(user_id, email=None, connection_id=None):
    """
    Obtiene credenciales válidas de Microsoft para una cuenta específica.

    Args:
        user_id: ID del usuario
        email: Email específico (preferido)
        connection_id: ID de conexión alternativo

    Returns:
        dict con access_token y refresh_token o None
    """
    # Buscar conexión específica
    if connection_id:
        connection = EmailConnection.query.filter_by(
            id=connection_id, user_id=user_id, is_active=True
        ).first()
    elif email:
        connection = EmailConnection.query.filter_by(
            user_id=user_id, provider='microsoft', email=email, is_active=True
        ).first()
    else:
        # Fallback - primera conexión
        connection = EmailConnection.query.filter_by(
            user_id=user_id, provider='microsoft', is_active=True
        ).first()

    if not connection or not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        return None

    # Verificar si el token expiró y refrescar si es necesario
    if connection.token_expiry and connection.token_expiry < datetime.utcnow():
        if connection.refresh_token:
            try:
                print(f"🔄 Refrescando token Microsoft expirado para {connection.email}...")
                token_response = http_requests.post(
                    'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                    data={
                        'client_id': MICROSOFT_CLIENT_ID,
                        'client_secret': MICROSOFT_CLIENT_SECRET,
                        'refresh_token': connection.refresh_token,
                        'grant_type': 'refresh_token',
                        'scope': ' '.join(SCOPES)
                    }
                )

                if token_response.status_code == 200:
                    token_data = token_response.json()
                    connection.access_token = token_data.get('access_token')
                    if token_data.get('refresh_token'):
                        connection.refresh_token = token_data.get('refresh_token')
                    connection.updated_at = datetime.utcnow()
                    connection.last_error = None  # Limpiar error anterior
                    db.session.commit()
                    print(f"✅ Token Microsoft refrescado exitosamente para {connection.email}")
                else:
                    error_msg = f'Token refresh failed: HTTP {token_response.status_code}'
                    print(f"❌ {error_msg} para {connection.email}")
                    connection.last_error = error_msg
                    connection.is_active = False
                    db.session.commit()
                    return None
            except Exception as e:
                error_msg = f"Error refrescando token Microsoft: {str(e)}"
                print(f"❌ {error_msg} para {connection.email}")
                import traceback
                traceback.print_exc()
                connection.last_error = error_msg
                connection.is_active = False
                db.session.commit()
                return None

    return {
        'access_token': connection.access_token,
        'refresh_token': connection.refresh_token,
        'email': connection.email
    }


def get_user_microsoft_connections(user_id):
    """Obtiene todas las conexiones Microsoft activas de un usuario"""
    return EmailConnection.query.filter_by(
        user_id=user_id, provider='microsoft', is_active=True
    ).all()
