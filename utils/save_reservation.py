"""
Función unificada para guardar reservas desde cualquier flujo.
Centraliza la lógica de guardado en datos JSONB.
"""
import json
from datetime import datetime
from models import db, Viaje
from utils.schema_helpers import get_fecha_inicio, get_fecha_fin


def parse_fecha(fecha_str):
    """Parsea fecha string a datetime"""
    if not fecha_str:
        return None
    if isinstance(fecha_str, datetime):
        return fecha_str
    try:
        return datetime.strptime(fecha_str, '%Y-%m-%d')
    except:
        return None


def extraer_fecha_inicio(datos, tipo):
    """Extrae fecha de inicio del dict de datos según tipo"""
    campos = {
        'hotel': 'fecha_checkin',
        'crucero': 'fecha_embarque',
        'auto': 'fecha_retiro',
        'restaurante': 'fecha',
        'espectaculo': 'fecha',
        'actividad': 'fecha',
        'transfer': 'fecha',
        'tren': 'fecha_salida',
        'vuelo': 'fecha_salida',
    }
    campo = campos.get(tipo, 'fecha_salida')
    return parse_fecha(datos.get(campo) or datos.get('fecha_salida') or datos.get('fecha'))


def extraer_fecha_fin(datos, tipo):
    """Extrae fecha de fin del dict de datos según tipo"""
    campos = {
        'hotel': 'fecha_checkout',
        'crucero': 'fecha_desembarque',
        'auto': 'fecha_devolucion',
        'tren': 'fecha_llegada',
        'vuelo': 'fecha_llegada',
    }
    campo = campos.get(tipo, 'fecha_llegada')
    return parse_fecha(datos.get(campo) or datos.get('fecha_llegada'))


def save_reservation(user_id, datos_dict, grupo_id=None, nombre_viaje=None):
    """
    Guarda una reserva desde cualquier flujo.

    Args:
        user_id: ID del usuario
        datos_dict: Dict con datos de la reserva (de Claude o de form)
        grupo_id: ID de grupo opcional
        nombre_viaje: Nombre del viaje opcional

    Returns:
        Viaje creado

    Raises:
        ValueError si no hay fecha válida
    """
    tipo = datos_dict.get('tipo', 'vuelo')

    # Extraer fechas para columnas índice
    fecha_salida = extraer_fecha_inicio(datos_dict, tipo)
    fecha_llegada = extraer_fecha_fin(datos_dict, tipo)

    if not fecha_salida:
        raise ValueError(f"Reserva sin fecha válida: {datos_dict.get('descripcion', 'sin descripción')}")

    # Asegurar que tipo esté en datos
    datos_dict['tipo'] = tipo

    viaje = Viaje(
        user_id=user_id,
        tipo=tipo,
        fecha_salida=fecha_salida,
        fecha_llegada=fecha_llegada,
        grupo_viaje=grupo_id,
        nombre_viaje=nombre_viaje,
        datos=datos_dict,
        # Columnas legacy para compatibilidad (transición)
        descripcion=datos_dict.get('descripcion', ''),
        origen=datos_dict.get('origen') or datos_dict.get('puerto_embarque') or datos_dict.get('lugar_retiro') or '',
        destino=datos_dict.get('destino') or datos_dict.get('puerto_desembarque') or datos_dict.get('lugar_devolucion') or '',
        codigo_reserva=datos_dict.get('codigo_reserva', ''),
        proveedor=datos_dict.get('aerolinea') or datos_dict.get('nombre_propiedad') or datos_dict.get('embarcacion') or datos_dict.get('empresa') or datos_dict.get('nombre') or datos_dict.get('evento') or datos_dict.get('operador') or '',
        precio=datos_dict.get('precio') or datos_dict.get('precio_total') or '',
        raw_data=json.dumps(datos_dict, ensure_ascii=False),
    )

    db.session.add(viaje)
    return viaje


def update_reservation(viaje, datos_dict):
    """
    Actualiza una reserva existente.

    Args:
        viaje: Instancia de Viaje a actualizar
        datos_dict: Dict con nuevos datos

    Returns:
        Viaje actualizado
    """
    tipo = datos_dict.get('tipo', viaje.tipo or 'vuelo')

    # Actualizar columnas índice
    viaje.tipo = tipo
    viaje.fecha_salida = extraer_fecha_inicio(datos_dict, tipo) or viaje.fecha_salida
    viaje.fecha_llegada = extraer_fecha_fin(datos_dict, tipo)

    # Asegurar tipo en datos
    datos_dict['tipo'] = tipo

    # Actualizar JSONB
    viaje.datos = datos_dict

    # Actualizar columnas legacy para compatibilidad
    viaje.descripcion = datos_dict.get('descripcion', '')
    viaje.origen = datos_dict.get('origen') or datos_dict.get('puerto_embarque') or datos_dict.get('lugar_retiro') or ''
    viaje.destino = datos_dict.get('destino') or datos_dict.get('puerto_desembarque') or datos_dict.get('lugar_devolucion') or ''
    viaje.codigo_reserva = datos_dict.get('codigo_reserva', '')
    viaje.proveedor = datos_dict.get('aerolinea') or datos_dict.get('nombre_propiedad') or datos_dict.get('embarcacion') or datos_dict.get('empresa') or datos_dict.get('nombre') or datos_dict.get('evento') or datos_dict.get('operador') or ''
    viaje.precio = datos_dict.get('precio') or datos_dict.get('precio_total') or ''
    viaje.raw_data = json.dumps(datos_dict, ensure_ascii=False)

    viaje.actualizado = datetime.utcnow()

    return viaje
