"""
Funciones helper - Mi Agente Viajes
"""
import unicodedata
import json
from datetime import datetime


def normalize_name(name):
    """
    Normaliza un nombre para comparación:
    - Quita acentos (Andrés → ANDRES)
    - Convierte a mayúsculas
    - Quita espacios extra
    """
    if not name:
        return ''
    # Normalizar unicode (NFD separa caracteres base de acentos)
    normalized = unicodedata.normalize('NFD', name)
    # Filtrar solo caracteres ASCII (quita acentos)
    ascii_only = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Mayúsculas y quitar espacios extra
    return ' '.join(ascii_only.upper().split())


def extraer_personas_de_datos(viaje):
    """
    BUG-PASSENGER-MATCH: Extrae lista de personas del campo datos JSONB.

    Busca en los campos:
    - pasajeros (crucero, tren)
    - huespedes (hotel)
    - participantes (actividad)

    Retorna lista de dicts con formato: [{"nombre": "APELLIDO/NOMBRE"}]
    """
    if not viaje.datos:
        return []

    datos = viaje.datos if isinstance(viaje.datos, dict) else {}
    personas = []

    # Campos que contienen personas según el tipo
    for campo in ['pasajeros', 'huespedes', 'participantes']:
        valor = datos.get(campo, [])
        if isinstance(valor, list):
            for item in valor:
                if isinstance(item, dict):
                    nombre = item.get('nombre', '')
                    if nombre:
                        personas.append({'nombre': nombre})
                elif isinstance(item, str):
                    # Lista de strings: ["Andres Gamberg", "Veronica Gerszkowicz"]
                    personas.append({'nombre': item})

    return personas


def get_viajes_for_user(user, Viaje, User):
    """
    MVP7: Obtiene viajes donde el usuario:
    1. Es owner (user_id), O
    2. Aparece como pasajero (matching por nombre)
    
    Args:
        user: Usuario actual
        Viaje: Modelo Viaje (pasado para evitar import circular)
        User: Modelo User (pasado para evitar import circular)
    """
    # Query base: viajes donde soy owner
    viajes_propios = Viaje.query.filter_by(user_id=user.id).all()
    viajes_ids = {v.id for v in viajes_propios}
    
    # Si el usuario tiene apellido_pax configurado, buscar también por pasajero
    if user.apellido_pax:
        user_apellido = normalize_name(user.apellido_pax)
        user_nombres = normalize_name(user.nombre_pax).split() if user.nombre_pax else []

        # BUG-PASSENGER-MATCH: Buscar en TODOS los viajes (no solo los que tienen pasajeros legacy)
        todos_viajes = Viaje.query.all()

        for viaje in todos_viajes:
            if viaje.id in viajes_ids:
                continue  # Ya lo tenemos

            try:
                # 1. Buscar en columna legacy pasajeros (compatibilidad)
                pasajeros = json.loads(viaje.pasajeros) if viaje.pasajeros else []

                # 2. TAMBIÉN buscar en datos JSONB (huespedes, participantes, etc.)
                personas_datos = extraer_personas_de_datos(viaje)
                pasajeros.extend(personas_datos)

                # 3. Verificar match con cualquier persona encontrada
                for pax in pasajeros:
                    nombre_pax = pax.get('nombre', '').upper()

                    # Parsear formato APELLIDO/NOMBRES o "Nombre Apellido"
                    if '/' in nombre_pax:
                        parts = nombre_pax.split('/')
                        apellido_reserva = normalize_name(parts[0])
                        nombres_reserva = normalize_name(parts[1]).split() if len(parts) > 1 else []
                    else:
                        words = nombre_pax.split()
                        apellido_reserva = normalize_name(words[-1]) if words else ''  # Último palabra = apellido
                        nombres_reserva = [normalize_name(w) for w in words[:-1]]

                    # Match: apellido exacto + algún nombre coincide
                    if apellido_reserva == user_apellido:
                        if not user_nombres:
                            # Solo apellido configurado = match
                            viajes_propios.append(viaje)
                            viajes_ids.add(viaje.id)
                            break
                        else:
                            # Buscar match en nombres
                            match_found = False
                            for user_nombre in user_nombres:
                                if any(user_nombre in nr or nr in user_nombre for nr in nombres_reserva):
                                    viajes_propios.append(viaje)
                                    viajes_ids.add(viaje.id)
                                    match_found = True
                                    break
                            if match_found:
                                break
            except:
                pass
    
    return viajes_propios


def calcular_ciudad_principal(vuelos):
    """Calcula la ciudad donde se pasa más tiempo"""
    if not vuelos:
        return None
    
    # Si es solo un vuelo, usar destino
    if len(vuelos) == 1:
        return vuelos[0].destino
    
    # Calcular tiempo en cada ciudad
    tiempo_por_ciudad = {}
    
    for i, vuelo in enumerate(vuelos):
        # Tiempo en ciudad destino
        if i < len(vuelos) - 1:  # No es el último vuelo
            proximo = vuelos[i + 1]
            
            # Si hay fecha/hora de llegada y próxima salida
            if vuelo.fecha_salida and proximo.fecha_salida:
                try:
                    # Usar fecha_salida como datetime (ya tiene hora)
                    llegada = vuelo.fecha_salida  # Esto es un datetime
                    salida_proxima = proximo.fecha_salida
                    
                    if isinstance(llegada, datetime) and isinstance(salida_proxima, datetime):
                        horas = (salida_proxima - llegada).total_seconds() / 3600
                        ciudad = vuelo.destino
                        
                        if ciudad not in tiempo_por_ciudad:
                            tiempo_por_ciudad[ciudad] = 0
                        tiempo_por_ciudad[ciudad] += horas
                except:
                    pass
    
    # Si no pudimos calcular, usar destino final
    if not tiempo_por_ciudad:
        return vuelos[-1].destino
    
    # Retornar ciudad con más horas
    return max(tiempo_por_ciudad, key=tiempo_por_ciudad.get)


def calcular_ciudad_principal_dict(vuelos):
    """Calcula la ciudad donde se pasa más tiempo (para diccionarios, usado en gmail_to_db)"""
    if not vuelos:
        return None
    
    # Si es solo un vuelo, usar destino
    if len(vuelos) == 1:
        return vuelos[0].get('destino')
    
    # Obtener origen inicial (de donde sale el viaje)
    origen_inicial = vuelos[0].get('origen', '')
    
    # Calcular tiempo en cada ciudad
    tiempo_por_ciudad = {}
    
    for i, vuelo in enumerate(vuelos[:-1]):  # Todos menos el último
        destino = vuelo.get('destino', '')
        fecha_llegada = vuelo.get('fecha_llegada') or vuelo.get('fecha_salida')
        fecha_salida_prox = vuelos[i + 1].get('fecha_salida')
        
        if fecha_llegada and fecha_salida_prox:
            try:
                # Parsear fechas si son strings
                if isinstance(fecha_llegada, str):
                    fecha_llegada = datetime.strptime(fecha_llegada, '%Y-%m-%d')
                if isinstance(fecha_salida_prox, str):
                    fecha_salida_prox = datetime.strptime(fecha_salida_prox, '%Y-%m-%d')
                
                dias = (fecha_salida_prox - fecha_llegada).days
                tiempo_por_ciudad[destino] = tiempo_por_ciudad.get(destino, 0) + max(dias, 0)
            except:
                pass
    
    # Si no pudimos calcular tiempos, buscar el destino que no sea el origen
    if not tiempo_por_ciudad:
        for v in vuelos:
            destino = v.get('destino', '')
            if destino and destino != origen_inicial:
                return destino
        return vuelos[-1].get('destino')
    
    # Excluir el origen inicial del cálculo
    if origen_inicial in tiempo_por_ciudad:
        del tiempo_por_ciudad[origen_inicial]
    
    # Retornar ciudad con más tiempo
    if tiempo_por_ciudad:
        return max(tiempo_por_ciudad, key=tiempo_por_ciudad.get)
    
    return vuelos[0].get('destino')


def deduplicar_vuelos_en_grupo(vuelos):
    """
    MVP11: Combina vuelos idénticos (mismo numero_vuelo + fecha + ruta)
    
    Retorna lista de vuelos donde los duplicados tienen pasajeros combinados.
    No modifica la BD - solo agrega atributos temporales para renderizado.
    
    Usado por:
    - viajes.py (index route) para UI web
    - calendario.py (calendar_feed) para eventos iCal
    
    Returns:
        Lista de vuelos con atributos temporales:
        - _es_combinado: bool
        - _pasajeros_combinados: list (solo si combinado)
        - _codigos_reserva: list (solo si combinado)
    """
    if not vuelos:
        return vuelos
    
    if len(vuelos) == 1:
        vuelos[0]._es_combinado = False
        return vuelos
    
    # Crear clave única para cada vuelo
    def vuelo_key(v):
        fecha = v.fecha_salida.date() if v.fecha_salida else None
        return (v.numero_vuelo, fecha, v.origen, v.destino)
    
    # Agrupar por clave
    grupos_vuelos = {}
    orden_original = []  # Para mantener orden por fecha
    
    for vuelo in vuelos:
        key = vuelo_key(vuelo)
        if key not in grupos_vuelos:
            grupos_vuelos[key] = []
            orden_original.append(key)
        grupos_vuelos[key].append(vuelo)
    
    # Procesar cada grupo
    resultado = []
    for key in orden_original:
        vuelos_iguales = grupos_vuelos[key]
        
        if len(vuelos_iguales) == 1:
            # No hay duplicado - marcar como no combinado
            vuelo = vuelos_iguales[0]
            vuelo._es_combinado = False
            resultado.append(vuelo)
        else:
            # Combinar pasajeros de todos los vuelos iguales
            vuelo_principal = vuelos_iguales[0]
            pasajeros_combinados = []
            codigos_reserva = []
            
            for v in vuelos_iguales:
                codigo = v.codigo_reserva or 'N/A'
                if codigo not in codigos_reserva:
                    codigos_reserva.append(codigo)
                
                # Parsear pasajeros
                try:
                    pax_list = json.loads(v.pasajeros) if v.pasajeros else []
                except:
                    pax_list = []
                
                # Agregar código de reserva a cada pasajero
                for p in pax_list:
                    p['codigo_reserva'] = codigo
                    pasajeros_combinados.append(p)
            
            # Agregar atributos temporales (no se guardan en BD)
            vuelo_principal._pasajeros_combinados = pasajeros_combinados
            vuelo_principal._codigos_reserva = codigos_reserva
            vuelo_principal._es_combinado = True
            resultado.append(vuelo_principal)
    
    # Ordenar por fecha
    resultado.sort(key=lambda v: v.fecha_salida)
    return resultado


def get_hora_salida_display(viaje):
    """
    Extrae la hora de salida/inicio según el tipo de viaje.
    Usado para countdown y display.
    """
    datos = viaje.datos or {}
    tipo = viaje.tipo or 'vuelo'

    # Mapeo de campos de hora por tipo
    campos_hora = {
        'vuelo': ['hora_salida'],
        'crucero': ['hora_embarque'],
        'barco': ['hora_embarque'],
        'ferry': ['hora_embarque'],
        'hotel': ['hora_checkin'],
        'auto': ['hora_retiro'],
        'tren': ['hora_salida'],
        'bus': ['hora_salida'],
        'transfer': ['hora_pickup', 'hora'],
        'restaurante': ['hora', 'hora_reserva'],
        'espectaculo': ['hora', 'hora_inicio'],
        'actividad': ['hora', 'hora_inicio'],
    }

    # Buscar en campos específicos del tipo
    for campo in campos_hora.get(tipo, ['hora_salida', 'hora']):
        hora = datos.get(campo)
        if hora:
            return hora

    # Fallback a columna legacy
    if viaje.hora_salida:
        return viaje.hora_salida

    return ''
