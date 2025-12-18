"""
Helpers de permisos - Mi Agente Viajes
"""


def puede_modificar_segmento(viaje):
    """
    Determina si un segmento individual puede ser editado/borrado.

    Args:
        viaje: Objeto Viaje

    Returns:
        bool: True si puede modificarse individualmente

    Reglas:
    - Solo VUELOS con PNR de fuentes automáticas están bloqueados
    - Otros tipos (hotel, crucero, restaurante, etc.) siempre son editables
    - Reservas manuales: siempre modificables
    - PDFs sin PNR: modificables (vuelos privados, charters)
    """
    # Obtener tipo
    tipo = viaje.tipo or 'vuelo'

    # DEBUG: ver qué tipo tiene el viaje
    print(f"DEBUG puede_modificar: id={viaje.id}, tipo={tipo}, viaje.tipo={viaje.tipo}, source={viaje.source}")

    # Solo vuelos tienen restricción de PNR
    # Hoteles, cruceros, restaurantes, etc. siempre son editables
    if tipo != 'vuelo':
        return True

    # --- A partir de aquí, solo aplica a vuelos ---

    # Obtener código de reserva de cualquier fuente (columna legacy o JSONB)
    codigo_reserva = viaje.codigo_reserva
    if not codigo_reserva and viaje.datos:
        datos = viaje.datos if isinstance(viaje.datos, dict) else {}
        codigo_reserva = datos.get('codigo_reserva', '')

    # Manual siempre puede
    if viaje.source == 'manual':
        return True

    # PDF sin código de reserva = vuelo privado
    if viaje.source == 'pdf_upload' and not codigo_reserva:
        return True

    # Retrocompatibilidad: registros sin source (NULL o string vacío)
    if viaje.source is None or viaje.source == '':
        # Sin código de reserva = asumir manual (permisivo)
        if not codigo_reserva:
            return True
        # Con código de reserva = asumir importado automáticamente (restrictivo)
        return False

    # Cualquier otro source automático con PNR = no modificable
    return False
