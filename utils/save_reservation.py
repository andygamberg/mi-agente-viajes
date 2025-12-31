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
        'bus': 'fecha_salida',
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
        'bus': 'fecha_llegada',
        'vuelo': 'fecha_llegada',
    }
    campo = campos.get(tipo, 'fecha_llegada')
    return parse_fecha(datos.get(campo) or datos.get('fecha_llegada'))


def save_reservation(user_id, datos_dict, grupo_id=None, nombre_viaje=None, source='manual'):
    """
    Guarda una reserva desde cualquier flujo.

    Args:
        user_id: ID del usuario
        datos_dict: Dict con datos de la reserva (de Claude o de form)
        grupo_id: ID de grupo opcional
        nombre_viaje: Nombre del viaje opcional
        source: Origen de la reserva ('manual', 'gmail', 'microsoft', 'email_forward', 'pdf_upload')

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
        source=source,
        # Columnas legacy para compatibilidad (transición)
        descripcion=datos_dict.get('descripcion', ''),
        origen=datos_dict.get('origen') or datos_dict.get('puerto_embarque') or datos_dict.get('lugar_retiro') or '',
        destino=datos_dict.get('destino') or datos_dict.get('puerto_desembarque') or datos_dict.get('lugar_devolucion') or '',
        codigo_reserva=datos_dict.get('codigo_reserva', ''),
        proveedor=datos_dict.get('aerolinea') or datos_dict.get('nombre_propiedad') or datos_dict.get('embarcacion') or datos_dict.get('empresa') or datos_dict.get('nombre') or datos_dict.get('evento') or datos_dict.get('operador') or '',
        precio=datos_dict.get('precio') or datos_dict.get('precio_total') or '',
        raw_data=json.dumps(datos_dict, ensure_ascii=False),
    )

    # Agregar código de aerolínea como alternativo si existe
    codigo_aerolinea = datos_dict.get('codigo_aerolinea')
    if codigo_aerolinea:
        viaje.add_codigo_alternativo(codigo_aerolinea)

    db.session.add(viaje)

    # Enviar push notification si no es manual Y usuario tiene preferencia activa
    if source != 'manual':
        try:
            from models import User
            user = User.query.get(user_id)
            if not user or not getattr(user, 'notif_nueva_reserva', True):
                pass  # No enviar si usuario desactivó esta preferencia
            else:
                from blueprints.push import send_reservation_notification
                send_reservation_notification(user_id, {
                    'tipo': tipo,
                    'descripcion': datos_dict.get('descripcion', ''),
                    'fecha': fecha_salida.strftime('%d/%m/%Y') if fecha_salida else '',
                    'codigo': datos_dict.get('codigo_reserva', ''),
                    'source': source
                })
        except Exception as e:
            # No fallar si push notification falla
            print(f"⚠️ Push notification failed: {e}")

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


def merge_reservation_data(existing_viaje, new_datos):
    """
    Actualiza una reserva existente con nueva información.
    SOBREESCRIBE cualquier campo que venga con valor nuevo.

    Args:
        existing_viaje: Viaje existente en BD
        new_datos: Dict con nuevos datos extraídos

    Returns:
        bool: True si hubo cambios
    """
    datos_actuales = existing_viaje.datos or {}
    hubo_cambios = False

    # Campos que NO se deben sobreescribir (identificadores únicos y de tramo)
    # Incluye campos de identidad de vuelo para evitar que ida sobrescriba vuelta
    campos_inmutables = ['tipo', 'codigo_reserva', 'numero_vuelo', 'origen', 'destino', 'fecha_salida', 'hora_salida']

    # Iterar sobre todos los campos nuevos
    for campo, nuevo_valor in new_datos.items():
        if campo in campos_inmutables:
            continue

        valor_actual = datos_actuales.get(campo)

        # Caso especial: pasajeros - merge inteligente
        if campo == 'pasajeros' and isinstance(nuevo_valor, list) and isinstance(valor_actual, list):
            pasajeros_changed = _merge_pasajeros(valor_actual, nuevo_valor)
            if pasajeros_changed:
                hubo_cambios = True
            continue

        # Para otros campos: sobreescribir si hay valor nuevo diferente
        if nuevo_valor is not None and nuevo_valor != valor_actual:
            valor_anterior = valor_actual
            datos_actuales[campo] = nuevo_valor
            hubo_cambios = True
            if valor_anterior:
                print(f"  📝 Actualizado {campo}: {valor_anterior} → {nuevo_valor}")
            else:
                print(f"  📝 Agregado {campo}: {nuevo_valor}")

    if hubo_cambios:
        existing_viaje.datos = datos_actuales
        existing_viaje.raw_data = json.dumps(datos_actuales, ensure_ascii=False)
        existing_viaje.actualizado = datetime.utcnow()

        # Actualizar columnas legacy también
        existing_viaje.descripcion = datos_actuales.get('descripcion', existing_viaje.descripcion or '')
        existing_viaje.origen = datos_actuales.get('origen') or datos_actuales.get('puerto_embarque') or datos_actuales.get('lugar_retiro') or existing_viaje.origen or ''
        existing_viaje.destino = datos_actuales.get('destino') or datos_actuales.get('puerto_desembarque') or datos_actuales.get('lugar_devolucion') or existing_viaje.destino or ''
        existing_viaje.proveedor = datos_actuales.get('aerolinea') or datos_actuales.get('nombre_propiedad') or datos_actuales.get('embarcacion') or datos_actuales.get('empresa') or datos_actuales.get('nombre') or datos_actuales.get('evento') or datos_actuales.get('operador') or existing_viaje.proveedor or ''
        existing_viaje.precio = datos_actuales.get('precio') or datos_actuales.get('precio_total') or existing_viaje.precio or ''

    return hubo_cambios


def _merge_pasajeros(pasajeros_actuales, nuevos_pasajeros):
    """
    Merge inteligente de pasajeros: actualiza info existente, agrega nuevos.
    """
    hubo_cambios = False

    for nuevo_pax in nuevos_pasajeros:
        if not isinstance(nuevo_pax, dict):
            continue

        nombre_nuevo = nuevo_pax.get('nombre', '').upper()
        if not nombre_nuevo:
            continue

        # Buscar pasajero existente por nombre
        pax_encontrado = None
        for pax_actual in pasajeros_actuales:
            if isinstance(pax_actual, dict):
                nombre_actual = pax_actual.get('nombre', '').upper()
                if nombre_nuevo and nombre_actual:
                    # Match flexible: uno contiene al otro
                    if nombre_nuevo in nombre_actual or nombre_actual in nombre_nuevo:
                        pax_encontrado = pax_actual
                        break

        if pax_encontrado:
            # Actualizar campos del pasajero existente
            for key, val in nuevo_pax.items():
                if val is not None and val != pax_encontrado.get(key):
                    valor_ant = pax_encontrado.get(key)
                    pax_encontrado[key] = val
                    hubo_cambios = True
                    if valor_ant:
                        print(f"  📝 Pasajero {nombre_nuevo}: {key} {valor_ant} → {val}")
                    else:
                        print(f"  📝 Pasajero {nombre_nuevo}: {key} = {val}")
        else:
            # Pasajero nuevo, agregar
            pasajeros_actuales.append(nuevo_pax)
            hubo_cambios = True
            print(f"  📝 Pasajero agregado: {nombre_nuevo}")

    return hubo_cambios
