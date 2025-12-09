"""
Extracción de información de vuelos con Claude API - Mi Agente Viajes
"""
import os
import json
import re
import logging
from datetime import datetime
import anthropic


def extraer_info_con_claude(email_text):
    """Extrae información de TODOS los vuelos del email/PDF"""
    
    # Inicializar cliente Anthropic
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
        future_years = [int(y) for y in years if int(y) >= current_year]
        if future_years:
            target_year = min(future_years)
    
    prompt = f"""Analiza este email/PDF de confirmacion de viaje (puede estar en español, inglés, portugués, italiano, francés o cualquier idioma).

IMPORTANTE:
- Extrae TODOS los vuelos (ida, vuelta, conexiones)
- Para cada vuelo: TODOS los pasajeros con asientos
- Franquicia de equipaje
- Códigos IATA en MAYÚSCULAS (EZE, GRU, PTY, BZE, FCO, CDG, etc)
- Fechas en formato YYYY-MM-DD
- Horas en formato HH:MM (24h)

Email/PDF:
{email_text}

Devuelve un ARRAY JSON con todos los vuelos:
[
  {{
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
    "pasajeros": [
      {{"nombre": "GAMBERG/ANDRES GUILLERMO", "asiento": "01A", "cabina": "Economy", "viajero_frecuente": "LATAM Pass 123456789"}},
      {{"nombre": "GERSZKOWICZ/VERONICA BEATRIZ", "asiento": "01B", "cabina": "Business", "viajero_frecuente": null}}
    ],
    "equipaje_facturado": "2x32kg (70lbs) por adulto",
    "equipaje_mano": "1x10kg (22lbs) por adulto",
    "terminal": null,
    "puerta": null,
    "notas": "Conexion a Belize"
  }}
]

NOTA: Para cada pasajero incluir "cabina" (Economy/Premium Economy/Business/First o null) y "viajero_frecuente" como "Programa Número" (ej: "LATAM Pass 123456789") o null.

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
        
        logging.info("=" * 80)
        logging.info("📝 JSON RECIBIDO DE CLAUDE:")
        logging.info(texto)
        logging.info("=" * 80)
        vuelos = json.loads(texto)
        
        # Corregir años si es necesario
        for vuelo in vuelos:
            if vuelo.get('fecha_salida', '').startswith(('2020','2021','2022','2023','2024')):
                vuelo['fecha_salida'] = vuelo['fecha_salida'].replace(vuelo['fecha_salida'][:4], str(target_year))
        
        logging.info(f"✓ Extraidos {len(vuelos)} vuelos")
        return vuelos
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return None
