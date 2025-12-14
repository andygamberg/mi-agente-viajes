"""
Blueprint de Calendario - Mi Agente Viajes
Rutas: /calendar-feed, /export-calendar, /update-calendar, /cancel-calendar, /regenerate-calendar-token
"""
from flask import Blueprint, make_response, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from collections import defaultdict
import json
import pytz
from icalendar import Calendar, Event, Alarm

from models import db, Viaje, User
from utils.helpers import get_viajes_for_user, deduplicar_vuelos_en_grupo

calendario_bp = Blueprint('calendario', __name__)


def get_dato(viaje, key, default=''):
    """Extrae dato de JSONB con fallback a columna legacy"""
    datos = viaje.datos or {}
    return datos.get(key) or getattr(viaje, key, default) or default


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
    MVP11: Deduplica vuelos combinados
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
    for grupo_id, viajes in grupos.items():
        # Ordenar viajes por fecha
        viajes_ordenados = sorted(viajes, key=lambda v: v.fecha_salida)

        # MVP11: Deduplicar si el usuario tiene la preferencia activa (solo para vuelos)
        combinar = getattr(user, 'combinar_vuelos', True)
        if combinar is None:
            combinar = True

        if combinar:
            viajes_ordenados = deduplicar_vuelos_en_grupo(viajes_ordenados)

        # Crear evento individual para cada reserva
        for viaje in viajes_ordenados:
            event = _crear_evento_calendario(viaje)
            cal.add_component(event)

        # MVP10: Crear evento all-day SOLO si el grupo tiene 2+ items
        if len(viajes_ordenados) >= 2 and not grupo_id.startswith('solo_'):
            event_allday = _crear_evento_allday(grupo_id, viajes_ordenados)
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


def _crear_evento_allday(grupo_id, viajes):
    """
    MVP10: Crea un evento all-day que abarca todo el viaje

    Args:
        grupo_id: ID del grupo de viaje
        viajes: Lista de reservas ordenadas por fecha

    Returns:
        Event iCal o None si no se puede crear
    """
    if not viajes:
        return None

    primer_viaje = viajes[0]
    ultimo_viaje = viajes[-1]
    
    # Obtener nombre del viaje
    nombre_viaje = primer_viaje.nombre_viaje or f"Viaje a {ultimo_viaje.destino or 'destino'}"

    # Fecha inicio: día del primer viaje
    fecha_inicio = primer_viaje.fecha_salida.date()

    # Fecha fin: día de llegada del último viaje + 1 (iCal all-day es exclusivo en el fin)
    if ultimo_viaje.fecha_llegada:
        fecha_fin = ultimo_viaje.fecha_llegada.date() + timedelta(days=1)
    else:
        # Si no hay fecha_llegada, usar fecha_salida del último + 1
        fecha_fin = ultimo_viaje.fecha_salida.date() + timedelta(days=1)
    
    # Crear evento all-day
    event = Event()
    event.add('summary', nombre_viaje)
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


def _es_evento_allday(viaje):
    """
    Determina si un evento debe ser all-day (sin hora específica)

    - Hotels y autos: siempre all-day
    - Cruceros/barcos: all-day solo si duran más de 24 horas (no ferries)
    - Todo lo demás: hora específica
    """
    # Hoteles y autos siempre all-day
    if viaje.tipo in ['hotel', 'auto']:
        return True

    # Crucero/barco: all-day si dura más de 24 horas
    if viaje.tipo in ['crucero', 'barco']:
        if viaje.fecha_llegada and viaje.fecha_salida:
            duracion = viaje.fecha_llegada - viaje.fecha_salida
            if duracion.total_seconds() > 24 * 3600:
                return True
        return False

    # Todo lo demás tiene hora específica
    return False


def _formatear_nombre_pasajero(nombre_completo):
    """
    Convierte APELLIDO/NOMBRE1 NOMBRE2 a Nombre1 Apellido

    Ejemplos:
        GAMBERG/ANDRES GUILLERMO -> Andrés Gamberg
        GERSZKOWICZ/VERONICA BEATRIZ -> Verónica Gerszkowicz
    """
    if not nombre_completo:
        return nombre_completo

    if '/' in nombre_completo:
        parts = nombre_completo.split('/')
        apellido = parts[0].strip().title()
        nombres = parts[1].strip().title() if len(parts) > 1 else ''
        # Tomar solo el primer nombre para mantenerlo corto
        primer_nombre = nombres.split()[0] if nombres else ''
        return f"{primer_nombre} {apellido}".strip()
    else:
        return nombre_completo.title()


def _crear_evento_calendario(viaje, sequence=0, method=None):
    """
    Crea un evento iCal para cualquier tipo de reserva

    Soporta: vuelo, hotel, barco/crucero, espectaculo, restaurante, actividad, auto, tren, transfer
    MVP11: Si es vuelo combinado (_es_combinado=True), agrupa pasajeros por reserva
    """
    tz = pytz.timezone('America/Argentina/Buenos_Aires')

    event = Event()

    # Determinar título y emoji según tipo
    tipo = viaje.tipo or 'vuelo'

    # Extraer datos de JSONB con fallback a legacy
    origen = get_dato(viaje, 'origen')
    destino = get_dato(viaje, 'destino')
    numero_vuelo = get_dato(viaje, 'numero_vuelo')
    proveedor = get_dato(viaje, 'proveedor')
    descripcion = get_dato(viaje, 'descripcion')

    if tipo == 'vuelo':
        emoji = '✈️'
        titulo = f"{emoji} {numero_vuelo}: {origen} → {destino}"
    elif tipo == 'hotel':
        emoji = '🏨'
        nombre_hotel = get_dato(viaje, 'nombre_propiedad') or proveedor or descripcion
        titulo = f"{emoji} {nombre_hotel}"
    elif tipo in ['barco', 'crucero']:
        emoji = '⛵'
        puerto_embarque = get_dato(viaje, 'puerto_embarque') or origen
        puerto_desembarque = get_dato(viaje, 'puerto_desembarque') or destino
        if puerto_embarque and puerto_desembarque:
            titulo = f"{emoji} {proveedor} {puerto_embarque} → {puerto_desembarque}"
        else:
            titulo = f"{emoji} {proveedor or descripcion}"
    elif tipo == 'espectaculo':
        emoji = '🎭'
        evento = get_dato(viaje, 'evento') or proveedor
        titulo = f"{emoji} {evento}"
        if descripcion and evento not in descripcion:
            titulo += f" - {descripcion}"
    elif tipo == 'restaurante':
        emoji = '🍽️'
        nombre_rest = get_dato(viaje, 'nombre') or proveedor or descripcion
        titulo = f"{emoji} {nombre_rest}"
    elif tipo == 'actividad':
        emoji = '🎯'
        nombre_act = get_dato(viaje, 'nombre') or descripcion or proveedor
        titulo = f"{emoji} {nombre_act}"
    elif tipo == 'auto':
        emoji = '🚗'
        empresa = get_dato(viaje, 'empresa') or proveedor or 'Rental'
        titulo = f"{emoji} {empresa}"
        lugar_retiro = get_dato(viaje, 'lugar_retiro') or origen
        if lugar_retiro:
            titulo += f" - {lugar_retiro}"
    elif tipo == 'tren':
        emoji = '🚆'
        operador = get_dato(viaje, 'operador') or proveedor or 'Tren'
        if origen and destino:
            titulo = f"{emoji} {operador} {origen} → {destino}"
        else:
            titulo = f"{emoji} {operador or descripcion}"
    elif tipo == 'transfer':
        emoji = '🚕'
        if origen and destino:
            titulo = f"{emoji} {origen} → {destino}"
        else:
            titulo = f"{emoji} {descripcion or 'Transfer'}"
    else:
        emoji = '📅'
        titulo = f"{emoji} {descripcion or proveedor or 'Reserva'}"

    event.add('summary', titulo)

    # Descripción completa - adaptada por tipo
    desc = []

    if tipo == 'vuelo':
        aerolinea = get_dato(viaje, 'aerolinea')
        desc.append(f"Vuelo {numero_vuelo} - {aerolinea}")
    elif tipo == 'hotel':
        desc.append(f"Hotel: {proveedor or descripcion}")
    elif tipo in ['barco', 'crucero']:
        desc.append(f"Crucero: {proveedor or descripcion}")
    elif tipo == 'espectaculo':
        # Leer detalles de datos JSONB
        datos = viaje.datos or {}
        evento_nombre = get_dato(viaje, 'evento') or proveedor
        venue = get_dato(viaje, 'venue') or get_dato(viaje, 'ubicacion')

        desc.append(f"Evento: {evento_nombre}")
        if venue:
            desc.append(f"Venue: {venue}")

        entradas_count = datos.get('entradas', 1)
        desc.append(f"Entradas: {entradas_count}")

        sector = datos.get('sector')
        if sector:
            desc.append(f"Sector: {sector}")

        # Mostrar detalles de cada entrada
        detalles = datos.get('detalles_entradas', [])
        if detalles and isinstance(detalles, list):
            desc.append("\nUbicaciones:")
            for d in detalles:
                if isinstance(d, dict):
                    fila = d.get('fila', '')
                    asiento = d.get('asiento', '')
                    desc.append(f"  • Fila {fila}: Asiento {asiento}")
    elif tipo == 'restaurante':
        nombre_rest = get_dato(viaje, 'nombre') or proveedor or descripcion
        desc.append(f"Restaurante: {nombre_rest}")
        direccion = get_dato(viaje, 'direccion') or get_dato(viaje, 'ubicacion')
        if direccion:
            desc.append(f"Dirección: {direccion}")
    elif tipo == 'actividad':
        nombre_act = get_dato(viaje, 'nombre') or descripcion or proveedor
        desc.append(f"Actividad: {nombre_act}")
        punto_encuentro = get_dato(viaje, 'punto_encuentro') or get_dato(viaje, 'ubicacion')
        if punto_encuentro:
            desc.append(f"Punto de encuentro: {punto_encuentro}")
    elif tipo == 'auto':
        empresa = get_dato(viaje, 'empresa') or proveedor
        desc.append(f"Rental: {empresa}")
        lugar_retiro = get_dato(viaje, 'lugar_retiro') or origen
        lugar_devolucion = get_dato(viaje, 'lugar_devolucion') or destino
        if lugar_retiro:
            desc.append(f"Retiro: {lugar_retiro}")
        if lugar_devolucion:
            desc.append(f"Devolución: {lugar_devolucion}")
    elif tipo == 'tren':
        operador = get_dato(viaje, 'operador') or proveedor or 'Tren'
        desc.append(f"Tren: {operador}")
        if origen:
            desc.append(f"Salida: Estación {origen}")
        if destino:
            desc.append(f"Llegada: Estación {destino}")
    elif tipo == 'transfer':
        desc.append(f"Transfer: {descripcion or 'Traslado'}")
        empresa = get_dato(viaje, 'empresa') or proveedor
        if empresa:
            desc.append(f"Empresa: {empresa}")
    else:
        desc.append(f"{descripcion or proveedor or 'Reserva'}")

    # Código de reserva (todos los tipos)
    codigo_reserva = get_dato(viaje, 'codigo_reserva')
    if getattr(viaje, '_es_combinado', False) and hasattr(viaje, '_codigos_reserva'):
        desc.append(f"\nCódigos: {', '.join(viaje._codigos_reserva)}")
    elif codigo_reserva:
        desc.append(f"\nCódigo: {codigo_reserva}")
    
    # MVP11: Pasajeros - usar combinados si disponible
    pasajeros_a_mostrar = []
    if getattr(viaje, '_es_combinado', False) and hasattr(viaje, '_pasajeros_combinados'):
        pasajeros_a_mostrar = viaje._pasajeros_combinados
    elif viaje.pasajeros:
        try:
            parsed = json.loads(viaje.pasajeros)
            # Validar que sea una lista de dicts (no un int como 8 para charters)
            if isinstance(parsed, list) and all(isinstance(p, dict) for p in parsed):
                pasajeros_a_mostrar = parsed
        except:
            pasajeros_a_mostrar = []

    if pasajeros_a_mostrar:
        # MVP11: Agrupar por código de reserva si es combinado
        es_combinado = getattr(viaje, '_es_combinado', False)
        
        if es_combinado and any(p.get('codigo_reserva') for p in pasajeros_a_mostrar):
            # Agrupar pasajeros por reserva
            por_reserva = defaultdict(list)
            for p in pasajeros_a_mostrar:
                codigo = p.get('codigo_reserva', 'Sin código')
                por_reserva[codigo].append(p)
            
            desc.append("")  # Línea en blanco
            
            for codigo, pasajeros in por_reserva.items():
                desc.append(f"━━━ {codigo} ━━━")
                for p in pasajeros:
                    nombre = _formatear_nombre_pasajero(p.get('nombre', ''))
                    pax = f"• {nombre}"
                    if p.get('asiento'):
                        pax += f" - {p['asiento']}"
                    if p.get('cabina'):
                        pax += f" ({p['cabina']})"
                    desc.append(pax)
                desc.append("")  # Línea en blanco entre grupos
        else:
            # Formato simple sin agrupar
            desc.append("\nPasajeros:")
            for p in pasajeros_a_mostrar:
                nombre = _formatear_nombre_pasajero(p.get('nombre', ''))
                pax = f"• {nombre}"
                if p.get('asiento'):
                    pax += f" - {p['asiento']}"
                if p.get('cabina'):
                    pax += f" ({p['cabina']})"
                desc.append(pax)
    
    # Horarios y detalles específicos por tipo
    if tipo == 'vuelo':
        if viaje.hora_salida and viaje.hora_llegada:
            desc.append(f"\nSalida: {viaje.origen} a las {viaje.hora_salida} (hora local)")
            desc.append(f"Llegada: {viaje.destino} a las {viaje.hora_llegada} (hora local)")

        if viaje.terminal:
            if ' a ' in viaje.terminal.lower():
                parts = viaje.terminal.split(' a ')
                desc.append(f"Terminal salida: {parts[0].strip()}")
                if len(parts) > 1:
                    desc.append(f"Terminal llegada: {parts[1].strip()}")
            else:
                desc.append(f"Terminal salida: {viaje.terminal}")

        if viaje.puerta:
            desc.append(f"Puerta: {viaje.puerta}")
    elif tipo == 'hotel':
        if viaje.hora_salida:
            desc.append(f"\nCheck-in: {viaje.hora_salida}")
        if viaje.hora_llegada:
            desc.append(f"Check-out: {viaje.hora_llegada}")
    elif tipo in ['espectaculo', 'restaurante', 'actividad']:
        if viaje.hora_salida:
            desc.append(f"\nHora: {viaje.hora_salida}")
    elif tipo in ['barco', 'crucero', 'tren', 'transfer']:
        if viaje.hora_salida:
            desc.append(f"\nSalida: {viaje.hora_salida}")
        if viaje.hora_llegada:
            desc.append(f"Llegada: {viaje.hora_llegada}")

    event.add('description', '\n'.join(desc))

    # Determinar si es evento all-day
    es_allday = _es_evento_allday(viaje)

    if es_allday:
        # Eventos all-day: usar formato DATE (sin hora)
        fecha_inicio = viaje.fecha_salida.date()

        # Calcular fecha_fin
        if viaje.fecha_llegada:
            # DTEND es EXCLUSIVO: el día DESPUÉS del último día
            fecha_fin = viaje.fecha_llegada.date() + timedelta(days=1)
        else:
            # Estimar duración
            if tipo == 'hotel':
                fecha_fin = fecha_inicio + timedelta(days=2)  # 1 noche = check-out al día siguiente
            elif tipo == 'auto':
                fecha_fin = fecha_inicio + timedelta(days=8)  # 7 días
            else:
                fecha_fin = fecha_inicio + timedelta(days=2)

        # Para all-day events, NO usar tz.localize, solo fecha
        event.add('dtstart', fecha_inicio)
        event.add('dtend', fecha_fin)

    else:
        # Eventos con hora específica: usar formato DATETIME

        # Para barco/crucero (ferries), intentar leer hora de raw_data
        if tipo in ['barco', 'crucero']:
            raw = {}
            if viaje.raw_data:
                try:
                    raw = json.loads(viaje.raw_data)
                except:
                    pass

            hora_embarque = raw.get('hora_embarque') or raw.get('hora_salida') or viaje.hora_salida or '09:00'
            hora_desembarque = raw.get('hora_desembarque') or raw.get('hora_llegada') or viaje.hora_llegada or '12:00'

            try:
                hora_inicio = datetime.strptime(hora_embarque, '%H:%M').time()
            except:
                hora_inicio = datetime.strptime('09:00', '%H:%M').time()

            try:
                hora_fin = datetime.strptime(hora_desembarque, '%H:%M').time()
            except:
                hora_fin = datetime.strptime('12:00', '%H:%M').time()

            dtstart = datetime.combine(viaje.fecha_salida, hora_inicio)
            if viaje.fecha_llegada:
                dtend = datetime.combine(viaje.fecha_llegada, hora_fin)
            else:
                dtend = datetime.combine(viaje.fecha_salida, hora_fin)

        else:
            # Otros tipos: usar hora_salida/hora_llegada normales
            if viaje.hora_salida:
                try:
                    hora_inicio = datetime.strptime(viaje.hora_salida, '%H:%M').time()
                except:
                    hora_inicio = datetime.strptime('09:00', '%H:%M').time()
            else:
                # Horas por defecto según tipo
                if tipo == 'espectaculo':
                    hora_inicio = datetime.strptime('20:00', '%H:%M').time()
                elif tipo == 'restaurante':
                    hora_inicio = datetime.strptime('20:00', '%H:%M').time()
                else:
                    hora_inicio = datetime.strptime('09:00', '%H:%M').time()

            dtstart = datetime.combine(viaje.fecha_salida, hora_inicio)

            # Calcular dtend
            if viaje.fecha_llegada and viaje.hora_llegada:
                try:
                    hora_fin = datetime.strptime(viaje.hora_llegada, '%H:%M').time()
                    dtend = datetime.combine(viaje.fecha_llegada, hora_fin)
                except:
                    dtend = dtstart + timedelta(hours=2)
            elif viaje.fecha_llegada:
                # Tiene fecha_llegada pero no hora
                dtend = datetime.combine(viaje.fecha_llegada, hora_inicio)
            else:
                # No tiene fecha_llegada - estimar duración
                if tipo == 'espectaculo':
                    dtend = dtstart + timedelta(hours=3)
                elif tipo == 'restaurante':
                    dtend = dtstart + timedelta(hours=2)
                elif tipo == 'actividad':
                    dtend = dtstart + timedelta(hours=4)
                elif tipo == 'transfer':
                    dtend = dtstart + timedelta(hours=1)
                else:
                    dtend = dtstart + timedelta(hours=2)

        event.add('dtstart', tz.localize(dtstart))
        event.add('dtend', tz.localize(dtend))

    # Location según tipo
    if tipo == 'vuelo':
        location = f'{viaje.origen} Airport'
    elif tipo in ['hotel', 'espectaculo', 'restaurante', 'actividad']:
        location = viaje.ubicacion or viaje.proveedor or viaje.descripcion
    elif tipo in ['barco', 'crucero']:
        location = f'Puerto {viaje.origen}' if viaje.origen else (viaje.proveedor or 'Puerto')
    elif tipo == 'tren':
        location = f'Estación {viaje.origen}' if viaje.origen else 'Estación'
    elif tipo in ['auto', 'transfer']:
        location = viaje.origen or viaje.ubicacion or viaje.descripcion
    else:
        location = viaje.ubicacion or viaje.origen or viaje.descripcion

    event.add('location', location or '')

    # UID único y estable
    event.add('uid', f'{tipo}-{viaje.id}@miagenteviajes.local')
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
