"""
Push Notifications Blueprint - Mi Agente Viajes

Endpoints para manejar suscripciones y envío de push notifications
usando Firebase Cloud Messaging API V1.
"""

from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
import os
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

push_bp = Blueprint('push', __name__, url_prefix='/api/push')

# Firebase Project ID
FIREBASE_PROJECT_ID = 'mi-agente-viajes-2a67b'

# Scopes necesarios para FCM
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']


def get_access_token():
    """Obtener access token para FCM API V1 usando Service Account."""
    try:
        # Intentar cargar desde variable de entorno (JSON string)
        sa_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        
        if sa_json:
            sa_info = json.loads(sa_json)
            credentials = service_account.Credentials.from_service_account_info(
                sa_info, scopes=SCOPES
            )
        else:
            # Fallback: cargar desde archivo
            sa_file = os.path.join(current_app.root_path, 'firebase-service-account.json')
            if os.path.exists(sa_file):
                credentials = service_account.Credentials.from_service_account_file(
                    sa_file, scopes=SCOPES
                )
            else:
                current_app.logger.error("Firebase Service Account not configured")
                return None
        
        # Refrescar token si es necesario
        credentials.refresh(Request())
        return credentials.token
        
    except Exception as e:
        current_app.logger.error(f"Failed to get FCM access token: {e}")
        return None


# ============================================
# SUSCRIPCIÓN
# ============================================

@push_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Guardar token de push notification para el usuario."""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        from models import db, PushSubscription
        
        # Verificar si ya existe
        existing = PushSubscription.query.filter_by(
            user_id=current_user.id,
            token=token
        ).first()
        
        if existing:
            existing.active = True
            db.session.commit()
            return jsonify({'status': 'already_subscribed'})
        
        # Crear nueva suscripción
        subscription = PushSubscription(
            user_id=current_user.id,
            token=token,
            active=True
        )
        db.session.add(subscription)
        db.session.commit()
        
        current_app.logger.info(f"Push subscription added for user {current_user.id}")
        return jsonify({'status': 'subscribed'})
        
    except Exception as e:
        current_app.logger.error(f"Push subscribe error: {e}")
        return jsonify({'error': str(e)}), 500


@push_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Desactivar token de push notification."""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        from models import db, PushSubscription
        
        subscription = PushSubscription.query.filter_by(
            user_id=current_user.id,
            token=token
        ).first()
        
        if subscription:
            subscription.active = False
            db.session.commit()
        
        return jsonify({'status': 'unsubscribed'})
        
    except Exception as e:
        current_app.logger.error(f"Push unsubscribe error: {e}")
        return jsonify({'error': str(e)}), 500


@push_bp.route('/status', methods=['GET'])
@login_required
def status():
    """Verificar estado de suscripción del usuario."""
    try:
        from models import PushSubscription
        
        subscription = PushSubscription.query.filter_by(
            user_id=current_user.id,
            active=True
        ).first()
        
        return jsonify({
            'subscribed': subscription is not None,
            'token_exists': subscription.token[:20] + '...' if subscription else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ENVÍO DE NOTIFICACIONES (API V1)
# ============================================

def send_push_notification(user_id, title, body, data=None, url=None):
    """
    Enviar push notification a un usuario usando FCM API V1.
    """
    from models import db, PushSubscription
    
    subscriptions = PushSubscription.query.filter_by(
        user_id=user_id,
        active=True
    ).all()
    
    if not subscriptions:
        return {'sent': 0, 'error': 'No active subscriptions'}
    
    access_token = get_access_token()
    if not access_token:
        return {'sent': 0, 'error': 'Could not get FCM access token'}
    
    notification_data = data or {}
    if url:
        notification_data['url'] = url
    notification_data = {k: str(v) for k, v in notification_data.items()}
    
    results = []
    fcm_url = f'https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send'

    # Base URL para assets
    BASE_URL = 'https://mi-agente-viajes-454542398872.us-east1.run.app'

    for sub in subscriptions:
        try:
            payload = {
                'message': {
                    'token': sub.token,
                    'notification': {
                        'title': title,
                        'body': body
                    },
                    'webpush': {
                        'headers': {
                            'Urgency': 'high'
                        },
                        'notification': {
                            'title': title,
                            'body': body,
                            'icon': f'{BASE_URL}/static/icons/icon-192x192.png',
                            'badge': f'{BASE_URL}/static/icons/icon-72x72.png',
                            'requireInteraction': False,
                            'renotify': True,
                            'tag': notification_data.get('tag', 'mi-agente-viajes')
                        },
                        'fcm_options': {
                            'link': url if url and url.startswith('http') else f'{BASE_URL}{url or "/"}'
                        }
                    },
                    'data': notification_data
                }
            }
            
            response = requests.post(
                fcm_url,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                results.append({'token': sub.token[:20] + '...', 'success': True})
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                results.append({'token': sub.token[:20] + '...', 'success': False, 'error': error_msg})
                
                if 'UNREGISTERED' in str(error_msg) or 'not found' in str(error_msg).lower():
                    sub.active = False
                    db.session.commit()
                
        except Exception as e:
            results.append({'token': sub.token[:20] + '...', 'success': False, 'error': str(e)})
    
    sent = sum(1 for r in results if r['success'])
    return {'sent': sent, 'total': len(subscriptions), 'results': results}


def send_reservation_notification(user_id, reserva_info):
    """
    Enviar notificación cuando se detecta una nueva reserva.

    Args:
        user_id: ID del usuario
        reserva_info: dict con info de la reserva:
            - tipo: 'vuelo', 'hotel', 'auto', etc.
            - descripcion: texto descriptivo
            - fecha: fecha de la reserva
            - codigo: código de reserva (opcional)
            - source: origen ('gmail', 'outlook', 'pdf_upload', etc.)
    """
    tipo = reserva_info.get('tipo', 'reserva')
    descripcion = reserva_info.get('descripcion', '')
    fecha = reserva_info.get('fecha', '')
    codigo = reserva_info.get('codigo', '')
    source = reserva_info.get('source', '')

    # Emojis por tipo
    emojis = {
        'vuelo': '✈️',
        'hotel': '🏨',
        'auto': '🚗',
        'crucero': '🚢',
        'tren': '🚄',
        'bus': '🚌',
        'restaurante': '🍽️',
        'actividad': '🎯',
        'espectaculo': '🎭',
        'transfer': '🚐'
    }
    emoji = emojis.get(tipo, '📋')

    # Origen amigable
    source_names = {
        'gmail': 'Gmail',
        'outlook': 'Outlook',
        'microsoft': 'Outlook',
        'pdf_upload': 'PDF',
        'email_forward': 'Email',
        'manual': 'Manual'
    }
    source_text = source_names.get(source, source)

    title = f"{emoji} Nueva reserva detectada"
    body = f"{descripcion}"
    if fecha:
        body += f" - {fecha}"

    return send_push_notification(
        user_id=user_id,
        title=title,
        body=body,
        data={
            'type': 'new_reservation',
            'reservation_type': tipo,
            'tag': f'reserva-{codigo}' if codigo else 'new-reservation',
            'source': source
        },
        url='/'
    )


def send_flight_change_notification(user_id, flight_info, change_type):
    """Enviar notificación de cambio de vuelo."""
    # Mapear tipos de api.py a los esperados aquí
    type_map = {
        'gate': 'gate_change',
        'cancelacion': 'cancelled'
    }
    change_type = type_map.get(change_type, change_type)

    titles = {
        'delay': f"⏰ Vuelo {flight_info.get('numero', '')} retrasado",
        'gate_change': f"🚪 Cambio de puerta - {flight_info.get('numero', '')}",
        'cancelled': f"❌ Vuelo {flight_info.get('numero', '')} cancelado",
        'status_change': f"✈️ Actualización - {flight_info.get('numero', '')}"
    }

    bodies = {
        'delay': f"Nueva salida: {flight_info.get('nueva_hora', 'Ver detalles')}",
        'gate_change': f"Nueva puerta: {flight_info.get('nueva_puerta', 'Ver detalles')}",
        'cancelled': "Tu vuelo ha sido cancelado. Contacta a la aerolínea.",
        'status_change': flight_info.get('mensaje', 'Ver detalles del vuelo')
    }
    
    return send_push_notification(
        user_id=user_id,
        title=titles.get(change_type, f"Actualización de vuelo"),
        body=bodies.get(change_type, 'Ver detalles'),
        data={'type': 'flight_change', 'change_type': change_type, 'flight': flight_info.get('numero', '')},
        url=flight_info.get('url', '/')
    )


@push_bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Enviar notificación de prueba."""
    try:
        result = send_push_notification(
            user_id=current_user.id,
            title="🧪 Notificación de prueba",
            body="¡Las push notifications funcionan!",
            url="/"
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
