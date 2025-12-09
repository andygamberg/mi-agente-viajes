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
        
        # Buscar en todos los viajes que tengan pasajeros
        todos_viajes = Viaje.query.filter(Viaje.pasajeros.isnot(None)).all()
        
        for viaje in todos_viajes:
            if viaje.id in viajes_ids:
                continue  # Ya lo tenemos
            
            try:
                pasajeros = json.loads(viaje.pasajeros) if viaje.pasajeros else []
                for pax in pasajeros:
                    nombre_pax = pax.get('nombre', '').upper()
                    
                    # Parsear formato APELLIDO/NOMBRES
                    if '/' in nombre_pax:
                        parts = nombre_pax.split('/')
                        apellido_reserva = normalize_name(parts[0])
                        nombres_reserva = normalize_name(parts[1]).split() if len(parts) > 1 else []
                    else:
                        words = nombre_pax.split()
                        apellido_reserva = normalize_name(words[0]) if words else ''
                        nombres_reserva = [normalize_name(w) for w in words[1:]]
                    
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
