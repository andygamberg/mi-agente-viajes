from fr24sdk.client import Client
from fr24sdk.exceptions import ApiError, AuthenticationError, Fr24SdkError
from datetime import datetime, timedelta
import os
import json

def check_flight_status(numero_vuelo, fecha_salida):
    """
    Chequea el estado actual de un vuelo específico
    
    Args:
        numero_vuelo (str): Código del vuelo (ej: "AR1303")
        fecha_salida (datetime): Fecha de salida del vuelo
    
    Returns:
        dict con: {
            'encontrado': bool,
            'estado': str,  # 'on_time', 'delayed', 'cancelled', 'in_flight', 'landed'
            'delay_minutos': int,
            'datetime_takeoff_actual': datetime,
            'datetime_landed_actual': datetime,
            'cambios': list  # Lista de cambios detectados
        }
    """
    try:
        with Client() as client:
            # Buscar vuelo en rango de +/- 1 día por si cambió fecha
            # FORMATO CORRECTO: datetime object sin microsegundos
            fecha_desde = (fecha_salida - timedelta(days=1)).replace(microsecond=0, second=0, minute=0, hour=0)
            fecha_hasta = (fecha_salida + timedelta(days=1)).replace(microsecond=0, second=59, minute=59, hour=23)
            
            result = client.flight_summary.get_light(
                flights=[numero_vuelo],
                flight_datetime_from=fecha_desde,
                flight_datetime_to=fecha_hasta
            )
            
            if not result.data or len(result.data) == 0:
                return {
                    'encontrado': False,
                    'estado': 'no_found',
                    'cambios': []
                }
            
            # Tomar el vuelo más cercano a la fecha original
            vuelo = result.data[0]
            
            # Parsear fechas
            takeoff_actual = datetime.fromisoformat(vuelo.datetime_takeoff.replace('Z', '+00:00')) if vuelo.datetime_takeoff else None
            landed_actual = datetime.fromisoformat(vuelo.datetime_landed.replace('Z', '+00:00')) if vuelo.datetime_landed else None
            
            # Determinar estado
            if vuelo.flight_ended:
                estado = 'landed'
            elif landed_actual:
                estado = 'landed'
            elif takeoff_actual and takeoff_actual < datetime.now(takeoff_actual.tzinfo):
                estado = 'in_flight'
            else:
                estado = 'on_time'  # Por defecto, calcularemos delay después
            
            # Calcular delay (comparar con hora programada)
            delay_minutos = 0
            if takeoff_actual:
                # Convertir fecha_salida a timezone-aware si no lo es
                if fecha_salida.tzinfo is None:
                    import pytz
                    tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
                    fecha_salida = tz_arg.localize(fecha_salida)
                
                diferencia = (takeoff_actual - fecha_salida).total_seconds() / 60
                delay_minutos = int(diferencia)
                
                if delay_minutos > 15:  # Más de 15 min = delayed
                    estado = 'delayed'
            
            return {
                'encontrado': True,
                'estado': estado,
                'delay_minutos': delay_minutos,
                'datetime_takeoff_actual': takeoff_actual,
                'datetime_landed_actual': landed_actual,
                'flight_ended': vuelo.flight_ended,
                'dest_icao_actual': vuelo.dest_icao_actual,
                'cambios': []  # Se detectarán comparando con BD
            }
            
    except AuthenticationError as e:
        print(f"❌ Error de autenticación FR24: {e}")
        return {'encontrado': False, 'estado': 'error', 'error': 'auth_error'}
    except ApiError as e:
        print(f"❌ API Error FR24: {e.status} - {e.message}")
        return {'encontrado': False, 'estado': 'error', 'error': f'api_error_{e.status}'}
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return {'encontrado': False, 'estado': 'error', 'error': str(e)}


def check_all_upcoming_flights(db_session):
    """
    Chequea todos los vuelos próximos (dentro de 48 horas)
    
    Args:
        db_session: Sesión de SQLAlchemy
    
    Returns:
        list de dicts con cambios detectados
    """
    from models import Viaje
    
    now = datetime.now()
    limite = now + timedelta(hours=48)
    
    # Obtener vuelos próximos
    vuelos_proximos = db_session.query(Viaje).filter(
        Viaje.tipo == 'vuelo',
        Viaje.fecha_salida >= now,
        Viaje.fecha_salida <= limite
    ).all()
    
    cambios_detectados = []
    
    for vuelo in vuelos_proximos:
        if not vuelo.numero_vuelo:
            continue
        
        print(f"🔍 Chequeando {vuelo.numero_vuelo} - {vuelo.origen}→{vuelo.destino}...")
        
        status = check_flight_status(vuelo.numero_vuelo, vuelo.fecha_salida)
        
        if not status['encontrado']:
            print(f"   ⚠️  No encontrado en FR24")
            continue
        
        # Detectar cambios
        cambios = []
        
        # 1. Delay significativo
        if status['delay_minutos'] > 30:
            cambios.append({
                'tipo': 'delay',
                'valor_anterior': 'On time',
                'valor_nuevo': f"{status['delay_minutos']} min delay",
                'severidad': 'alta' if status['delay_minutos'] > 120 else 'media'
            })
        
        # 2. Cancelación (muy raro en API, pero posible)
        if status['estado'] == 'cancelled':
            cambios.append({
                'tipo': 'cancelacion',
                'severidad': 'critica'
            })
        
        # 3. Cambio de aeropuerto destino
        if status['dest_icao_actual'] and vuelo.destino:
            if status['dest_icao_actual'] != vuelo.destino:
                cambios.append({
                    'tipo': 'destino_cambiado',
                    'valor_anterior': vuelo.destino,
                    'valor_nuevo': status['dest_icao_actual'],
                    'severidad': 'alta'
                })
        
        if cambios:
            cambios_detectados.append({
                'vuelo_id': vuelo.id,
                'numero_vuelo': vuelo.numero_vuelo,
                'ruta': f"{vuelo.origen}→{vuelo.destino}",
                'fecha_salida': vuelo.fecha_salida,
                'status_fr24': status,
                'cambios': cambios
            })
            print(f"   ⚠️  {len(cambios)} cambio(s) detectado(s)")
            
            # ACTUALIZAR BD con nuevos horarios
            if status.get('datetime_takeoff_actual'):
                vuelo.fecha_salida = status['datetime_takeoff_actual']
                vuelo.hora_salida = status['datetime_takeoff_actual'].strftime('%H:%M')
            
            if status.get('datetime_landed_actual'):
                vuelo.fecha_llegada = status['datetime_landed_actual']
                vuelo.hora_llegada = status['datetime_landed_actual'].strftime('%H:%M')

            # Actualizar campos FR24 para badges y tracking
            vuelo.ultima_actualizacion_fr24 = datetime.now()
            vuelo.status_fr24 = status.get('estado', 'unknown')
            vuelo.delay_minutos = status.get('delay_minutos', 0)

            db_session.commit()
            print(f"   💾 BD actualizada con nuevos horarios")
        else:
            print(f"   ✅ On time")
    
    return cambios_detectados


if __name__ == '__main__':
    # Testing local
    import sys
    if len(sys.argv) > 1:
        vuelo = sys.argv[1]
        fecha = datetime.now()
        result = check_flight_status(vuelo, fecha)
        print(json.dumps(result, default=str, indent=2))
