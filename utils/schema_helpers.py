"""
Helpers para trabajar con datos JSONB y schemas.
"""
from datetime import datetime


def get_dato(viaje, key, default=''):
    """Extrae dato de JSONB con fallback a columnas legacy"""
    # Primero intentar desde datos JSONB
    if viaje.datos and isinstance(viaje.datos, dict):
        valor = viaje.datos.get(key)
        if valor is not None:
            return valor

    # Fallback a columnas legacy (transición)
    if hasattr(viaje, key):
        return getattr(viaje, key, default) or default

    return default


def get_fecha_inicio(viaje):
    """Extrae fecha de inicio según tipo"""
    datos = viaje.datos or {}
    tipo = viaje.tipo or 'vuelo'

    # Mapeo de campo fecha por tipo
    campos_fecha = {
        'hotel': 'fecha_checkin',
        'crucero': 'fecha_embarque',
        'auto': 'fecha_retiro',
        'restaurante': 'fecha',
        'espectaculo': 'fecha',
        'actividad': 'fecha',
        'transfer': 'fecha',
    }

    campo = campos_fecha.get(tipo, 'fecha_salida')
    fecha_str = datos.get(campo) or datos.get('fecha_salida') or datos.get('fecha')

    if fecha_str:
        try:
            if isinstance(fecha_str, str):
                return datetime.strptime(fecha_str, '%Y-%m-%d')
            return fecha_str
        except:
            pass

    # Fallback a columna BD
    return viaje.fecha_salida


def get_fecha_fin(viaje):
    """Extrae fecha de fin según tipo"""
    datos = viaje.datos or {}
    tipo = viaje.tipo or 'vuelo'

    campos_fecha = {
        'hotel': 'fecha_checkout',
        'crucero': 'fecha_desembarque',
        'auto': 'fecha_devolucion',
    }

    campo = campos_fecha.get(tipo, 'fecha_llegada')
    fecha_str = datos.get(campo) or datos.get('fecha_llegada')

    if fecha_str:
        try:
            if isinstance(fecha_str, str):
                return datetime.strptime(fecha_str, '%Y-%m-%d')
            return fecha_str
        except:
            pass

    return viaje.fecha_llegada


def get_titulo_card(viaje):
    """Genera título para card según tipo"""
    datos = viaje.datos or {}
    tipo = viaje.tipo or 'vuelo'

    if tipo == 'vuelo':
        aerolinea = datos.get('aerolinea', '')
        numero = datos.get('numero_vuelo', '')
        return f"{aerolinea} {numero}".strip() or 'Vuelo'

    elif tipo == 'hotel':
        return datos.get('nombre_propiedad') or 'Hotel'

    elif tipo == 'crucero':
        return datos.get('embarcacion') or datos.get('compania') or 'Crucero'

    elif tipo == 'auto':
        empresa = datos.get('empresa', '')
        modelo = datos.get('modelo', '')
        return f"{empresa} - {modelo}".strip(' -') or 'Rental'

    elif tipo == 'restaurante':
        return datos.get('nombre') or 'Restaurante'

    elif tipo == 'espectaculo':
        return datos.get('evento') or 'Espectáculo'

    elif tipo == 'actividad':
        return datos.get('nombre') or datos.get('proveedor') or 'Actividad'

    elif tipo == 'tren':
        return datos.get('operador') or 'Tren'

    elif tipo == 'bus':
        empresa = datos.get('empresa', '')
        origen = datos.get('origen', '')
        destino = datos.get('destino', '')
        if empresa and origen and destino:
            return f"{empresa} {origen} → {destino}"
        elif origen and destino:
            return f"{origen} → {destino}"
        return datos.get('descripcion') or 'Bus'

    elif tipo == 'transfer':
        return datos.get('empresa') or 'Transfer'

    return datos.get('descripcion') or 'Reserva'


def get_subtitulo_card(viaje):
    """Genera subtítulo para card según tipo"""
    datos = viaje.datos or {}
    tipo = viaje.tipo or 'vuelo'

    if tipo in ['vuelo', 'tren', 'transfer', 'bus']:
        origen = datos.get('origen', '')
        destino = datos.get('destino', '')
        if origen and destino:
            return f"{origen} → {destino}"

    elif tipo == 'hotel':
        return datos.get('direccion') or ''

    elif tipo == 'crucero':
        embarque = datos.get('puerto_embarque', '')
        desembarque = datos.get('puerto_desembarque', '')
        if embarque and desembarque:
            return f"{embarque} → {desembarque}"

    elif tipo == 'auto':
        retiro = datos.get('lugar_retiro', '')
        devolucion = datos.get('lugar_devolucion', '')
        if retiro and devolucion:
            return f"{retiro} → {devolucion}"

    elif tipo == 'restaurante':
        return datos.get('direccion') or ''

    elif tipo == 'espectaculo':
        return datos.get('venue') or ''

    elif tipo == 'actividad':
        return datos.get('punto_encuentro') or ''

    return ''
