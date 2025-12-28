"""
Utilidad para obtener timezone de aeropuertos y convertir horas UTC a local.
"""
from datetime import datetime
import pytz

# Mapeo de aeropuertos IATA -> timezone
# Incluye los aeropuertos más comunes de Latinoamérica y destinos frecuentes
AIRPORT_TIMEZONES = {
    # Argentina
    'EZE': 'America/Argentina/Buenos_Aires',
    'AEP': 'America/Argentina/Buenos_Aires',
    'COR': 'America/Argentina/Cordoba',
    'MDZ': 'America/Argentina/Mendoza',
    'BRC': 'America/Argentina/Salta',  # Bariloche
    'IGR': 'America/Argentina/Buenos_Aires',  # Iguazú
    'USH': 'America/Argentina/Ushuaia',
    'SLA': 'America/Argentina/Salta',
    'TUC': 'America/Argentina/Tucuman',
    'ROS': 'America/Argentina/Cordoba',
    'NQN': 'America/Argentina/Salta',
    'FTE': 'America/Argentina/Rio_Gallegos',  # El Calafate

    # Brasil
    'GRU': 'America/Sao_Paulo',
    'GIG': 'America/Sao_Paulo',
    'SDU': 'America/Sao_Paulo',
    'CGH': 'America/Sao_Paulo',
    'BSB': 'America/Sao_Paulo',
    'CNF': 'America/Sao_Paulo',
    'POA': 'America/Sao_Paulo',
    'FLN': 'America/Sao_Paulo',
    'REC': 'America/Recife',
    'SSA': 'America/Bahia',
    'FOR': 'America/Fortaleza',
    'MAO': 'America/Manaus',

    # Chile
    'SCL': 'America/Santiago',
    'IQQ': 'America/Santiago',
    'PUQ': 'America/Punta_Arenas',

    # Uruguay
    'MVD': 'America/Montevideo',

    # Paraguay
    'ASU': 'America/Asuncion',

    # Perú
    'LIM': 'America/Lima',
    'CUZ': 'America/Lima',

    # Colombia
    'BOG': 'America/Bogota',
    'MDE': 'America/Bogota',
    'CTG': 'America/Bogota',

    # México
    'MEX': 'America/Mexico_City',
    'CUN': 'America/Cancun',
    'GDL': 'America/Mexico_City',
    'MTY': 'America/Monterrey',

    # Panamá
    'PTY': 'America/Panama',

    # USA
    'MIA': 'America/New_York',
    'JFK': 'America/New_York',
    'EWR': 'America/New_York',
    'LGA': 'America/New_York',
    'LAX': 'America/Los_Angeles',
    'SFO': 'America/Los_Angeles',
    'ORD': 'America/Chicago',
    'DFW': 'America/Chicago',
    'ATL': 'America/New_York',
    'IAH': 'America/Chicago',
    'DEN': 'America/Denver',
    'LAS': 'America/Los_Angeles',
    'PHX': 'America/Phoenix',
    'SEA': 'America/Los_Angeles',
    'BOS': 'America/New_York',
    'PHL': 'America/New_York',
    'IAD': 'America/New_York',
    'DCA': 'America/New_York',
    'MCO': 'America/New_York',
    'FLL': 'America/New_York',
    'TPA': 'America/New_York',
    'SAN': 'America/Los_Angeles',

    # Europa
    'MAD': 'Europe/Madrid',
    'BCN': 'Europe/Madrid',
    'FCO': 'Europe/Rome',
    'MXP': 'Europe/Rome',
    'LHR': 'Europe/London',
    'LGW': 'Europe/London',
    'STN': 'Europe/London',
    'CDG': 'Europe/Paris',
    'ORY': 'Europe/Paris',
    'AMS': 'Europe/Amsterdam',
    'FRA': 'Europe/Berlin',
    'MUC': 'Europe/Berlin',
    'ZRH': 'Europe/Zurich',
    'VIE': 'Europe/Vienna',
    'LIS': 'Europe/Lisbon',
    'OPO': 'Europe/Lisbon',
    'DUB': 'Europe/Dublin',

    # Otros
    'DXB': 'Asia/Dubai',
    'DOH': 'Asia/Qatar',
    'IST': 'Europe/Istanbul',
    'TLV': 'Asia/Jerusalem',
    'SYD': 'Australia/Sydney',
    'MEL': 'Australia/Melbourne',
    'AKL': 'Pacific/Auckland',
    'NRT': 'Asia/Tokyo',
    'HND': 'Asia/Tokyo',
    'HKG': 'Asia/Hong_Kong',
    'SIN': 'Asia/Singapore',
    'BKK': 'Asia/Bangkok',
}


def get_airport_timezone(iata_code):
    """
    Obtiene la timezone de un aeropuerto por su código IATA.

    Args:
        iata_code: Código IATA del aeropuerto (ej: 'EZE', 'MIA')

    Returns:
        pytz timezone object, o None si no se encuentra
    """
    if not iata_code:
        return None

    iata_code = iata_code.upper().strip()
    tz_name = AIRPORT_TIMEZONES.get(iata_code)

    if tz_name:
        try:
            return pytz.timezone(tz_name)
        except:
            return None

    return None


def utc_to_airport_local(utc_datetime, iata_code, fallback_tz='America/Argentina/Buenos_Aires'):
    """
    Convierte datetime UTC a hora local del aeropuerto.

    Args:
        utc_datetime: datetime en UTC (puede ser aware o naive)
        iata_code: Código IATA del aeropuerto
        fallback_tz: Timezone a usar si no se encuentra el aeropuerto

    Returns:
        datetime en hora local del aeropuerto (timezone-aware)
    """
    if not utc_datetime:
        return None

    # Asegurar que sea timezone-aware UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.UTC.localize(utc_datetime)
    else:
        utc_datetime = utc_datetime.astimezone(pytz.UTC)

    # Obtener timezone del aeropuerto
    airport_tz = get_airport_timezone(iata_code)
    if not airport_tz:
        airport_tz = pytz.timezone(fallback_tz)

    # Convertir
    return utc_datetime.astimezone(airport_tz)


def format_local_time(utc_datetime, iata_code, format_str='%H:%M'):
    """
    Convierte UTC a hora local y la formatea como string.

    Args:
        utc_datetime: datetime en UTC
        iata_code: Código IATA del aeropuerto
        format_str: Formato de salida (default: 'HH:MM')

    Returns:
        String con la hora local formateada
    """
    local_dt = utc_to_airport_local(utc_datetime, iata_code)
    if local_dt:
        return local_dt.strftime(format_str)
    return None
