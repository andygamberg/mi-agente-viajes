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
    - Reservas manuales: siempre modificables
    - PDFs sin PNR: modificables (vuelos privados, charters)
    - Reservas automáticas con PNR: no modificables individualmente
      (para mantener integridad del PNR completo)
    """
    # Manual siempre puede
    if viaje.source == 'manual':
        return True

    # PDF sin código de reserva = probablemente vuelo privado
    if viaje.source == 'pdf_upload' and not viaje.codigo_reserva:
        return True

    # Retrocompatibilidad: registros sin source
    if viaje.source is None:
        # Sin código = asumir manual
        if not viaje.codigo_reserva:
            return True
        # Con código = asumir automático (restrictivo)
        return False

    return False
