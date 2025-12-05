"""
Procesa emails de misviajes@gamberg.com.ar y los guarda en BD
"""
import os
import sys
from email_processor import fetch_unread_emails, mark_as_read
from app import app, db, Viaje, extraer_info_con_claude
from datetime import datetime

def process_emails():
    """Lee emails, extrae vuelos con Claude, guarda en BD"""
    
    with app.app_context():
        print('🔍 Buscando emails nuevos...')
        emails = fetch_unread_emails()
        
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
                    mark_as_read(email['id'])
                    continue
                
                print(f'✈️  Detectados {len(vuelos)} vuelos')
                
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
                        create_flight(vuelo_data)
                        vuelos_creados += 1
                
                # Marcar email como leído
                mark_as_read(email['id'])
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

def create_flight(vuelo_data):
    """Crea nuevo vuelo en BD"""
    viaje = Viaje(
        tipo='vuelo',
        descripcion=f"{vuelo_data.get('origen')} → {vuelo_data.get('destino')}",
        origen=vuelo_data.get('origen'),
        destino=vuelo_data.get('destino'),
        fecha_salida=vuelo_data.get('fecha_salida'),
        fecha_llegada=vuelo_data.get('fecha_llegada'),
        hora_salida=vuelo_data.get('hora_salida'),
        hora_llegada=vuelo_data.get('hora_llegada'),
        aerolinea=vuelo_data.get('aerolinea'),
        numero_vuelo=vuelo_data.get('numero_vuelo'),
        codigo_reserva=vuelo_data.get('codigo_reserva'),
        asiento=vuelo_data.get('asiento'),
        pasajeros=vuelo_data.get('pasajeros')
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
