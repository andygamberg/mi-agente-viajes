"""
Scheduler inteligente para monitoreo de vuelos
Ajusta frecuencia según proximidad del vuelo
"""
from datetime import datetime, timedelta
from flight_monitor import check_all_upcoming_flights
import os

def get_check_frequency_minutes(vuelo):
    """
    Retorna minutos hasta próximo check según proximidad del vuelo
    
    Estrategia:
    - Más de 7 días: 1x por día (1440 min)
    - 7-2 días: 2x por día (720 min)
    - 48-24h: cada 6h (360 min)
    - 24-12h: cada 1h (60 min)
    - 12-2h: cada 30 min
    - Menos de 2h: cada 15 min
    """
    ahora = datetime.now()
    tiempo_hasta = (vuelo.fecha_salida - ahora).total_seconds() / 3600  # en horas
    
    if tiempo_hasta > 168:      # >7 días
        return 1440  # 24 horas
    elif tiempo_hasta > 48:     # 7-2 días  
        return 720   # 12 horas
    elif tiempo_hasta > 24:     # 48-24 horas
        return 360   # 6 horas
    elif tiempo_hasta > 12:     # 24-12 horas
        return 60    # 1 hora
    elif tiempo_hasta > 2:      # 12-2 horas
        return 30    # 30 minutos
    else:                       # <2 horas
        return 15    # 15 minutos

def should_check_now(vuelo):
    """
    Determina si el vuelo debe chequearse ahora
    basado en última actualización y frecuencia
    """
    if not vuelo.ultima_actualizacion_fr24:
        return True  # Nunca chequeado
    
    frecuencia_min = get_check_frequency_minutes(vuelo)
    tiempo_desde_ultima = (datetime.now() - vuelo.ultima_actualizacion_fr24).total_seconds() / 60
    
    return tiempo_desde_ultima >= frecuencia_min

def get_vuelos_to_check(db_session):
    """
    Retorna lista de vuelos que deben chequearse ahora
    según estrategia de frecuencia dinámica
    """
    from models import Viaje
    
    # Vuelos próximos (dentro de 30 días hacia adelante)
    ahora = datetime.now()
    fecha_limite = ahora + timedelta(days=30)
    
    vuelos = db_session.query(Viaje).filter(
        Viaje.fecha_salida >= ahora,
        Viaje.fecha_salida <= fecha_limite
    ).all()
    
    # Filtrar según estrategia
    vuelos_to_check = [v for v in vuelos if should_check_now(v)]
    
    return vuelos_to_check

def calcular_estadisticas_creditos(db_session):
    """
    Calcula estimación de créditos que se usarán este mes
    """
    from models import Viaje
    
    ahora = datetime.now()
    fin_mes = ahora + timedelta(days=30)
    
    vuelos = db_session.query(Viaje).filter(
        Viaje.fecha_salida >= ahora,
        Viaje.fecha_salida <= fin_mes
    ).all()
    
    total_checks = 0
    
    for vuelo in vuelos:
        dias_hasta = (vuelo.fecha_salida - ahora).days
        horas_hasta = (vuelo.fecha_salida - ahora).total_seconds() / 3600
        
        if dias_hasta > 7:
            # 1x por día hasta los 7 días
            checks = dias_hasta - 7
        else:
            checks = 0
            
        # 7-2 días: 2x por día
        if 2 <= dias_hasta <= 7:
            checks += 5 * 2  # 5 días × 2 checks
            
        # 48-24h: cada 6h = 4 checks
        if horas_hasta <= 48:
            checks += 4
            
        # 24-12h: cada 1h = 12 checks
        if horas_hasta <= 24:
            checks += 12
            
        # 12-2h: cada 30min = 20 checks
        if horas_hasta <= 12:
            checks += 20
            
        # <2h: cada 15min = 8 checks
        if horas_hasta <= 2:
            checks += 8
            
        total_checks += checks
    
    creditos_estimados = total_checks * 10  # asumiendo 10 créditos por check
    
    return {
        'total_vuelos': len(vuelos),
        'checks_estimados': total_checks,
        'creditos_estimados': creditos_estimados,
        'creditos_disponibles': 60000,  # con promo
        'margen': 60000 - creditos_estimados
    }

if __name__ == '__main__':
    from app import app
    from models import db
    
    with app.app_context():
        stats = calcular_estadisticas_creditos(db.session)
        print(f"\n📊 Estadísticas de uso de créditos FR24:")
        print(f"  Vuelos próximos (30 días): {stats['total_vuelos']}")
        print(f"  Checks estimados: {stats['checks_estimados']}")
        print(f"  Créditos estimados: {stats['creditos_estimados']:,}")
        print(f"  Créditos disponibles: {stats['creditos_disponibles']:,}")
        print(f"  Margen: {stats['margen']:,} ({stats['margen']/stats['creditos_disponibles']*100:.1f}%)")
