"""
Extracción de información de reservas con Claude API - Mi Agente Viajes
Soporta: vuelos, hoteles, autos, cruceros, trenes, restaurantes, actividades, espectáculos, transfers
"""
import os
import json
import re
import logging
from datetime import datetime
import anthropic


def extraer_info_con_claude(email_text):
    """Extrae información de TODAS las reservas del email/PDF"""

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logging.error("❌ ANTHROPIC_API_KEY no configurada")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logging.error(f"❌ Error inicializando Anthropic: {e}")
        return None

    # Detectar año del contexto
    years = re.findall(r'20[2-9][0-9]', email_text)
    now = datetime.now()
    current_year = now.year

    target_year = current_year
    if years:
        # Solo considerar años razonables (máximo 3 años en el futuro)
        # Esto evita que números como PNR "2049" se interpreten como años
        max_reasonable_year = current_year + 3
        reasonable_years = [int(y) for y in years
                            if current_year <= int(y) <= max_reasonable_year]
        if reasonable_years:
            target_year = min(reasonable_years)
            print(f"  📅 Año detectado en documento: {target_year}")
        else:
            # Si no hay años razonables, asumir próximo año para viajes futuros
            target_year = current_year + 1
            print(f"  📅 Sin año válido detectado, usando: {target_year}")

    prompt = f"""Analiza este email/PDF de confirmación de reserva (cualquier idioma).

TIPOS DE RESERVAS A DETECTAR:
- vuelo: aerolíneas, confirmaciones de vuelo
- hotel: Booking, Airbnb, Marriott, Hilton, hostels
- auto: rental cars (Hertz, Avis, Enterprise, Localiza)
- crucero: MSC, Royal Caribbean, ferries
- tren: Eurostar, Renfe, Trenitalia, Amtrak
- restaurante: OpenTable, TheFork, Resy, confirmaciones directas
- actividad: tours, excursiones (Civitatis, GetYourGuide, Viator)
- espectaculo: Ticketmaster, entradas eventos, teatro, conciertos
- transfer: traslados aeropuerto, shuttles

CRÍTICO PARA VUELOS:
- Si hay vuelo de IDA y VUELTA, extraer AMBOS como objetos separados
- Cada tramo es un objeto independiente en el array
- No omitir el vuelo de regreso
- Verificar que el documento no tenga más páginas con otros tramos
- Un itinerario completo típicamente tiene 2+ segmentos (ida y vuelta)

CRÍTICO - DISTINCIÓN DE FECHAS:
- "FECHA DE EMISIÓN" o "FECHA DE EMISIÓN DEL BOLETO" = cuándo se compró el ticket (IGNORAR)
- "FECHA DE SALIDA" o fechas junto a rutas/destinos = cuándo viaja el pasajero (USAR ESTA)
- Buscar fechas en el ITINERARIO del viaje, no en la información del boleto/ticket
- Si el documento tiene encabezado con fecha del viaje (ej: "28 AGO 2026") usar ESA fecha
- NUNCA usar la fecha de emisión como fecha de salida del vuelo

IMPORTANTE:
- Extrae TODAS las reservas del documento
- Códigos IATA para aeropuertos en MAYÚSCULAS
- Fechas en formato YYYY-MM-DD
- Horas en formato HH:MM (24h)
- Si el email/PDF contiene múltiples tramos de transporte (ej: ferry + bus), extraer CADA tramo como objeto separado con su tipo correspondiente
- Los tramos de bus/ómnibus deben usar tipo: "bus"

IMPORTANTE - VALIDACIÓN:
- Si no podés extraer una fecha válida → NO incluyas el objeto en el array
- Si es una expedición, crucero de aventura, o charter → tipo: "crucero" o "barco"
- Si es un email informativo sin reserva confirmada → devolver []
- NUNCA devolver objetos con fecha_salida: null, fecha_embarque: null, o fecha: null
- Si no hay fecha, NO incluir el objeto

IMPORTANTE - CONSOLIDACIÓN DE ENTRADAS:
Para espectáculos/eventos con múltiples entradas/tickets del MISMO evento (misma fecha, mismo venue):
- Crear UN SOLO objeto con el total de entradas
- Incluir array "detalles_entradas" con información de cada entrada individual
- NO crear objetos separados por cada ticket

Ejemplo CORRECTO para 4 entradas del mismo evento:
{{
  "tipo": "espectaculo",
  "evento": "Venere e Adone",
  "venue": "Teatro La Fenice Venezia",
  "fecha": "2026-06-28",
  "hora": "17:00",
  "sector": "Palco 23",
  "entradas": 4,
  "detalles_entradas": [
    {{"puesto": 1, "ubicacion": "Palco centrale-parapetto", "precio": "€209,00"}},
    {{"puesto": 2, "ubicacion": "Palco centrale-parapetto", "precio": "€209,00"}},
    {{"puesto": 3, "ubicacion": "Palco centrale-dietro", "precio": "€165,00"}},
    {{"puesto": 4, "ubicacion": "Palco centrale-dietro", "precio": "€165,00"}}
  ],
  "precio_total": "€748,00"
}}

Ejemplo INCORRECTO (NO hacer esto):
[
  {{"tipo": "espectaculo", "evento": "Venere e Adone", "entradas": 1, ...}},
  {{"tipo": "espectaculo", "evento": "Venere e Adone", "entradas": 1, ...}},
  {{"tipo": "espectaculo", "evento": "Venere e Adone", "entradas": 1, ...}},
  {{"tipo": "espectaculo", "evento": "Venere e Adone", "entradas": 1, ...}}
]

Email/PDF:
{email_text}

Devuelve un ARRAY JSON con todas las reservas encontradas:

PARA VUELOS:
[{{
  "tipo": "vuelo",
  "descripcion": "Buenos Aires a Panama",
  "origen": "EZE",
  "destino": "PTY",
  "fecha_salida": "2026-07-21",
  "hora_salida": "02:27",
  "fecha_llegada": "2026-07-21",
  "hora_llegada": "07:39",
  "aerolinea": "Copa Airlines",
  "numero_vuelo": "CM168",
  "codigo_reserva": "AEOQD4",
  "codigo_aerolinea": "XYZ123",
  "pasajeros": [{{"nombre": "APELLIDO/NOMBRE", "asiento": "01A", "cabina": "Economy", "viajero_frecuente": null}}],
  "equipaje_facturado": "2x32kg",
  "equipaje_mano": "1x10kg",
  "terminal": null,
  "puerta": null
}}]

NOTA IMPORTANTE SOBRE CÓDIGOS DE RESERVA:
- "codigo_reserva" es el código principal/general (PNR, ej: AEOQD4)
- "codigo_aerolinea" es el código propietario de la aerolínea si existe (ej: confirmación de GOL, American, etc.)
- Extraer AMBOS si aparecen en el email. El codigo_reserva es obligatorio, codigo_aerolinea solo si existe.

PARA HOTELES/AIRBNB:
[{{
  "tipo": "hotel",
  "descripcion": "Hotel Marriott Buenos Aires",
  "nombre_propiedad": "Marriott Plaza Hotel",
  "direccion": "Florida 1005, CABA",
  "fecha_checkin": "2026-07-21",
  "hora_checkin": "15:00",
  "fecha_checkout": "2026-07-24",
  "hora_checkout": "11:00",
  "noches": 3,
  "habitacion": "Deluxe King",
  "huespedes": ["Andres Gamberg", "Veronica Gerszkowicz"],
  "codigo_reserva": "12345678",
  "precio_total": "USD 450",
  "incluye_desayuno": true,
  "notas": "Late checkout confirmado"
}}]

PARA RENTAL DE AUTOS:
[{{
  "tipo": "auto",
  "descripcion": "Hertz - Toyota Corolla",
  "empresa": "Hertz",
  "categoria": "Compact",
  "modelo": "Toyota Corolla o similar",
  "fecha_retiro": "2026-07-21",
  "hora_retiro": "10:00",
  "lugar_retiro": "Aeropuerto EZE",
  "fecha_devolucion": "2026-07-25",
  "hora_devolucion": "10:00",
  "lugar_devolucion": "Aeropuerto EZE",
  "codigo_reserva": "H123456",
  "precio_total": "USD 200",
  "incluye_seguro": true,
  "kilometraje": "Ilimitado"
}}]

PARA RESTAURANTES:
[{{
  "tipo": "restaurante",
  "descripcion": "Don Julio - Cena",
  "nombre": "Don Julio",
  "direccion": "Guatemala 4699, Palermo",
  "fecha": "2026-07-22",
  "hora": "21:00",
  "comensales": 4,
  "codigo_reserva": "DJ789",
  "notas": "Mesa exterior solicitada"
}}]

PARA ACTIVIDADES/TOURS:
[{{
  "tipo": "actividad",
  "descripcion": "Tour Cataratas del Iguazú",
  "nombre": "Cataratas lado argentino",
  "proveedor": "Civitatis",
  "fecha": "2026-07-23",
  "hora": "08:00",
  "duracion": "8 horas",
  "punto_encuentro": "Hotel pickup",
  "participantes": 2,
  "codigo_reserva": "CIV123",
  "precio_total": "USD 150",
  "incluye": "Transporte, guía, entradas"
}}]

PARA CRUCEROS/FERRIES:
[{{
  "tipo": "crucero",
  "descripcion": "MSC Seashore - Caribe",
  "embarcacion": "MSC Seashore",
  "compania": "MSC Cruceros",
  "puerto_embarque": "Miami",
  "fecha_embarque": "2026-07-21",
  "puerto_desembarque": "Miami",
  "fecha_desembarque": "2026-07-28",
  "camarote": "Balcón 12045",
  "pasajeros": ["Andres Gamberg", "Veronica Gerszkowicz"],
  "codigo_reserva": "MSC789",
  "itinerario": ["Miami", "Cozumel", "Roatan", "Belize"]
}}]

PARA TRENES:
[{{
  "tipo": "tren",
  "descripcion": "Eurostar Paris-London",
  "operador": "Eurostar",
  "numero_tren": "ES9012",
  "origen": "Paris Gare du Nord",
  "destino": "London St Pancras",
  "fecha_salida": "2026-07-21",
  "hora_salida": "10:30",
  "fecha_llegada": "2026-07-21",
  "hora_llegada": "11:50",
  "clase": "Standard Premier",
  "asientos": ["Coach 5 Seat 42"],
  "pasajeros": ["Andres Gamberg"],
  "codigo_reserva": "EUR456"
}}]

PARA BUSES:
[{{
  "tipo": "bus",
  "descripcion": "Buquebus Bus - Montevideo a Punta del Este",
  "empresa": "Buquebus",
  "servicio": "Ejecutivo",
  "origen": "Montevideo",
  "destino": "Punta del Este",
  "fecha_salida": "2025-12-27",
  "hora_salida": "10:15",
  "fecha_llegada": "2025-12-27",
  "hora_llegada": "12:45",
  "pasajeros": [{{"nombre": "MARTIN GAMBERG"}}, {{"nombre": "LARA TANUS SALOME"}}],
  "codigo_reserva": "B2501493584"
}}]

PARA ESPECTÁCULOS:
[{{
  "tipo": "espectaculo",
  "descripcion": "Coldplay - River Plate",
  "evento": "Coldplay Music of the Spheres Tour",
  "venue": "Estadio River Plate",
  "fecha": "2026-11-15",
  "hora": "21:00",
  "sector": "Campo VIP",
  "entradas": 2,
  "codigo_reserva": "TM789456",
  "notas": "Puerta 7"
}}]

PARA TRANSFERS:
[{{
  "tipo": "transfer",
  "descripcion": "Transfer EZE - Hotel",
  "empresa": "TravelSafe",
  "desde": "Aeropuerto EZE",
  "hasta": "Hotel Marriott",
  "fecha": "2026-07-21",
  "hora": "09:00",
  "pasajeros": 2,
  "vehiculo": "Sedan",
  "codigo_reserva": "TS123",
  "contacto": "+54 11 4567-8900"
}}]

Si el email no contiene ninguna reserva identificable, devuelve: []

IMPORTANTE: Devuelve SOLO el array JSON, sin markdown ni explicaciones."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        texto = message.content[0].text.strip()
        if '```' in texto:
            texto = texto.split('```')[1].replace('json','').strip()

        print("=" * 80)
        print("📝 JSON RECIBIDO DE CLAUDE:")
        print(texto)
        print("=" * 80)
        reservas = json.loads(texto)

        # Validar años extraídos (solo corregir años claramente erróneos)
        # RESPETAR años entre 2020-2030 (viajes históricos o futuros cercanos)
        for reserva in reservas:
            for campo in ['fecha_salida', 'fecha_llegada', 'fecha_checkin', 'fecha_checkout',
                          'fecha_retiro', 'fecha_devolucion', 'fecha', 'fecha_embarque', 'fecha_desembarque']:
                fecha_valor = reserva.get(campo, '')
                if fecha_valor and len(fecha_valor) >= 4:
                    try:
                        year_extracted = int(fecha_valor[:4])

                        # Rango válido: 2020-2030 (viajes históricos o futuros cercanos)
                        # Si está en este rango, RESPETAR el año del documento
                        if 2020 <= year_extracted <= 2030:
                            # Año válido, no corregir - respetar lo que dice el documento
                            pass
                        else:
                            # Año claramente erróneo (ej: 2049, 1999, 2019), corregir a target_year
                            reserva[campo] = str(target_year) + fecha_valor[4:]
                            print(f"  ⚠️ Año corregido (fuera de rango 2020-2030): {year_extracted} → {target_year}")

                    except (ValueError, IndexError):
                        pass

        print(f"✓ Extraídas {len(reservas)} reservas")
        return reservas

    except Exception as e:
        print(f"❌ Error en Claude: {e}")
        logging.error(f"Error: {e}")
        return None
