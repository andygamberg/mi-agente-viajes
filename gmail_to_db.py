"""
Procesa emails de misviajes@gamberg.com.ar y los guarda en BD
"""
import json
import uuid
import os
import sys
from email_processor import fetch_emails_with_attachments, mark_as_read
from app import app, db, Viaje, extraer_info_con_claude, get_ciudad_nombre
from datetime import datetime


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
            print(f'�� Procesando: {email["subject"][:60]}...')
            
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
                        create_flight(vuelo_data, grupo_id, nombre_viaje)
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
    """Chequea si el vuelo ya existe en BD"""
    if not vuelo_data.get('numero_vuelo') or not vuelo_data.get('fecha_salida'):
        return None
    
    # Buscar por número de vuelo + fecha + origen + destino
    existe = Viaje.query.filter_by(
        numero_vuelo=vuelo_data.get('numero_vuelo'),
        fecha_salida=vuelo_data.get('fecha_salida'),
        origen=vuelo_data.get('origen'),
        destino=vuelo_data.get('destino')
    ).first()
    
    return existe

def create_flight(vuelo_data, grupo_id=None, nombre_viaje=None):
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
    
    viaje = Viaje(
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
    """Actualiza vuelo existente"""
    # Actualizar solo campos que vienen en el nuevo email
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
