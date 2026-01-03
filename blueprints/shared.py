"""
Blueprint para compartir viajes públicamente
Rutas: /share/<grupo_id>, /shared/<token>
"""
from flask import Blueprint, render_template, jsonify, url_for, abort
from flask_login import login_required, current_user
from models import db, Viaje, User, SharedTrip
from utils.helpers import get_viajes_for_user, deduplicar_vuelos_en_grupo
import secrets

shared_bp = Blueprint('shared', __name__)


def generar_token_unico():
    """Genera token único de 32 caracteres"""
    return secrets.token_urlsafe(32)


@shared_bp.route('/share/<grupo_id>', methods=['POST'])
@login_required
def share_trip(grupo_id):
    """
    Genera o retorna link de compartir existente para un grupo de viaje.

    Returns:
        JSON con url completa para compartir
    """
    # Detectar si es un viaje individual (formato: solo_<id>)
    if grupo_id.startswith('solo_'):
        viaje_id = grupo_id.replace('solo_', '')
        viajes = Viaje.query.filter_by(
            id=int(viaje_id),
            user_id=current_user.id
        ).all()
        # Para viajes individuales, usar el viaje_id como grupo_id en SharedTrip
        grupo_id_real = grupo_id
    else:
        # Grupo de viajes normal
        viajes = Viaje.query.filter_by(
            user_id=current_user.id,
            grupo_viaje=grupo_id
        ).all()
        grupo_id_real = grupo_id

    if not viajes:
        return jsonify({'error': 'Viaje no encontrado'}), 404

    # Buscar si ya existe un share para este grupo
    shared = SharedTrip.query.filter_by(
        grupo_viaje=grupo_id_real,
        owner_id=current_user.id
    ).first()

    if not shared:
        # Crear nuevo share
        token = generar_token_unico()
        shared = SharedTrip(
            grupo_viaje=grupo_id_real,
            token=token,
            owner_id=current_user.id
        )
        db.session.add(shared)
        db.session.commit()

    # Generar URL completa
    share_url = url_for('shared.ver_viaje_compartido', token=shared.token, _external=True)

    return jsonify({
        'success': True,
        'url': share_url,
        'token': shared.token
    })


@shared_bp.route('/shared/<token>')
def ver_viaje_compartido(token):
    """
    Vista pública de un viaje compartido (sin login requerido).

    Args:
        token: Token único del viaje compartido
    """
    # Buscar el share
    shared = SharedTrip.query.filter_by(token=token).first()

    if not shared:
        abort(404)

    # Detectar si es viaje individual (formato: solo_<id>)
    if shared.grupo_viaje.startswith('solo_'):
        viaje_id = shared.grupo_viaje.replace('solo_', '')
        viajes = Viaje.query.filter_by(id=int(viaje_id)).all()
    else:
        # Grupo de viajes normal
        viajes = Viaje.query.filter_by(
            grupo_viaje=shared.grupo_viaje
        ).order_by(Viaje.fecha_salida).all()

    if not viajes:
        abort(404)

    # Obtener dueño
    owner = User.query.get(shared.owner_id)

    # Deduplicar vuelos si el usuario tiene la preferencia activada
    if owner and owner.combinar_vuelos and not shared.grupo_viaje.startswith('solo_'):
        viajes = deduplicar_vuelos_en_grupo(viajes)

    # Renderizar template público
    return render_template(
        'shared_trip.html',
        viajes=viajes,
        nombre_viaje=viajes[0].nombre_viaje if viajes else 'Viaje',
        owner_nombre=owner.nombre if owner else 'Usuario',
        grupo_id=shared.grupo_viaje
    )
