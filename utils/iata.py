"""
Mapeo de códigos IATA a ciudades - Mi Agente Viajes
"""

IATA_TO_CITY = {
    # Argentina
    'EZE': 'Buenos Aires',
    'AEP': 'Buenos Aires',
    'COR': 'Córdoba',
    'MDZ': 'Mendoza',
    'FTE': 'El Calafate',
    'USH': 'Ushuaia',
    'IGR': 'Iguazú',
    
    # Chile
    'SCL': 'Santiago',
    'IPC': 'Isla de Pascua',
    'PUQ': 'Punta Arenas',
    'PMC': 'Puerto Montt',
    'ANF': 'Antofagasta',
    
    # Brasil
    'GRU': 'São Paulo',
    'GIG': 'Rio de Janeiro',
    'BSB': 'Brasilia',
    'SSA': 'Salvador',
    'FOR': 'Fortaleza',
    
    # USA
    'JFK': 'New York',
    'LAX': 'Los Angeles',
    'MIA': 'Miami',
    'ORD': 'Chicago',
    'SFO': 'San Francisco',
    'LAS': 'Las Vegas',
    'ATL': 'Atlanta',
    
    # Europa
    'MAD': 'Madrid',
    'BCN': 'Barcelona',
    'CDG': 'Paris',
    'LHR': 'London',
    'FCO': 'Roma',
    'OLB': 'Olbia',
    'AMS': 'Amsterdam',
    'FRA': 'Frankfurt',
    'MUC': 'Munich',
    'ZRH': 'Zurich',
    'VIE': 'Vienna',
    
    # Centroamérica y Caribe
    'PTY': 'Panama',
    'BZE': 'Belice',
    'CUN': 'Cancún',
    'MEX': 'Ciudad de México',
    'LIM': 'Lima',
    'BOG': 'Bogotá',
    'UIO': 'Quito',
    'GYE': 'Guayaquil',
    
    # Asia
    'NRT': 'Tokyo',
    'HND': 'Tokyo',
    'BKK': 'Bangkok',
    'SIN': 'Singapore',
    'HKG': 'Hong Kong',
    'DXB': 'Dubai',
    
    # Oceanía
    'SYD': 'Sydney',
    'AKL': 'Auckland',
    'MEL': 'Melbourne',
    
    # África
    'JNB': 'Johannesburg',
    'CPT': 'Cape Town',
    'CAI': 'Cairo',
    
    # Más Europa
    'LIS': 'Lisboa',
    'VCE': 'Venice',
    'MXP': 'Milano',
    'IST': 'Istanbul',
    'ATH': 'Athens',
    'PRG': 'Prague',
    'BUD': 'Budapest',
    'WAW': 'Warsaw',
    
    # Más USA
    'BOS': 'Boston',
    'SEA': 'Seattle',
    'DEN': 'Denver',
    'PHX': 'Phoenix',
    'IAH': 'Houston',
    'DFW': 'Dallas',
    'MSP': 'Minneapolis',
    
    # Más Sudamérica
    'MVD': 'Montevideo',
    'ASU': 'Asunción',
    'SCZ': 'Santa Cruz',
    'CNF': 'Belo Horizonte',
    'CCS': 'Caracas',
    
    # Caribe adicional
    'SJU': 'San Juan',
    'PUJ': 'Punta Cana',
    'HAV': 'La Habana',
    'MBJ': 'Montego Bay',
    
    # Centroamérica adicional
    'SAL': 'San Salvador',
    'GUA': 'Guatemala',
    'SJO': 'San José',
    'MGA': 'Managua',
}


def get_ciudad_nombre(codigo_iata):
    """Convierte código IATA a nombre de ciudad"""
    if not codigo_iata:
        return None
    return IATA_TO_CITY.get(codigo_iata.upper(), codigo_iata)
