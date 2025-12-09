"""
Procesa emails de misviajes@gamberg.com.ar y los guarda en BD
"""
import json
import uuid
import os
import sys
import unicodedata
from email_processor import fetch_emails_with_attachments, mark_as_read
from app import app
from utils import extraer_info_con_claude, get_ciudad_nombre
from models import db, Viaje, User, UserEmail
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


def find_user_by_passenger(pasajeros):
    """
    Busca usuario por nombre en lista de pasajeros.
    
    Lógica de matching:
    1. Normaliza nombres (quita acentos, mayúsculas)
    2. Apellido debe coincidir exactamente
    3. Cualquier nombre del usuario debe coincidir con cualquier nombre en la reserva
    
    Ejemplo:
    - Usuario: nombres="María Laura", apellido="Pérez"
    - Reserva: "PEREZ/MARIA LAURA BEATRIZ"
    - Match: ✅ (apellido exacto + "MARIA" aparece en ambos)
    """
    if not pasajeros:
        return None
    
    # Obtener todos los usuarios con apellido configurado
    users = User.query.filter(User.apellido_pax.isnot(None)).all()
    if not users:
        return None
    
    for pax in pasajeros:
        nombre_pax = pax.get('nombre', '').upper()
        if not nombre_pax:
            continue
        
        # Formato típico: APELLIDO/NOMBRE1 NOMBRE2 NOMBRE3
        if '/' in nombre_pax:
            parts = nombre_pax.split('/')
            apellido_reserva = normalize_name(parts[0])
            nombres_reserva = normalize_name(parts[1]).split() if len(parts) > 1 else []
        else:
            # Sin formato estándar, intentar dividir (primer palabra = apellido)
            words = nombre_pax.split()
            apellido_reserva = normalize_name(words[0]) if words else ''
            nombres_reserva = [normalize_name(w) for w in words[1:]] if len(words) > 1 else []
        
        if not apellido_reserva:
            continue
        
        # Buscar match con usuarios
        for user in users:
            user_apellido = normalize_name(user.apellido_pax)
            user_nombres = normalize_name(user.nombre_pax).split() if user.nombre_pax else []
            
            # 1. Apellido debe coincidir exactamente
            if apellido_reserva != user_apellido:
                continue
            
            # 2. Al menos un nombre debe coincidir
            if not user_nombres:
                # Si el usuario no tiene nombres configurados, match solo por apellido
                print(f'  👤 Usuario encontrado por apellido: {user.nombre} (match: {nombre_pax})')
                return user.id
            
            # Buscar si algún nombre del usuario aparece en la reserva
            nombres_match = any(
                user_nombre in nombres_reserva or 
                any(user_nombre in reserva_nombre or reserva_nombre in user_nombre 
                    for reserva_nombre in nombres_reserva)
                for user_nombre in user_nombres
            )
            
            if nombres_match:
                print(f'  👤 Usuario encontrado: {user.nombre} (match: {nombre_pax})')
                return user.id
    
    return None


def calcular_ciudad_principal_dict(vuelos):
    """Calcula la ciudad donde se pasa más tiempo (para diccionarios)"""
    from datetime import datetime
    
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

def process_emails():
    """Lee emails, extrae vuelos con Claude, guarda en BD"""
    
    with app.app_context():
        print('🔍 Buscando emails nuevos...')
        emails = fetch_emails_with_attachments()
        
        if not emails:
            print('✅ No hay emails nuevos para procesar')
            return
        
        vuelos_creados = 0
        vuelos_actualizados = 0
        emails_procesados = 0
        
        for email in emails:
            print(f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            print(f'📧 Procesando: {email["subject"][:60]}...')
            
            # Extraer vuelos con Claude API
            try:
                vuelos = extraer_info_con_claude(email['body'])
                
                if not vuelos or len(vuelos) == 0:
                    print('⚠️  No se detectaron vuelos en este email')
                    try:
                        mark_as_read(email['id'])
                    except Exception as e:
                        print(f'⚠️  No se pudo marcar como leído: {e}')
                    continue
                
                print(f'✈️  Detectados {len(vuelos)} vuelos')
                
                # Generar grupo_viaje para esta reserva
                grupo_id = str(uuid.uuid4())[:8]
                
                # Calcular ciudad principal (donde más tiempo se pasa)
                ciudad_principal = calcular_ciudad_principal_dict(vuelos)
                ciudad_nombre = get_ciudad_nombre(ciudad_principal)
                nombre_viaje = f"Viaje a {ciudad_nombre}" if ciudad_principal else "Viaje"
                
                # Guardar cada vuelo
                for vuelo_data in vuelos:
                    # Chequear duplicados
                    existe = check_duplicate(vuelo_data)
                    
                    if existe:
                        print(f'🔄 Actualizando vuelo existente: {vuelo_data.get("numero_vuelo")}')
                        update_flight(existe, vuelo_data)
                        vuelos_actualizados += 1
                    else:
                        print(f'✨ Creando nuevo vuelo: {vuelo_data.get("numero_vuelo")}')
                        create_flight(vuelo_data, grupo_id, nombre_viaje, email.get('from'))
                        vuelos_creados += 1
                
                # Marcar email como leído
                try:
                    mark_as_read(email['id'])
                except Exception as e:
                    print(f'⚠️  No se pudo marcar como leído: {e}')
                emails_procesados += 1
                
            except Exception as e:
                print(f'❌ Error procesando email: {e}')
                import traceback
                traceback.print_exc()
        
        print(f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        print(f'📊 RESUMEN:')
        print(f'  • Emails procesados: {emails_procesados}')
        print(f'  • Vuelos nuevos: {vuelos_creados}')
        print(f'  • Vuelos actualizados: {vuelos_actualizados}')
        
        return {'emails': emails_procesados, 'creados': vuelos_creados, 'actualizados': vuelos_actualizados}

def check_duplicate(vuelo_data):
    """Chequea si el vuelo ya existe en BD (por PNR + vuelo + ruta)"""
    if not vuelo_data.get('numero_vuelo'):
        return None
    
    # Buscar por código reserva + número vuelo + origen + destino
    # (sin fecha, para detectar cambios de horario)
    existe = Viaje.query.filter_by(
        codigo_reserva=vuelo_data.get('codigo_reserva'),
        numero_vuelo=vuelo_data.get('numero_vuelo'),
        origen=vuelo_data.get('origen'),
        destino=vuelo_data.get('destino')
    ).first()
    
    return existe

def create_flight(vuelo_data, grupo_id=None, nombre_viaje=None, from_email=None):
    """Crea nuevo vuelo en BD"""
    from datetime import datetime
    
    # Parsear fecha_salida
    fecha_salida = None
    fecha_salida_str = vuelo_data.get('fecha_salida')
    hora_salida = vuelo_data.get('hora_salida', '')
    if fecha_salida_str:
        try:
            if hora_salida:
                fecha_salida = datetime.strptime(f"{fecha_salida_str} {hora_salida}", '%Y-%m-%d %H:%M')
            else:
                fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
        except:
            fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
    
    # Parsear fecha_llegada
    fecha_llegada = None
    fecha_llegada_str = vuelo_data.get('fecha_llegada')
    hora_llegada = vuelo_data.get('hora_llegada', '')
    if fecha_llegada_str:
        try:
            if hora_llegada:
                fecha_llegada = datetime.strptime(f"{fecha_llegada_str} {hora_llegada}", '%Y-%m-%d %H:%M')
            else:
                fecha_llegada = datetime.strptime(fecha_llegada_str, '%Y-%m-%d')
        except:
            pass
    
    # Buscar usuario por email remitente
    user_id = None
    if from_email:
        # Extraer email limpio (puede venir como "Nombre <email@x.com>")
        import re
        email_match = re.search(r'<(.+?)>', from_email)
        clean_email = email_match.group(1) if email_match else from_email
        clean_email = clean_email.strip().lower()
        
        # Buscar por email principal
        user = User.query.filter_by(email=clean_email).first()
        if user:
            user_id = user.id
            print(f'  👤 Usuario identificado: {user.nombre} ({clean_email})')
        else:
            # Buscar en emails adicionales
            user_email = UserEmail.query.filter_by(email=clean_email).first()
            if user_email:
                user_id = user_email.user_id
                user = User.query.get(user_id)
                print(f'  👤 Usuario identificado por email adicional: {user.nombre} ({clean_email})')
            else:
                print(f'  ⚠️ Usuario no encontrado por email: {clean_email}')
                # Intentar buscar por nombre de pasajero
                pasajeros = vuelo_data.get('pasajeros', [])
                user_id = find_user_by_passenger(pasajeros)
                if user_id:
                    print(f'  ✅ Usuario asignado por nombre de pasajero')
    
    viaje = Viaje(
        user_id=user_id,
        tipo='vuelo',
        descripcion=f"{vuelo_data.get('origen')} → {vuelo_data.get('destino')}",
        origen=vuelo_data.get('origen'),
        destino=vuelo_data.get('destino'),
        fecha_salida=fecha_salida,
        fecha_llegada=fecha_llegada,
        hora_salida=hora_salida,
        hora_llegada=hora_llegada,
        aerolinea=vuelo_data.get('aerolinea'),
        numero_vuelo=vuelo_data.get('numero_vuelo'),
        codigo_reserva=vuelo_data.get('codigo_reserva'),
        asiento=vuelo_data.get('asiento'),
        pasajeros=json.dumps(vuelo_data.get('pasajeros')) if vuelo_data.get('pasajeros') else None,
        grupo_viaje=grupo_id,
        nombre_viaje=nombre_viaje
    )
    
    db.session.add(viaje)
    db.session.commit()
    
    print(f'  ✅ Vuelo guardado (ID: {viaje.id})')

def update_flight(viaje, vuelo_data):
    """Actualiza vuelo existente (incluyendo cambios de fecha/hora)"""
    from datetime import datetime as dt
    
    # Actualizar fecha_salida si cambió
    fecha_salida_str = vuelo_data.get('fecha_salida')
    hora_salida = vuelo_data.get('hora_salida', '')
    if fecha_salida_str:
        try:
            if hora_salida:
                nueva_fecha = dt.strptime(f"{fecha_salida_str} {hora_salida}", '%Y-%m-%d %H:%M')
            else:
                nueva_fecha = dt.strptime(fecha_salida_str, '%Y-%m-%d')
            viaje.fecha_salida = nueva_fecha
        except:
            pass
    
    # Actualizar fecha_llegada si cambió
    fecha_llegada_str = vuelo_data.get('fecha_llegada')
    hora_llegada = vuelo_data.get('hora_llegada', '')
    if fecha_llegada_str:
        try:
            if hora_llegada:
                nueva_fecha = dt.strptime(f"{fecha_llegada_str} {hora_llegada}", '%Y-%m-%d %H:%M')
            else:
                nueva_fecha = dt.strptime(fecha_llegada_str, '%Y-%m-%d')
            viaje.fecha_llegada = nueva_fecha
        except:
            pass
    
    # Actualizar otros campos
    if vuelo_data.get('hora_salida'):
        viaje.hora_salida = vuelo_data.get('hora_salida')
    if vuelo_data.get('hora_llegada'):
        viaje.hora_llegada = vuelo_data.get('hora_llegada')
    if vuelo_data.get('asiento'):
        viaje.asiento = vuelo_data.get('asiento')
    if vuelo_data.get('terminal'):
        viaje.terminal = vuelo_data.get('terminal')
    if vuelo_data.get('puerta'):
        viaje.puerta = vuelo_data.get('puerta')
    
    viaje.actualizado = datetime.now()
    db.session.commit()
    
    print(f'  ✅ Vuelo actualizado (ID: {viaje.id})')

if __name__ == '__main__':
    process_emails()
