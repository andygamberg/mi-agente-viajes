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
    # Obtener código de reserva de cualquier fuente (columna legacy o JSONB)
    codigo_reserva = viaje.codigo_reserva
    if not codigo_reserva and viaje.datos:
        datos = viaje.datos if isinstance(viaje.datos, dict) else {}
        codigo_reserva = datos.get('codigo_reserva', '')

    # Manual siempre puede
    if viaje.source == 'manual':
        return True

    # PDF sin código de reserva = probablemente vuelo privado
    if viaje.source == 'pdf_upload' and not codigo_reserva:
        return True

    # Retrocompatibilidad: registros sin source (NULL o string vacío)
    if viaje.source is None or viaje.source == '':
        # Sin código de reserva = asumir manual (permisivo)
        if not codigo_reserva:
            return True
        # Con código de reserva = asumir importado automáticamente (restrictivo)
        return False

    # Cualquier otro source (gmail, microsoft, email_forward) = no modificable
    return False
