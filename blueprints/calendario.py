"""
Blueprint de Calendario - Mi Agente Viajes
Rutas: /calendar-feed, /export-calendar, /update-calendar, /cancel-calendar, /regenerate-calendar-token
"""
from flask import Blueprint, make_response, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
import json
import pytz
from icalendar import Calendar, Event, Alarm

from models import db, Viaje, User
from utils.helpers import get_viajes_for_user, deduplicar_vuelos_en_grupo

calendario_bp = Blueprint('calendario', __name__)


@calendario_bp.route('/calendar-feed')
def calendar_feed_old():
    """
    Feed viejo sin token - redirige a login o muestra error
    Los usuarios deben usar /calendar-feed/<token> desde su perfil
    """
    return jsonify({
        'error': 'Calendar feed requires authentication token',
        'message': 'Please use your personal calendar link from your profile page',
        'help': 'Login and go to Profile > Calendar section to get your personal link'
    }), 403


@calendario_bp.route('/calendar-feed/<token>')
def calendar_feed(token):
    """
    MVP9: Webcal feed privado - genera .ics solo con viajes del usuario
    Cada usuario tiene su propio token único
    
    MVP10: Agrega eventos all-day para viajes con múltiples vuelos
    MVP11: Aplica deduplicación de vuelos idénticos
    """
    # Buscar usuario por token
    user = User.query.filter_by(calendar_token=token).first()
    if not user:
        return jsonify({'error': 'Invalid calendar token'}), 404
    
    # Obtener viajes del usuario (owner + pasajero)
    viajes_futuros = get_viajes_for_user(user, Viaje, User)
    
    # Filtrar solo futuros
    hoy = date.today()
    viajes_futuros = [v for v in viajes_futuros if v.fecha_salida.date() >= hoy]
    viajes_futuros = sorted(viajes_futuros, key=lambda v: v.fecha_salida)
    
    # MVP11: Obtener preferencia de usuario
    combinar = getattr(user, 'combinar_vuelos', True)
    if combinar is None:
        combinar = True
    
    # Crear calendario
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', f'Mis Viajes - {user.nombre}')
    cal.add('x-wr-timezone', 'America/Argentina/Buenos_Aires')
    cal.add('x-wr-caldesc', f'Calendario de viajes de {user.nombre}')
    
    # Agrupar viajes por grupo_viaje
    grupos = {}
    for viaje in viajes_futuros:
        grupo_id = viaje.grupo_viaje or f'solo_{viaje.id}'
        if grupo_id not in grupos:
            grupos[grupo_id] = []
        grupos[grupo_id].append(viaje)
    
    # Crear eventos
    for grupo_id, vuelos in grupos.items():
        # Ordenar vuelos por fecha
        vuelos_ordenados = sorted(vuelos, key=lambda v: v.fecha_salida)
        
        # MVP11: Si combinar_vuelos está ON, deduplicar dentro del grupo
        if combinar:
            vuelos_ordenados = deduplicar_vuelos_en_grupo(vuelos_ordenados)
        else:
            # Marcar todos como no combinados
            for v in vuelos_ordenados:
                v._es_combinado = False
        
        # Crear evento individual para cada vuelo (ya deduplicados si aplica)
        for vuelo in vuelos_ordenados:
            event = _crear_evento_calendario(vuelo)
            cal.add_component(event)
        
        # MVP10: Crear evento all-day SOLO si el grupo tiene 2+ vuelos
        if len(vuelos_ordenados) >= 2 and not grupo_id.startswith('solo_'):
            event_allday = _crear_evento_allday(grupo_id, vuelos_ordenados)
            if event_allday:
                cal.add_component(event_allday)
    
    # Response con headers correctos para webcal
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    response.headers['Content-Disposition'] = 'inline; filename="calendar.ics"'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


@calendario_bp.route('/regenerate-calendar-token', methods=['POST'])
@login_required
def regenerate_calendar_token():
    """
    MVP9: Regenera el token del calendario (por si se compartió por error)
    """
    current_user.regenerate_calendar_token()
    db.session.commit()
    flash('Token de calendario regenerado. Deberás volver a suscribirte con el nuevo link.', 'success')
    return redirect(url_for('viajes.perfil'))


@calendario_bp.route('/export-calendar/<grupo_id>')
@login_required
def export_calendar(grupo_id):
    """Exporta viaje a .ics con iTIP"""
    vuelos = _get_vuelos_by_grupo(grupo_id)
    
    if not vuelos:
        return "Viaje no encontrado", 404
    
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')
    cal.add('x-wr-calname', 'Mis Viajes')
    
    for vuelo in vuelos:
        event = _crear_evento_calendario(vuelo, sequence=0, method='REQUEST')
        cal.add_component(event)
    
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    nombre = (vuelos[0].nombre_viaje or 'viaje').replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre}.ics"'
    return response


@calendario_bp.route('/update-calendar/<grupo_id>')
@login_required
def update_calendar(grupo_id):
    """Genera .ics UPDATE para sincronizar cambios"""
    vuelos = _get_vuelos_by_grupo(grupo_id)
    
    if not vuelos:
        return "Viaje no encontrado", 404
    
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'UPDATE')
    
    for vuelo in vuelos:
        event = _crear_evento_calendario(vuelo, sequence=1, method='UPDATE')
        cal.add_component(event)
    
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    nombre = (vuelos[0].nombre_viaje or 'viaje').replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre}_update.ics"'
    return response


@calendario_bp.route('/cancel-calendar/<grupo_id>')
@login_required
def cancel_calendar(grupo_id):
    """Genera .ics CANCEL para eliminar de calendario"""
    vuelos = _get_vuelos_by_grupo(grupo_id)
    
    if not vuelos:
        return "Viaje no encontrado", 404
    
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'CANCEL')
    
    tz = pytz.timezone('America/Argentina/Buenos_Aires')
    
    for vuelo in vuelos:
        event = Event()
        event.add('summary', f"{vuelo.numero_vuelo}: {vuelo.origen} → {vuelo.destino}")
        event.add('uid', f'vuelo-{vuelo.id}@miagenteviajes.local')
        event.add('dtstamp', datetime.now(pytz.UTC))
        event.add('status', 'CANCELLED')
        event.add('sequence', 10)
        
        dtstart = datetime.combine(vuelo.fecha_salida, datetime.strptime(vuelo.hora_salida, '%H:%M').time())
        dtend = datetime.combine(vuelo.fecha_llegada, datetime.strptime(vuelo.hora_llegada, '%H:%M').time())
        
        event.add('dtstart', tz.localize(dtstart))
        event.add('dtend', tz.localize(dtend))
        event.add('organizer', 'mailto:viajes@miagenteviajes.local')
        event.add('attendee', 'mailto:viajes@miagenteviajes.local')
        
        cal.add_component(event)
    
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    nombre = (vuelos[0].nombre_viaje or 'viaje').replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre}_cancel.ics"'
    return response


# ============================================
# FUNCIONES HELPER PRIVADAS
# ============================================

def _get_vuelos_by_grupo(grupo_id):
    """Obtiene vuelos por grupo_id o viaje individual"""
    if grupo_id.startswith('solo_'):
        viaje_id = int(grupo_id.replace('solo_', ''))
        vuelo = Viaje.query.get(viaje_id)
        return [vuelo] if vuelo else []
    else:
        return Viaje.query.filter_by(grupo_viaje=grupo_id).order_by(Viaje.fecha_salida, Viaje.hora_salida).all()


def _crear_evento_allday(grupo_id, vuelos):
    """
    MVP10: Crea un evento all-day que abarca todo el viaje
    
    Args:
        grupo_id: ID del grupo de viaje
        vuelos: Lista de vuelos ordenados por fecha
    
    Returns:
        Event iCal o None si no se puede crear
    """
    if not vuelos:
        return None
    
    primer_vuelo = vuelos[0]
    ultimo_vuelo = vuelos[-1]
    
    # Obtener nombre del viaje
    nombre_viaje = primer_vuelo.nombre_viaje or f"Viaje a {ultimo_vuelo.destino}"
    
    # Fecha inicio: día del primer vuelo
    fecha_inicio = primer_vuelo.fecha_salida.date()
    
    # Fecha fin: día de llegada del último vuelo + 1 (iCal all-day es exclusivo en el fin)
    if ultimo_vuelo.fecha_llegada:
        fecha_fin = ultimo_vuelo.fecha_llegada.date() + timedelta(days=1)
    else:
        # Si no hay fecha_llegada, usar fecha_salida del último vuelo + 1
        fecha_fin = ultimo_vuelo.fecha_salida.date() + timedelta(days=1)
    
    # Crear evento all-day
    event = Event()
    event.add('summary', f"🌍 {nombre_viaje}")
    event.add('uid', f'viaje-allday-{grupo_id}@miagenteviajes.local')
    event.add('dtstamp', datetime.now(pytz.UTC))
    
    # Para eventos all-day, usar DATE (no DATETIME)
    event.add('dtstart', fecha_inicio)
    event.add('dtend', fecha_fin)
    
    # Sin descripción - la info detallada está en cada vuelo individual
    
    # Transparencia: TRANSPARENT para que no bloquee el calendario
    event.add('transp', 'TRANSPARENT')
    
    # Categoría para filtrado
    event.add('categories', ['Viaje'])
    
    return event


def _crear_evento_calendario(vuelo, sequence=0, method=None):
    """
    Crea un evento iCal para un vuelo
    
    MVP11: Si el vuelo está combinado (_es_combinado=True), 
    incluye todos los pasajeros en la descripción
    """
    tz = pytz.timezone('America/Argentina/Buenos_Aires')
    
    event = Event()
    
    # Título limpio
    titulo = f"{vuelo.numero_vuelo}: {vuelo.origen} → {vuelo.destino}"
    event.add('summary', titulo)
    
    # Descripción completa
    desc = [f"Vuelo {vuelo.numero_vuelo} - {vuelo.aerolinea}"]
    
    # MVP11: Si es vuelo combinado, mostrar múltiples códigos
    if getattr(vuelo, '_es_combinado', False) and hasattr(vuelo, '_codigos_reserva'):
        desc.append(f"\nCódigos: {', '.join(vuelo._codigos_reserva)}")
    elif vuelo.codigo_reserva:
        desc.append(f"\nCódigo: {vuelo.codigo_reserva}")
    
    # MVP11: Pasajeros - usar combinados si disponible
    pasajeros_a_mostrar = []
    if getattr(vuelo, '_es_combinado', False) and hasattr(vuelo, '_pasajeros_combinados'):
        pasajeros_a_mostrar = vuelo._pasajeros_combinados
    elif vuelo.pasajeros:
        try:
            pasajeros_a_mostrar = json.loads(vuelo.pasajeros)
        except:
            pasajeros_a_mostrar = []
    
    if pasajeros_a_mostrar:
        desc.append("\nPasajeros:")
        for p in pasajeros_a_mostrar:
            pax = f"• {p.get('nombre', '')}"
            if p.get('asiento'):
                pax += f" - Asiento {p['asiento']}"
            if p.get('cabina'):
                pax += f" ({p['cabina']})"
            # MVP11: Mostrar código de reserva si es combinado
            if p.get('codigo_reserva'):
                pax += f" [{p['codigo_reserva']}]"
            desc.append(pax)
    
    # Horarios locales
    desc.append(f"\nSalida: {vuelo.origen} a las {vuelo.hora_salida} (hora local)")
    desc.append(f"Llegada: {vuelo.destino} a las {vuelo.hora_llegada} (hora local)")
    
    # Terminal
    if vuelo.terminal:
        if ' a ' in vuelo.terminal.lower():
            parts = vuelo.terminal.split(' a ')
            desc.append(f"Terminal salida: {parts[0].strip()}")
            if len(parts) > 1:
                desc.append(f"Terminal llegada: {parts[1].strip()}")
        else:
            desc.append(f"Terminal salida: {vuelo.terminal}")
    
    if vuelo.puerta:
        desc.append(f"Puerta: {vuelo.puerta}")
    
    event.add('description', '\n'.join(desc))
    
    # Fechas
    dtstart = datetime.combine(vuelo.fecha_salida, datetime.strptime(vuelo.hora_salida, '%H:%M').time())
    dtend = datetime.combine(vuelo.fecha_llegada, datetime.strptime(vuelo.hora_llegada, '%H:%M').time())
    
    event.add('dtstart', tz.localize(dtstart))
    event.add('dtend', tz.localize(dtend))
    event.add('location', f'{vuelo.origen} Airport')
    
    # UID único y estable - MVP11: usar numero_vuelo + fecha para combinados
    if getattr(vuelo, '_es_combinado', False):
        # UID basado en vuelo+fecha para que sea único y estable
        fecha_str = vuelo.fecha_salida.strftime('%Y%m%d')
        event.add('uid', f'vuelo-{vuelo.numero_vuelo}-{fecha_str}@miagenteviajes.local')
    else:
        event.add('uid', f'vuelo-{vuelo.id}@miagenteviajes.local')
    
    event.add('dtstamp', datetime.now(pytz.UTC))
    event.add('sequence', sequence)
    
    # Para iTIP REQUEST/UPDATE
    if method in ('REQUEST', 'UPDATE'):
        event.add('organizer', 'mailto:viajes@miagenteviajes.local')
        event.add('attendee', 'mailto:viajes@miagenteviajes.local')
        event.add('status', 'CONFIRMED')
    
    # Alarma
    alarm = Alarm()
    alarm.add('trigger', timedelta(hours=-24))
    alarm.add('action', 'DISPLAY')
    alarm.add('description', f'Mañana: {titulo}')
    event.add_component(alarm)
    
    return event
