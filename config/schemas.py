"""
Schemas de reservas por tipo.
Define qué campos tiene cada tipo y cómo se muestran en cards/forms.
"""

RESERVATION_SCHEMAS = {
    'vuelo': {
        'titulo': 'Vuelo',
        'icono': 'paper-airplane',
        'campos': [
            {'key': 'aerolinea', 'label': 'Aerolínea', 'type': 'text', 'card': True},
            {'key': 'numero_vuelo', 'label': 'Número de vuelo', 'type': 'text', 'card': True},
            {'key': 'origen', 'label': 'Origen', 'type': 'text', 'card': True, 'required': True},
            {'key': 'destino', 'label': 'Destino', 'type': 'text', 'card': True, 'required': True},
            {'key': 'fecha_salida', 'label': 'Fecha salida', 'type': 'date', 'required': True},
            {'key': 'hora_salida', 'label': 'Hora salida', 'type': 'time', 'card': True},
            {'key': 'fecha_llegada', 'label': 'Fecha llegada', 'type': 'date'},
            {'key': 'hora_llegada', 'label': 'Hora llegada', 'type': 'time'},
            {'key': 'terminal', 'label': 'Terminal', 'type': 'text'},
            {'key': 'puerta', 'label': 'Puerta', 'type': 'text'},
            {'key': 'pasajeros', 'label': 'Pasajeros', 'type': 'list', 'item_fields': ['nombre', 'asiento']},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text', 'card': True},
            {'key': 'precio', 'label': 'Precio', 'type': 'text', 'card': False},
        ]
    },
    'hotel': {
        'titulo': 'Hotel',
        'icono': 'building-office',
        'campos': [
            {'key': 'nombre_propiedad', 'label': 'Hotel', 'type': 'text', 'card': True},
            {'key': 'direccion', 'label': 'Dirección', 'type': 'text', 'card': True},
            {'key': 'fecha_checkin', 'label': 'Check-in', 'type': 'date', 'required': True},
            {'key': 'hora_checkin', 'label': 'Hora check-in', 'type': 'time'},
            {'key': 'fecha_checkout', 'label': 'Check-out', 'type': 'date'},
            {'key': 'hora_checkout', 'label': 'Hora check-out', 'type': 'time'},
            {'key': 'habitacion', 'label': 'Habitación', 'type': 'text'},
            {'key': 'huespedes', 'label': 'Huéspedes', 'type': 'list', 'item_fields': ['nombre']},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text', 'card': True},
            {'key': 'precio', 'label': 'Precio', 'type': 'text', 'card': False},
            {'key': 'notas', 'label': 'Notas', 'type': 'textarea'},
        ]
    },
    'crucero': {
        'titulo': 'Crucero / Ferry',
        'icono': 'lifebuoy',
        'campos': [
            {'key': 'embarcacion', 'label': 'Embarcación', 'type': 'text', 'card': True},
            {'key': 'compania', 'label': 'Compañía', 'type': 'text'},
            {'key': 'puerto_embarque', 'label': 'Puerto embarque', 'type': 'text', 'card': True},
            {'key': 'puerto_desembarque', 'label': 'Puerto desembarque', 'type': 'text', 'card': True},
            {'key': 'fecha_embarque', 'label': 'Fecha embarque', 'type': 'date', 'required': True},
            {'key': 'hora_embarque', 'label': 'Hora embarque', 'type': 'time', 'card': True},
            {'key': 'fecha_desembarque', 'label': 'Fecha desembarque', 'type': 'date'},
            {'key': 'hora_llegada', 'label': 'Hora llegada', 'type': 'time', 'card': True},
            {'key': 'cabina', 'label': 'Cabina / Camarote', 'type': 'text'},
            {'key': 'pasajeros', 'label': 'Pasajeros', 'type': 'list', 'item_fields': ['nombre']},
            {'key': 'vehiculos', 'label': 'Vehículos', 'type': 'list', 'item_fields': ['tipo', 'patente', 'marca'], 'card': True},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text', 'card': True},
            {'key': 'precio', 'label': 'Precio', 'type': 'text', 'card': False},
        ]
    },
    'auto': {
        'titulo': 'Rental de Auto',
        'icono': 'truck',
        'campos': [
            {'key': 'empresa', 'label': 'Empresa', 'type': 'text', 'card': True},
            {'key': 'categoria', 'label': 'Categoría', 'type': 'text'},
            {'key': 'modelo', 'label': 'Modelo', 'type': 'text', 'card': True},
            {'key': 'lugar_retiro', 'label': 'Lugar retiro', 'type': 'text', 'card': True},
            {'key': 'lugar_devolucion', 'label': 'Lugar devolución', 'type': 'text', 'card': True},
            {'key': 'fecha_retiro', 'label': 'Fecha retiro', 'type': 'date', 'required': True},
            {'key': 'hora_retiro', 'label': 'Hora retiro', 'type': 'time'},
            {'key': 'fecha_devolucion', 'label': 'Fecha devolución', 'type': 'date'},
            {'key': 'hora_devolucion', 'label': 'Hora devolución', 'type': 'time'},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text', 'card': True},
            {'key': 'precio', 'label': 'Precio', 'type': 'text', 'card': False},
        ]
    },
    'restaurante': {
        'titulo': 'Restaurante',
        'icono': 'cake',
        'campos': [
            {'key': 'nombre', 'label': 'Restaurante', 'type': 'text', 'card': True},
            {'key': 'direccion', 'label': 'Dirección', 'type': 'text', 'card': True},
            {'key': 'fecha', 'label': 'Fecha', 'type': 'date', 'required': True},
            {'key': 'hora', 'label': 'Hora', 'type': 'time', 'card': True},
            {'key': 'comensales', 'label': 'Comensales', 'type': 'number', 'card': True},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text'},
            {'key': 'notas', 'label': 'Notas', 'type': 'textarea'},
        ]
    },
    'espectaculo': {
        'titulo': 'Espectáculo',
        'icono': 'ticket',
        'campos': [
            {'key': 'evento', 'label': 'Evento', 'type': 'text', 'card': True},
            {'key': 'venue', 'label': 'Lugar', 'type': 'text', 'card': True},
            {'key': 'fecha', 'label': 'Fecha', 'type': 'date', 'required': True},
            {'key': 'hora', 'label': 'Hora', 'type': 'time', 'card': True},
            {'key': 'entradas', 'label': 'Cantidad entradas', 'type': 'number', 'card': True},
            {'key': 'sector', 'label': 'Sector', 'type': 'text', 'card': True},
            {'key': 'detalles_entradas', 'label': 'Detalles', 'type': 'list', 'item_fields': ['asiento', 'fila', 'seccion']},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text'},
            {'key': 'precio', 'label': 'Precio', 'type': 'text', 'card': False},
        ]
    },
    'actividad': {
        'titulo': 'Actividad / Tour',
        'icono': 'map-pin',
        'campos': [
            {'key': 'nombre', 'label': 'Actividad', 'type': 'text', 'card': True},
            {'key': 'proveedor', 'label': 'Proveedor', 'type': 'text'},
            {'key': 'punto_encuentro', 'label': 'Punto de encuentro', 'type': 'text', 'card': True},
            {'key': 'fecha', 'label': 'Fecha', 'type': 'date', 'required': True},
            {'key': 'hora', 'label': 'Hora', 'type': 'time', 'card': True},
            {'key': 'duracion', 'label': 'Duración', 'type': 'text'},
            {'key': 'participantes', 'label': 'Participantes', 'type': 'list', 'item_fields': ['nombre']},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text'},
            {'key': 'precio', 'label': 'Precio', 'type': 'text', 'card': False},
        ]
    },
    'tren': {
        'titulo': 'Tren',
        'icono': 'truck',  # No hay train en heroicons outline
        'campos': [
            {'key': 'operador', 'label': 'Operador', 'type': 'text', 'card': True},
            {'key': 'numero_tren', 'label': 'Número de tren', 'type': 'text'},
            {'key': 'origen', 'label': 'Estación origen', 'type': 'text', 'card': True},
            {'key': 'destino', 'label': 'Estación destino', 'type': 'text', 'card': True},
            {'key': 'fecha_salida', 'label': 'Fecha salida', 'type': 'date', 'required': True},
            {'key': 'hora_salida', 'label': 'Hora salida', 'type': 'time', 'card': True},
            {'key': 'fecha_llegada', 'label': 'Fecha llegada', 'type': 'date'},
            {'key': 'hora_llegada', 'label': 'Hora llegada', 'type': 'time'},
            {'key': 'pasajeros', 'label': 'Pasajeros', 'type': 'list', 'item_fields': ['nombre', 'asiento']},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text', 'card': True},
            {'key': 'precio', 'label': 'Precio', 'type': 'text', 'card': False},
        ]
    },
    'transfer': {
        'titulo': 'Transfer',
        'icono': 'arrow-path',
        'campos': [
            {'key': 'empresa', 'label': 'Empresa', 'type': 'text', 'card': True},
            {'key': 'origen', 'label': 'Punto recogida', 'type': 'text', 'card': True},
            {'key': 'destino', 'label': 'Destino', 'type': 'text', 'card': True},
            {'key': 'fecha', 'label': 'Fecha', 'type': 'date', 'required': True},
            {'key': 'hora', 'label': 'Hora', 'type': 'time', 'card': True},
            {'key': 'codigo_reserva', 'label': 'Código reserva', 'type': 'text'},
            {'key': 'notas', 'label': 'Notas', 'type': 'textarea'},
        ]
    },
}


def get_schema(tipo):
    """Retorna schema del tipo o vuelo como default"""
    return RESERVATION_SCHEMAS.get(tipo, RESERVATION_SCHEMAS['vuelo'])


def get_all_tipos():
    """Retorna lista de tipos disponibles"""
    return [(k, v['titulo']) for k, v in RESERVATION_SCHEMAS.items()]
