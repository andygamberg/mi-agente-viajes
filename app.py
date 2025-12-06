from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import anthropic
import os
from dotenv import load_dotenv
import json
from icalendar import Calendar, Event, Alarm
import pytz
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
import logging

load_dotenv()


# Mapeo de códigos IATA a ciudades
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


app = Flask(__name__)
app.secret_key = 'mi-agente-viajes-secret-2024'
# Configuración de base de datos (PostgreSQL en producción, SQLite en local)
if os.getenv('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///viajes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'
db = SQLAlchemy(app)

# Agregar filtro fromjson para Jinja2
@app.template_filter('fromjson')
def fromjson_filter(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []


# # try:
# #     client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
# #     ANTHROPIC_AVAILABLE = True
# # except:
# #     ANTHROPIC_AVAILABLE = False

class Viaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    origen = db.Column(db.String(100))
    destino = db.Column(db.String(100))
    fecha_salida = db.Column(db.DateTime, nullable=False)
    fecha_llegada = db.Column(db.DateTime)
    hora_salida = db.Column(db.String(10))
    hora_llegada = db.Column(db.String(10))
    aerolinea = db.Column(db.String(100))
    numero_vuelo = db.Column(db.String(50))
    codigo_reserva = db.Column(db.String(50))
    terminal = db.Column(db.String(50))
    puerta = db.Column(db.String(20))
    asiento = db.Column(db.String(20))
    nombre_hotel = db.Column(db.String(200))
    direccion_hotel = db.Column(db.String(300))
    notas = db.Column(db.Text)
    pasajeros = db.Column(db.Text)  # JSON con lista de pasajeros [{nombre, asiento}]
    equipaje_facturado = db.Column(db.String(200))  # ej: "2x32kg (70lbs)"
    equipaje_mano = db.Column(db.String(200))  # ej: "1x10kg (22lbs)"
    grupo_viaje = db.Column(db.String(50))  # ID para agrupar vuelos del mismo viaje
    nombre_viaje = db.Column(db.String(200))  # Nombre personalizado del viaje (editable)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    
    # Campos para monitoreo FR24
    ultima_actualizacion_fr24 = db.Column(db.DateTime)
    status_fr24 = db.Column(db.String(50))  # 'on_time', 'delayed', 'cancelled', 'landed', etc
    delay_minutos = db.Column(db.Integer)
    datetime_takeoff_actual = db.Column(db.DateTime)
    datetime_landed_actual = db.Column(db.DateTime)
def calcular_ciudad_principal(vuelos):
    """Calcula la ciudad donde se pasa más tiempo"""
    from datetime import datetime, timedelta
    
    if not vuelos:
        return None
    
    # Si es solo un vuelo, usar destino
    if len(vuelos) == 1:
        return vuelos[0].destino
    
    # Calcular tiempo en cada ciudad
    tiempo_por_ciudad = {}
    
    for i, vuelo in enumerate(vuelos):
        # Tiempo en ciudad destino
        if i < len(vuelos) - 1:  # No es el último vuelo
            proximo = vuelos[i + 1]
            
            # Si hay fecha/hora de llegada y próxima salida
            if vuelo.fecha_salida and proximo.fecha_salida:
                try:
                    # Usar fecha_salida como datetime (ya tiene hora)
                    llegada = vuelo.fecha_salida  # Esto es un datetime
                    salida_proxima = proximo.fecha_salida
                    
                    if isinstance(llegada, datetime) and isinstance(salida_proxima, datetime):
                        horas = (salida_proxima - llegada).total_seconds() / 3600
                        ciudad = vuelo.destino
                        
                        if ciudad not in tiempo_por_ciudad:
                            tiempo_por_ciudad[ciudad] = 0
                        tiempo_por_ciudad[ciudad] += horas
                except:
                    pass
    
    # Si no pudimos calcular, usar destino final
    if not tiempo_por_ciudad:
        return vuelos[-1].destino
    
    # Retornar ciudad con más horas
    return max(tiempo_por_ciudad, key=tiempo_por_ciudad.get)

@app.route('/')
def index():
    viajes = Viaje.query.order_by(Viaje.fecha_salida).all()
    ahora = datetime.now()
    
    # Separar por futuro/pasado
    viajes_futuros = [v for v in viajes if v.fecha_salida >= ahora]
    viajes_pasados = [v for v in viajes if v.fecha_salida < ahora]
    
    # Agrupar por grupo_viaje
    def agrupar_viajes(lista_viajes):
        grupos = {}
        for v in lista_viajes:
            grupo_id = v.grupo_viaje if v.grupo_viaje else f"solo_{v.id}"
            if grupo_id not in grupos:
                grupos[grupo_id] = []
            grupos[grupo_id].append(v)
        # Convertir a lista de grupos ordenados
        return [sorted(vuelos, key=lambda x: x.fecha_salida) for vuelos in grupos.values()]
    
    proximos = agrupar_viajes(viajes_futuros)
    pasados = agrupar_viajes(viajes_pasados)
    pasados.reverse()
    
    return render_template('index.html', proximos=proximos, pasados=pasados)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        try:
            print("=== DEBUG: Datos recibidos ===")
            print(f"Tipo: {request.form.get('tipo')}")
            print(f"Descripcion: {request.form.get('descripcion')}")
            print(f"Fecha salida: {request.form.get('fecha_salida')}")
            
            fecha_salida_str = request.form.get('fecha_salida')
            if not fecha_salida_str:
                print("ERROR: No hay fecha de salida")
                return "Error: Falta fecha de salida", 400
            
            hora_salida = request.form.get('hora_salida', '')
            
            if hora_salida:
                fecha_salida = datetime.strptime(f"{fecha_salida_str} {hora_salida}", '%Y-%m-%d %H:%M')
            else:
                fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
            
            print(f"Fecha parseada: {fecha_salida}")
            
            fecha_llegada = None
            fecha_llegada_str = request.form.get('fecha_llegada')
            hora_llegada = request.form.get('hora_llegada', '')
            if fecha_llegada_str:
                if hora_llegada:
                    fecha_llegada = datetime.strptime(f"{fecha_llegada_str} {hora_llegada}", '%Y-%m-%d %H:%M')
                else:
                    fecha_llegada = datetime.strptime(fecha_llegada_str, '%Y-%m-%d')
            
            nuevo_viaje = Viaje(
                tipo=request.form.get('tipo'),
                descripcion=request.form.get('descripcion'),
                origen=request.form.get('origen', ''),
                destino=request.form.get('destino', ''),
                fecha_salida=fecha_salida,
                fecha_llegada=fecha_llegada,
                hora_salida=hora_salida,
                hora_llegada=hora_llegada,
                aerolinea=request.form.get('aerolinea', ''),
                numero_vuelo=request.form.get('numero_vuelo', ''),
                codigo_reserva=request.form.get('codigo_reserva', ''),
                terminal=request.form.get('terminal', ''),
                puerta=request.form.get('puerta', ''),
                asiento=request.form.get('asiento', ''),
                nombre_hotel=request.form.get('nombre_hotel', ''),
                direccion_hotel=request.form.get('direccion_hotel', ''),
                notas=request.form.get('notas', '')
            )
            
            print(f"Viaje creado: {nuevo_viaje.descripcion}")
            db.session.add(nuevo_viaje)
            print("Viaje agregado a session")
            db.session.commit()
            print("Commit exitoso!")
            
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"ERROR AL GUARDAR: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    return render_template('agregar.html')

@app.route('/carga-rapida', methods=['GET', 'POST'])
def carga_rapida():
    if request.method == 'POST':
        email_text = ''
        
        # Intentar leer PDF si se subió
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                try:
                    reader = PdfReader(pdf_file)
                    for page in reader.pages:
                        email_text += page.extract_text() + "\n"
                    print(f"PDF leído, {len(email_text)} caracteres")
                except Exception as e:
                    print(f"Error leyendo PDF: {e}")
                    flash(f"Error leyendo PDF: {str(e)}", "error"); return render_template('carga_rapida.html')
        
        # Si no hay PDF, usar el texto pegado
        if not email_text.strip():
            email_text = request.form.get('email_text', '')
        
        if not email_text.strip():
            flash("Subi un PDF o pega el email", "error"); return render_template('carga_rapida.html')
        
        try:
            flash("🔍 Intentando procesar con Claude API...", "info")
            vuelos = extraer_info_con_claude(email_text)
            flash(f"📊 Resultado: {type(vuelos)} - {len(vuelos) if vuelos else 0} vuelos", "info")
            if vuelos and len(vuelos) > 0:
                # Mostrar lista de vuelos extraídos para que el usuario seleccione cuáles guardar
                return render_template('revisar_vuelos.html', vuelos=vuelos)
            else:
                flash("No pude extraer vuelos del documento", "error"); return render_template('carga_rapida.html')
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            flash(f"Error procesando: {str(e)}", "error"); return render_template('carga_rapida.html')
    
    return render_template('carga_rapida.html', anthropic_ok=True)

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
    
    import re
    from datetime import datetime, timedelta
    
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
        
        logging.error("=" * 80)
        logging.error("📝 JSON RECIBIDO DE CLAUDE:")
        logging.error(texto)
        logging.error("=" * 80)
        vuelos = json.loads(texto)
        
        # Corregir años si es necesario
        for vuelo in vuelos:
            if vuelo.get('fecha_salida', '').startswith(('2020','2021','2022','2023','2024')):
                vuelo['fecha_salida'] = vuelo['fecha_salida'].replace(vuelo['fecha_salida'][:4], str(target_year))
        
        logging.error(f"✓ Extraidos {len(vuelos)} vuelos")
        return vuelos
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return None


@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    viaje = Viaje.query.get_or_404(id)
    db.session.delete(viaje)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/guardar-vuelos', methods=['POST'])
def guardar_vuelos():
    """Guarda los vuelos seleccionados en la base de datos"""
    try:
        import uuid
        
        # Verificar si ya existe este grupo de vuelos (prevenir duplicados)
        # Obtenemos el primer vuelo para verificar (sin importar si está marcado)
        primer_vuelo_data = None
        json_field = 'vuelo_json_0'
        if json_field in request.form:
            vuelo_json = request.form.get(json_field)
            if vuelo_json:
                try:
                    primer_vuelo_data = json.loads(vuelo_json)
                except:
                    pass
        
        # Si encontramos data, verificar duplicados por código de reserva y fecha
        print(f"🔍 primer_vuelo_data: {primer_vuelo_data}")
        if primer_vuelo_data:
            codigo = primer_vuelo_data.get('codigo_reserva')
            fecha = primer_vuelo_data.get('fecha_salida')
            origen = primer_vuelo_data.get('origen')
            print(f"🔍 Validación 1 - Código: {codigo}, Fecha: {fecha}")
            
            if codigo:
                # Buscar vuelos con mismo código (único por reserva)
                duplicado = Viaje.query.filter_by(codigo_reserva=codigo).first()
                
                if duplicado:
                    print(f"⚠️ DUPLICADO ENCONTRADO: {codigo}")
                    from flask import flash
                    flash(f'Este viaje ya existe (código {codigo})', 'error')
                    return redirect(url_for('carga_rapida'))
                else:
                    print(f"✅ No hay duplicado, guardando {codigo}")
        
        # Generar un ID único para este grupo de vuelos
        grupo_id = str(uuid.uuid4())[:8]
        
        vuelos_guardados = 0
        
        # Iterar sobre todos los vuelos enviados
        index = 0
        while True:
            checkbox_name = f'vuelo_{index}'
            data_name = f'vuelo_data_{index}'
            
            # Si no existe este índice, terminamos
            json_field = f'vuelo_json_{index}'
            if json_field not in request.form:
                break
            
            # Si el checkbox está marcado, guardar
            if checkbox_name in request.form:
                json_field = f'vuelo_json_{index}'
                vuelo_json = request.form.get(json_field)
                if not vuelo_json:
                    index += 1
                    continue
                vuelo_data = json.loads(vuelo_json)
                
                # Parsear fechas
                fecha_salida_str = vuelo_data.get('fecha_salida')
                hora_salida = vuelo_data.get('hora_salida', '')
                
                if fecha_salida_str:
                    if hora_salida:
                        fecha_salida = datetime.strptime(f"{fecha_salida_str} {hora_salida}", '%Y-%m-%d %H:%M')
                    else:
                        fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
                else:
                    index += 1
                    continue
                
                fecha_llegada = None
                fecha_llegada_str = vuelo_data.get('fecha_llegada')
                hora_llegada = vuelo_data.get('hora_llegada', '')
                if fecha_llegada_str:
                    try:
                        if hora_llegada:
                            fecha_llegada = datetime.strptime(f"{fecha_llegada_str} {hora_llegada}", '%Y-%m-%d %H:%M')
                        else:
                            fecha_llegada = datetime.strptime(fecha_llegada_str, '%Y-%m-%d')
                    except:
                        pass
                
                # Convertir lista de pasajeros a JSON string
                pasajeros_json = json.dumps(vuelo_data.get('pasajeros', []))
                
                # VALIDAR DUPLICADO antes de crear
                codigo = vuelo_data.get('codigo_reserva')
                fecha_str = vuelo_data.get('fecha_salida')
                print(f"🔍 Validación 2 - Index: {index}, Código: {codigo}, Fecha: {fecha_str}")
                

                
                # Crear nuevo viaje
                nuevo_viaje = Viaje(
                    tipo='vuelo',
                    descripcion=vuelo_data.get('descripcion', ''),
                    origen=vuelo_data.get('origen', ''),
                    destino=vuelo_data.get('destino', ''),
                    grupo_viaje=grupo_id,
                    fecha_salida=fecha_salida,
                    fecha_llegada=fecha_llegada,
                    hora_salida=hora_salida,
                    hora_llegada=hora_llegada,
                    aerolinea=vuelo_data.get('aerolinea', ''),
                    numero_vuelo=vuelo_data.get('numero_vuelo', ''),
                    codigo_reserva=vuelo_data.get('codigo_reserva', ''),
                    terminal=vuelo_data.get('terminal', ''),
                    puerta=vuelo_data.get('puerta', ''),
                    asiento=vuelo_data.get('pasajeros', [{}])[0].get('asiento', '') if vuelo_data.get('pasajeros') else '',
                    pasajeros=pasajeros_json,
                    equipaje_facturado=vuelo_data.get('equipaje_facturado', ''),
                    equipaje_mano=vuelo_data.get('equipaje_mano', ''),
                    notas=vuelo_data.get('notas', '')
                )
                
                db.session.add(nuevo_viaje)
                vuelos_guardados += 1
                print(f"✓ Vuelo guardado: {vuelo_data.get('numero_vuelo')} {vuelo_data.get('origen')}->{vuelo_data.get('destino')}")
            
            index += 1
        
        # Asignar nombre automático a todos los vuelos del grupo
        vuelos_del_grupo = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
        if vuelos_del_grupo:
            vuelos_ordenados = sorted(vuelos_del_grupo, key=lambda x: x.fecha_salida)
            ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
            ciudad_nombre = get_ciudad_nombre(ciudad_principal)
            nombre_auto = f"Viaje a {ciudad_nombre}"
            for v in vuelos_del_grupo:
                v.nombre_viaje = nombre_auto
        
        db.session.commit()
        print(f"✅ Total guardados: {vuelos_guardados} vuelos")
        
        # Auto-descargar calendario
        from flask import session
        
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Error guardando vuelos: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return f"Error: {str(e)}", 500




@app.route('/agrupar-manual', methods=['POST'])
def agrupar_manual():
    import uuid
    grupos_ids = request.form.getlist('grupos_ids')
    if len(grupos_ids) < 2:
        return redirect(url_for('index'))
    nuevo_grupo = str(uuid.uuid4())[:8]
    todos_vuelos = []
    for grupo_id in grupos_ids:
        if grupo_id.startswith('solo_'):
            viaje_id = int(grupo_id.replace('solo_', ''))
            viaje = Viaje.query.get(viaje_id)
            if viaje:
                todos_vuelos.append(viaje)
        else:
            viajes = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
            todos_vuelos.extend(viajes)
    if todos_vuelos:
        vuelos_ordenados = sorted(todos_vuelos, key=lambda x: x.fecha_salida)
        ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
        ciudad_nombre = get_ciudad_nombre(ciudad_principal)
        nombre_auto = f"Viaje a {ciudad_nombre}"
        for v in todos_vuelos:
            v.grupo_viaje = nuevo_grupo
            v.nombre_viaje = nombre_auto
    db.session.commit()
    
    # Auto-descargar UPDATE
    session['auto_update_calendar'] = grupo_id
    
    return redirect(url_for('index'))

@app.route('/editar-nombre-viaje', methods=['POST'])
def editar_nombre_viaje():
    grupo_id = request.form.get('grupo_id')
    nuevo_nombre = request.form.get('nombre')
    if grupo_id and nuevo_nombre:
        if grupo_id.startswith('solo_'):
            viaje_id = int(grupo_id.replace('solo_', ''))
            viaje = Viaje.query.get(viaje_id)
            if viaje:
                viaje.nombre_viaje = nuevo_nombre
        else:
            viajes = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
            for viaje in viajes:
                viaje.nombre_viaje = nuevo_nombre
        db.session.commit()
    # No UPDATE - nombre no afecta calendario
    return redirect(url_for('index'))

@app.route('/desagrupar', methods=['POST'])
def desagrupar():
    viaje_id = request.form.get('viaje_id')
    viaje = Viaje.query.get_or_404(int(viaje_id))
    viaje.grupo_viaje = None
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/eliminar-grupo', methods=['POST'])
def eliminar_grupo():
    """Elimina todos los vuelos de un grupo"""
    grupo_id = request.form.get('grupo_id')
    
    if grupo_id.startswith('solo_'):
        viaje_id = int(grupo_id.replace('solo_', ''))
        viaje = Viaje.query.get_or_404(viaje_id)
        db.session.delete(viaje)
    else:
        viajes = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
        for viaje in viajes:
            db.session.delete(viaje)
    
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/desagrupar-grupo', methods=['POST'])
def desagrupar_grupo():
    """Separa vuelos por código de reserva (los de misma reserva quedan juntos)"""
    import uuid
    from collections import defaultdict
    
    grupo_id = request.form.get('grupo_id')
    
    if grupo_id and not grupo_id.startswith('solo_'):
        viajes = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
        
        # Agrupar por código de reserva
        por_reserva = defaultdict(list)
        for viaje in viajes:
            codigo = viaje.codigo_reserva or 'sin_codigo'
            por_reserva[codigo].append(viaje)
        
        # Si solo hay una reserva, no hacer nada
        if len(por_reserva) <= 1:
            db.session.commit()
            return redirect(url_for('index'))
        
        # Crear un nuevo grupo para cada reserva
        for codigo, vuelos_reserva in por_reserva.items():
            nuevo_grupo = str(uuid.uuid4())[:8]
            vuelos_ordenados = sorted(vuelos_reserva, key=lambda x: x.fecha_salida)
            ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
            ciudad_nombre = get_ciudad_nombre(ciudad_principal)
            nombre_auto = f"Viaje a {ciudad_nombre}"
            
            for viaje in vuelos_reserva:
                viaje.grupo_viaje = nuevo_grupo
                viaje.nombre_viaje = nombre_auto
        
        db.session.commit()
    
    return redirect(url_for('index'))


@app.route('/eliminar-multiples', methods=['POST'])
def eliminar_multiples():
    """Elimina múltiples grupos/viajes de una vez"""
    grupos_ids = request.form.getlist('grupos_ids')
    
    # SEGUNDO: Ahora sí eliminar de BD
    for grupo_id in grupos_ids:
        if grupo_id.startswith('solo_'):
            viaje_id = int(grupo_id.replace('solo_', ''))
            viaje = Viaje.query.get(viaje_id)
            if viaje:
                db.session.delete(viaje)
        else:
            viajes = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
            for viaje in viajes:
                db.session.delete(viaje)
    
    db.session.commit()
    return redirect(url_for('index'))



@app.route('/update-calendar/<grupo_id>')
def update_calendar(grupo_id):
    """Genera .ics UPDATE para sincronizar cambios"""
    if grupo_id.startswith('solo_'):
        viaje_id = int(grupo_id.replace('solo_', ''))
        vuelos = [Viaje.query.get(viaje_id)]
    else:
        vuelos = Viaje.query.filter_by(grupo_viaje=grupo_id).order_by(Viaje.fecha_salida, Viaje.hora_salida).all()
    
    if not vuelos:
        return "Viaje no encontrado", 404
    
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'UPDATE')  # iTIP: actualización
    
    for vuelo in vuelos:
        event = Event()
        event.add('summary', f"{vuelo.numero_vuelo}: {vuelo.origen} → {vuelo.destino}")
        event.add('uid', f'vuelo-{vuelo.id}@miagenteviajes.local')
        event.add('sequence', 1)  # Incrementar para indicar cambio
        event.add('status', 'CONFIRMED')
        
        # Mismo contenido que export_calendar (descripción, fechas, etc)
        desc = [f"Vuelo {vuelo.numero_vuelo} - {vuelo.aerolinea}"]
        if vuelo.codigo_reserva:
            desc.append(f"\nCódigo: {vuelo.codigo_reserva}")
        if vuelo.pasajeros:
            try:
                pasajeros = json.loads(vuelo.pasajeros)
                if pasajeros:
                    desc.append("\nPasajeros:")
                    for p in pasajeros:
                        pax = f"• {p.get('nombre', '')}"
                        if p.get('asiento'):
                            pax += f" - Asiento {p['asiento']}"
                        if p.get('cabina'):
                            pax += f" ({p['cabina']})"
                        desc.append(pax)
            except:
                pass
        desc.append(f"\nSalida: {vuelo.origen} a las {vuelo.hora_salida} (hora local)")
        desc.append(f"Llegada: {vuelo.destino} a las {vuelo.hora_llegada} (hora local)")
        if vuelo.terminal:
            if ' a ' in vuelo.terminal.lower():
                parts = vuelo.terminal.split(' a ')
                desc.append(f"Terminal salida: {parts[0].strip()}")
                if len(parts) > 1:
                    desc.append(f"Terminal llegada: {parts[1].strip()}")
            else:
                desc.append(f"Terminal salida: {vuelo.terminal}")
        if vuelo.puerta:
            desc.append(f"Puerta: {vuelo.puerta}")
        event.add('description', '\n'.join(desc))
        
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        dtstart = datetime.combine(vuelo.fecha_salida, datetime.strptime(vuelo.hora_salida, '%H:%M').time())
        dtend = datetime.combine(vuelo.fecha_llegada, datetime.strptime(vuelo.hora_llegada, '%H:%M').time())
        event.add('dtstart', tz.localize(dtstart))
        event.add('dtend', tz.localize(dtend))
        event.add('location', f'{vuelo.origen} Airport')
        event.add('dtstamp', datetime.now(pytz.UTC))
        
        cal.add_component(event)
    
    from flask import make_response
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    nombre = (vuelos[0].nombre_viaje or 'viaje').replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre}_update.ics"'
    return response

@app.route('/cancel-calendar/<grupo_id>')
def cancel_calendar(grupo_id):
    """Genera .ics CANCEL para eliminar de calendario"""
    if grupo_id.startswith('solo_'):
        viaje_id = int(grupo_id.replace('solo_', ''))
        vuelos = [Viaje.query.get(viaje_id)]
    else:
        vuelos = Viaje.query.filter_by(grupo_viaje=grupo_id).order_by(Viaje.fecha_salida, Viaje.hora_salida).all()
    
    if not vuelos:
        return "Viaje no encontrado", 404
    
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'CANCEL')
    
    for vuelo in vuelos:
        event = Event()
        
        # Mismo título que al crear
        event.add('summary', f"{vuelo.numero_vuelo}: {vuelo.origen} → {vuelo.destino}")
        
        # UID IDÉNTICO al original
        event.add('uid', f'vuelo-{vuelo.id}@miagenteviajes.local')
        
        # CRITICAL para iTIP CANCEL
        event.add('dtstamp', datetime.now(pytz.UTC))
        event.add('status', 'CANCELLED')
        event.add('sequence', 10)  # Número alto para forzar cancelación
        
        # Fechas originales (requeridas)
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        dtstart = datetime.combine(vuelo.fecha_salida, datetime.strptime(vuelo.hora_salida, '%H:%M').time())
        dtend = datetime.combine(vuelo.fecha_llegada, datetime.strptime(vuelo.hora_llegada, '%H:%M').time())
        
        event.add('dtstart', tz.localize(dtstart))
        event.add('dtend', tz.localize(dtend))
        
        # Organizer y Attendee (requerido para iTIP)
        event.add('organizer', 'mailto:viajes@miagenteviajes.local')
        event.add('attendee', 'mailto:viajes@miagenteviajes.local')
        
        cal.add_component(event)
    
    from flask import make_response
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    nombre = (vuelos[0].nombre_viaje or 'viaje').replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre}_cancel.ics"'
    return response

@app.route('/export-calendar/<grupo_id>')
def export_calendar(grupo_id):
    """Exporta viaje a .ics con iTIP"""
    if grupo_id.startswith('solo_'):
        viaje_id = int(grupo_id.replace('solo_', ''))
        vuelos = [Viaje.query.get(viaje_id)]
    else:
        vuelos = Viaje.query.filter_by(grupo_viaje=grupo_id).order_by(Viaje.fecha_salida, Viaje.hora_salida).all()
    
    if not vuelos:
        return "Viaje no encontrado", 404
    
    # Crear calendario con iTIP
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')  # iTIP: es una invitación
    cal.add('x-wr-calname', 'Mis Viajes')
    
    for vuelo in vuelos:
        event = Event()
        
        # Título LIMPIO: solo número + ruta
        titulo = f"{vuelo.numero_vuelo}: {vuelo.origen} → {vuelo.destino}"
        event.add('summary', titulo)
        
        # Descripción con TODO
        desc = [f"Vuelo {vuelo.numero_vuelo} - {vuelo.aerolinea}"]
        
        if vuelo.codigo_reserva:
            desc.append(f"\nCódigo: {vuelo.codigo_reserva}")
        
        # PASAJEROS
        if vuelo.pasajeros:
            try:
                pasajeros = json.loads(vuelo.pasajeros)
                if pasajeros:
                    desc.append("\nPasajeros:")
                    for p in pasajeros:
                        pax = f"• {p.get('nombre', '')}"
                        if p.get('asiento'):
                            pax += f" - Asiento {p['asiento']}"
                        if p.get('cabina'):
                            pax += f" ({p['cabina']})"
                        desc.append(pax)
            except:
                pass
        
        # HORARIOS LOCALES explícitos
        desc.append(f"\nSalida: {vuelo.origen} a las {vuelo.hora_salida} (hora local)")
        desc.append(f"Llegada: {vuelo.destino} a las {vuelo.hora_llegada} (hora local)")
        
        # Terminal - separar si tiene origen y destino
        if vuelo.terminal:
            if ' a ' in vuelo.terminal.lower():
                # Formato: "TERMINAL 1 a TERMINAL 2"
                parts = vuelo.terminal.split(' a ')
                desc.append(f"Terminal salida: {parts[0].strip()}")
                if len(parts) > 1:
                    desc.append(f"Terminal llegada: {parts[1].strip()}")
            else:
                desc.append(f"Terminal salida: {vuelo.terminal}")
        
        if vuelo.puerta:
            desc.append(f"Puerta: {vuelo.puerta}")
        
        event.add('description', '\n'.join(desc))
        
        # Fechas
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        dtstart = datetime.combine(vuelo.fecha_salida, datetime.strptime(vuelo.hora_salida, '%H:%M').time())
        dtend = datetime.combine(vuelo.fecha_llegada, datetime.strptime(vuelo.hora_llegada, '%H:%M').time())
        
        event.add('dtstart', tz.localize(dtstart))
        event.add('dtend', tz.localize(dtend))
        event.add('location', f'{vuelo.origen} Airport')
        
        # UID único y estable para iTIP
        event.add('uid', f'vuelo-{vuelo.id}@miagenteviajes.local')
        event.add('dtstamp', datetime.now(pytz.UTC))
        event.add('sequence', 0)
        
        # CRITICAL para iTIP: organizer y attendee
        event.add('organizer', 'mailto:viajes@miagenteviajes.local')
        event.add('attendee', 'mailto:viajes@miagenteviajes.local')
        
        # Alarmas
        alarm = Alarm()
        alarm.add('trigger', timedelta(hours=-24))
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'Mañana: {titulo}')
        event.add_component(alarm)
        
        cal.add_component(event)
    
    from flask import make_response
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    nombre = (vuelos[0].nombre_viaje or 'viaje').replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre}.ics"'
    return response


@app.route('/calendar-feed')
def calendar_feed():
    """
    Webcal feed - genera .ics dinámico con TODOS los viajes futuros
    Calendar.app consulta esta URL automáticamente
    """
    from datetime import date
    
    # Obtener TODOS los viajes futuros
    hoy = date.today()
    viajes_futuros = Viaje.query.filter(Viaje.fecha_salida >= hoy).order_by(Viaje.fecha_salida, Viaje.hora_salida).all()
    
    # Crear calendario
    cal = Calendar()
    cal.add('prodid', '-//Mi Agente Viajes//')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')  # PUBLISH para feeds (no REQUEST)
    cal.add('x-wr-calname', 'Mis Viajes')
    cal.add('x-wr-timezone', 'America/Argentina/Buenos_Aires')
    cal.add('x-wr-caldesc', 'Calendario sincronizado de Mi Agente Viajes')
    
    # Agrupar viajes por grupo_viaje
    grupos = {}
    for viaje in viajes_futuros:
        grupo_id = viaje.grupo_viaje or f'solo_{viaje.id}'
        if grupo_id not in grupos:
            grupos[grupo_id] = []
        grupos[grupo_id].append(viaje)
    
    # Crear eventos
    for grupo_id, vuelos in grupos.items():
        for vuelo in vuelos:
            event = Event()
            
            # Título limpio
            titulo = f"{vuelo.numero_vuelo}: {vuelo.origen} → {vuelo.destino}"
            event.add('summary', titulo)
            
            # Descripción completa
            desc = [f"Vuelo {vuelo.numero_vuelo} - {vuelo.aerolinea}"]
            
            if vuelo.codigo_reserva:
                desc.append(f"\nCódigo: {vuelo.codigo_reserva}")
            
            # Pasajeros
            if vuelo.pasajeros:
                try:
                    pasajeros = json.loads(vuelo.pasajeros)
                    if pasajeros:
                        desc.append("\nPasajeros:")
                        for p in pasajeros:
                            pax = f"• {p.get('nombre', '')}"
                            if p.get('asiento'):
                                pax += f" - Asiento {p['asiento']}"
                            if p.get('cabina'):
                                pax += f" ({p['cabina']})"
                            desc.append(pax)
                except:
                    pass
            
            # Horarios locales
            desc.append(f"\nSalida: {vuelo.origen} a las {vuelo.hora_salida} (hora local)")
            desc.append(f"Llegada: {vuelo.destino} a las {vuelo.hora_llegada} (hora local)")
            
            # Terminal
            if vuelo.terminal:
                if ' a ' in vuelo.terminal.lower():
                    parts = vuelo.terminal.split(' a ')
                    desc.append(f"Terminal salida: {parts[0].strip()}")
                    if len(parts) > 1:
                        desc.append(f"Terminal llegada: {parts[1].strip()}")
                else:
                    desc.append(f"Terminal salida: {vuelo.terminal}")
            
            if vuelo.puerta:
                desc.append(f"Puerta: {vuelo.puerta}")
            
            event.add('description', '\n'.join(desc))
            
            # Fechas
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            dtstart = datetime.combine(vuelo.fecha_salida, datetime.strptime(vuelo.hora_salida, '%H:%M').time())
            dtend = datetime.combine(vuelo.fecha_llegada, datetime.strptime(vuelo.hora_llegada, '%H:%M').time())
            
            event.add('dtstart', tz.localize(dtstart))
            event.add('dtend', tz.localize(dtend))
            event.add('location', f'{vuelo.origen} Airport')
            
            # UID único y estable
            event.add('uid', f'vuelo-{vuelo.id}@miagenteviajes.local')
            event.add('dtstamp', datetime.now(pytz.UTC))
            
            # Alarmas
            alarm = Alarm()
            alarm.add('trigger', timedelta(hours=-24))
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f'Mañana: {titulo}')
            event.add_component(alarm)
            
            cal.add_component(event)
    
    # Response con headers correctos para webcal
    from flask import make_response
    response = make_response(cal.to_ical())
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    response.headers['Content-Disposition'] = 'inline; filename="calendar.ics"'
    
    # CRITICAL para que Calendar.app lo trate como feed
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


# MVP 4: FLIGHT MONITORING
# ============================================

from flight_monitor import check_flight_status, check_all_upcoming_flights

@app.route('/api/check-flights', methods=['GET'])
def api_check_flights():
    """
    Endpoint para chequear estado de vuelos próximos
    Returns JSON con cambios detectados
    """
    try:
        cambios = check_all_upcoming_flights(db.session)
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'vuelos_chequeados': len(cambios),
            'cambios': cambios
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }, 500


@app.route('/check-flights-manual')
def check_flights_manual():
    """
    Página para chequear vuelos manualmente (para testing)
    """
    try:
        cambios = check_all_upcoming_flights(db.session)
        
        return render_template('check_flights.html', 
                             cambios=cambios,
                             timestamp=datetime.now())
    except Exception as e:
        flash(f'Error chequeando vuelos: {str(e)}', 'error')
        return redirect(url_for('index'))


# MVP5: Email Automation
@app.route('/cron/process-emails', methods=['GET', 'POST'])
def process_emails_cron():
    """Procesa emails de misviajes@gamberg.com.ar"""
    from email_processor import fetch_unread_emails
    
    try:
        emails = fetch_unread_emails()
        if not emails:
            return {'success': True, 'message': 'No hay emails nuevos'}, 200
        
        vuelos_creados = 0
        for email in emails:
            vuelos = extraer_info_con_claude(email['body'])
            if not vuelos:
                continue
            
            for v in vuelos:
                existe = Viaje.query.filter_by(
                    numero_vuelo=v.get('numero_vuelo'),
                    fecha_salida=v.get('fecha_salida')
                ).first()
                
                if not existe:
                    viaje = Viaje(
                        tipo='vuelo',
                        descripcion=f"{v.get('origen')} → {v.get('destino')}",
                        origen=v.get('origen'),
                        destino=v.get('destino'),
                        fecha_salida=v.get('fecha_salida'),
                        hora_salida=v.get('hora_salida'),
                        aerolinea=v.get('aerolinea'),
                        numero_vuelo=v.get('numero_vuelo')
                    )
                    db.session.add(viaje)
                    vuelos_creados += 1
            
            db.session.commit()
        
        return {'success': True, 'vuelos_creados': vuelos_creados}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

# API endpoint para Cloud Function
@app.route("/api/process-email-text", methods=["POST"])
def api_process_email_text():
    try:
        data = request.get_json()
        email_text = data.get("email_text", "")
        if not email_text:
            return {"success": False, "error": "No email text provided"}, 400
        
        vuelos = extraer_info_con_claude(email_text)
        if not vuelos:
            return {"success": True, "vuelos_creados": 0}, 200
        
        vuelos_creados = 0
        for vuelo_data in vuelos:
            viaje = Viaje(
                tipo="vuelo",
                descripcion=f"{vuelo_data.get("origen")} → {vuelo_data.get("destino")}",
                origen=vuelo_data.get("origen"),
                destino=vuelo_data.get("destino"),
                fecha_salida=vuelo_data.get("fecha_salida"),
                hora_salida=vuelo_data.get("hora_salida"),
                aerolinea=vuelo_data.get("aerolinea"),
                numero_vuelo=vuelo_data.get("numero_vuelo")
            )
            db.session.add(viaje)
            vuelos_creados += 1
        
        db.session.commit()
        return {"success": True, "vuelos_creados": vuelos_creados}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
# Force rebuild Fri Dec  5 14:24:00 UTC 2025
