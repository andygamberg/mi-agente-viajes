"""
Blueprint de Viajes - Mi Agente Viajes
Rutas: /, /agregar, /carga-rapida, /eliminar, /agrupar, /perfil, etc.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from datetime import datetime
import json
import uuid

from models import db, Viaje, User, UserEmail, EmailConnection
from utils.iata import get_ciudad_nombre
from utils.claude import extraer_info_con_claude
from utils.helpers import calcular_ciudad_principal, normalize_name, get_viajes_for_user
from utils.save_reservation import save_reservation
from utils.schema_helpers import get_dato, get_titulo_card, get_subtitulo_card
from config.schemas import RESERVATION_SCHEMAS, get_schema

viajes_bp = Blueprint('viajes', __name__)


# ============================================
# MVP11: DEDUPLICACIÓN DE VUELOS
# ============================================

def deduplicar_vuelos_en_grupo(vuelos):
    """
    Combina reservas idénticas de cualquier tipo que tengan diferentes pasajeros/huéspedes.

    Retorna lista donde los duplicados tienen pasajeros combinados.
    No modifica la BD - solo agrega atributos temporales para renderizado.
    """
    if not vuelos or len(vuelos) <= 1:
        return vuelos

    def get_datetime_salida(v):
        """Combina fecha_salida con hora para ordenamiento preciso"""
        from datetime import datetime, time

        if not v.fecha_salida:
            return datetime.max

        datos = v.datos or {}
        hora_str = (datos.get('hora_salida') or datos.get('hora_embarque') or
                   datos.get('hora') or datos.get('hora_checkin') or
                   datos.get('hora_retiro'))

        if hora_str:
            try:
                parts = str(hora_str).replace('h', ':').split(':')
                hora = int(parts[0])
                minuto = int(parts[1]) if len(parts) > 1 else 0
                return datetime.combine(v.fecha_salida.date(), time(hora, minuto))
            except:
                pass

        return v.fecha_salida

    def get_dedup_key(v):
        """Genera clave de deduplicación según el tipo"""
        fecha = v.fecha_salida.date() if v.fecha_salida else None
        datos = v.datos or {}
        tipo = v.tipo or 'vuelo'

        if tipo == 'vuelo':
            return (tipo, v.numero_vuelo, fecha, v.origen, v.destino)

        elif tipo == 'bus':
            empresa = datos.get('empresa', '')
            return (tipo, empresa, fecha, v.origen, v.destino)

        elif tipo == 'tren':
            operador = datos.get('operador', '')
            return (tipo, operador, fecha, v.origen, v.destino)

        elif tipo == 'crucero':
            # Ferries cortos (<24h) sí deduplicar por ruta+fecha+hora
            if v.fecha_salida and v.fecha_llegada:
                duracion = v.fecha_llegada - v.fecha_salida
                if duracion.total_seconds() < 24 * 3600:
                    # Usar hora de embarque como parte de la clave (no embarcación que puede variar)
                    hora = datos.get('hora_embarque', '')
                    return ('ferry', fecha, hora, v.origen, v.destino)
            return (v.id,)  # Crucero largo - no deduplicar

        elif tipo == 'hotel':
            nombre = datos.get('nombre_propiedad', '')
            return (tipo, nombre, fecha)

        elif tipo == 'auto':
            empresa = datos.get('empresa', '')
            lugar = datos.get('lugar_retiro', '')
            return (tipo, empresa, lugar, fecha)

        elif tipo == 'restaurante':
            nombre = datos.get('nombre', '')
            return (tipo, nombre, fecha)

        elif tipo == 'espectaculo':
            evento = datos.get('evento', '')
            return (tipo, evento, fecha)

        elif tipo == 'actividad':
            nombre = datos.get('nombre', '')
            return (tipo, nombre, fecha)

        elif tipo == 'transfer':
            empresa = datos.get('empresa', '')
            return (tipo, empresa, fecha, v.origen, v.destino)

        else:
            return (v.id,)  # Tipo desconocido - no deduplicar

    def get_personas(v):
        """Extrae lista de personas de cualquier tipo de reserva"""
        datos = v.datos or {}

        # Campos que contienen personas según el tipo
        for campo in ['pasajeros', 'huespedes', 'participantes', 'comensales']:
            valor = datos.get(campo)
            if valor:
                if isinstance(valor, list):
                    return valor
                elif isinstance(valor, int):
                    # comensales puede ser int
                    return []

        # Fallback a columna legacy
        if v.pasajeros:
            try:
                return json.loads(v.pasajeros) if v.pasajeros else []
            except:
                pass

        return []

    # Agrupar por clave
    grupos = {}
    orden_original = []

    for vuelo in vuelos:
        key = get_dedup_key(vuelo)
        if key not in grupos:
            grupos[key] = []
            orden_original.append(key)
        grupos[key].append(vuelo)

    # Procesar cada grupo
    resultado = []
    for key in orden_original:
        items_iguales = grupos[key]

        if len(items_iguales) == 1:
            item = items_iguales[0]
            item._es_combinado = False
            resultado.append(item)
        else:
            # Combinar personas de todos los items iguales
            item_principal = items_iguales[0]
            personas_combinadas = []
            codigos_reserva = []

            for item in items_iguales:
                codigo = item.codigo_reserva or 'N/A'
                if codigo not in codigos_reserva:
                    codigos_reserva.append(codigo)

                personas = get_personas(item)
                for p in personas:
                    if isinstance(p, dict):
                        p_copy = p.copy()
                        p_copy['codigo_reserva'] = codigo
                        personas_combinadas.append(p_copy)
                    elif isinstance(p, str):
                        personas_combinadas.append({
                            'nombre': p,
                            'codigo_reserva': codigo
                        })

            # Ordenar para consistencia
            codigos_ordenados = sorted(codigos_reserva)
            reservas_ordenadas = sorted(items_iguales, key=lambda r: r.codigo_reserva or '')
            personas_ordenadas = sorted(personas_combinadas, key=lambda p: p.get('codigo_reserva', ''))

            # Agregar atributos temporales
            item_principal._pasajeros_combinados = personas_ordenadas
            item_principal._codigos_reserva = codigos_ordenados
            item_principal._reservas_combinadas = reservas_ordenadas
            item_principal._es_combinado = True
            resultado.append(item_principal)

    # Ordenar por fecha+hora
    resultado.sort(key=get_datetime_salida)
    return resultado


@viajes_bp.route('/')
@login_required
def index():
    # MVP7: Buscar viajes donde soy owner O pasajero
    viajes = get_viajes_for_user(current_user, Viaje, User)
    viajes = sorted(viajes, key=lambda v: v.fecha_salida)
    
    ahora = datetime.now()
    
    # Separar por futuro/pasado
    viajes_futuros = [v for v in viajes if v.fecha_salida >= ahora]
    viajes_pasados = [v for v in viajes if v.fecha_salida < ahora]
    
    # MVP11: Obtener preferencia de usuario
    combinar = getattr(current_user, 'combinar_vuelos', True)
    if combinar is None:
        combinar = True
    
    # Agrupar por grupo_viaje
    def agrupar_viajes(lista_viajes):
        grupos = {}
        for v in lista_viajes:
            grupo_id = v.grupo_viaje if v.grupo_viaje else f"solo_{v.id}"
            if grupo_id not in grupos:
                grupos[grupo_id] = []
            grupos[grupo_id].append(v)
        
        # Convertir a lista de grupos
        resultado = []
        for grupo_id, vuelos in grupos.items():
            vuelos_ordenados = sorted(vuelos, key=lambda x: x.fecha_salida)
            
            # MVP11: Si combinar_vuelos está ON, deduplicar dentro del grupo
            if combinar:
                vuelos_ordenados = deduplicar_vuelos_en_grupo(vuelos_ordenados)
            else:
                # Marcar todos como no combinados
                for v in vuelos_ordenados:
                    v._es_combinado = False
            
            resultado.append(vuelos_ordenados)
        
        return resultado
    
    proximos = agrupar_viajes(viajes_futuros)
    pasados = agrupar_viajes(viajes_pasados)
    pasados.reverse()
    
    # ONBOARDING: Mostrar si nombre_pax vacío Y tiene 0 viajes
    show_onboarding = (not current_user.nombre_pax) and (len(viajes) == 0)
    
    # Badge de perfil incompleto (mostrar si nombre_pax vacío)
    profile_incomplete = not current_user.nombre_pax
    
    # Pasar helpers al template
    return render_template('index.html',
                           proximos=proximos,
                           pasados=pasados,
                           show_onboarding=show_onboarding,
                           profile_incomplete=profile_incomplete,
                           get_dato=get_dato,
                           get_titulo_card=get_titulo_card,
                           get_subtitulo_card=get_subtitulo_card,
                           get_schema=get_schema)


@viajes_bp.route('/bienvenida')
@login_required
def bienvenida():
    """Pantalla de bienvenida post-registro"""
    return render_template('bienvenida.html')


@viajes_bp.route('/agregar', methods=['GET', 'POST'])
@login_required
def agregar():
    """MVP16: Agregar reserva con schemas dinámicos"""
    from config.schemas import get_schema, get_all_tipos

    # Tipo por defecto o desde query param
    tipo_actual = request.args.get('tipo', 'vuelo')
    schema = get_schema(tipo_actual)
    tipos_disponibles = get_all_tipos()

    if request.method == 'POST':
        try:
            nuevo_tipo = request.form.get('tipo', 'vuelo')
            datos = {}

            schema_post = get_schema(nuevo_tipo)
            for campo in schema_post['campos']:
                key = campo['key']

                if campo['type'] == 'list':
                    # Parsear campos de lista
                    items = []
                    idx = 0
                    while True:
                        item = {}
                        has_data = False
                        for subfield in campo.get('item_fields', []):
                            form_key = f"{key}[{idx}][{subfield}]"
                            value = request.form.get(form_key, '').strip()
                            if value:
                                has_data = True
                                item[subfield] = value
                        if not has_data:
                            break
                        if item:
                            items.append(item)
                        idx += 1
                    if items:
                        datos[key] = items
                else:
                    value = request.form.get(key, '').strip()
                    if value:
                        datos[key] = value

            # Agregar tipo
            datos['tipo'] = nuevo_tipo

            nuevo_viaje = save_reservation(
                user_id=current_user.id,
                datos_dict=datos,
                source='manual'
            )
            db.session.commit()
            flash("✓ Reserva agregada", "success")
            return redirect(url_for('viajes.index'))

        except ValueError as e:
            flash(f"Error: {e}", "error")
        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f"Error: {str(e)}", "error")

    return render_template('agregar.html',
                         schema=schema,
                         datos={},
                         tipos_disponibles=tipos_disponibles,
                         tipo_actual=tipo_actual,
                         modo='crear')


@viajes_bp.route('/carga-rapida', methods=['GET', 'POST'])
@login_required
def carga_rapida():
    if request.method == 'POST':
        email_text = ''
        
        # Intentar leer PDF si se subió
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(pdf_file)
                    for page in reader.pages:
                        email_text += page.extract_text() + "\n"
                except Exception as e:
                    flash(f"Error leyendo PDF: {str(e)}", "error")
                    return render_template('carga_rapida.html')
        
        # Si no hay PDF, usar el texto pegado
        if not email_text.strip():
            email_text = request.form.get('email_text', '')
        
        if not email_text.strip():
            flash("Subí un PDF o pegá el email", "error")
            return render_template('carga_rapida.html')
        
        try:
            vuelos = extraer_info_con_claude(email_text)
            
            if not vuelos or len(vuelos) == 0:
                flash("No pude extraer vuelos del documento", "error")
                return render_template('carga_rapida.html')
            
            # Verificar duplicados por código de reserva
            primer_vuelo = vuelos[0]
            codigo = primer_vuelo.get('codigo_reserva')
            if codigo:
                duplicado = Viaje.query.filter_by(codigo_reserva=codigo).first()
                if duplicado:
                    flash(f'Este viaje ya existe (código {codigo})', 'error')
                    return redirect(url_for('viajes.index'))
            
            # Generar ID de grupo
            grupo_id = str(uuid.uuid4())[:8]
            vuelos_guardados = 0
            
            for reserva_data in vuelos:
                # Truncar codigo_reserva si es muy largo
                codigo = reserva_data.get('codigo_reserva', '')
                if codigo and len(codigo) > 250:
                    print(f"⚠️ Código reserva muy largo ({len(codigo)} chars), truncando")
                    reserva_data['codigo_reserva'] = codigo[:250]

                try:
                    nuevo_viaje = save_reservation(
                        user_id=current_user.id,
                        datos_dict=reserva_data,
                        grupo_id=grupo_id,
                        nombre_viaje=None,
                        source='pdf_upload'
                    )
                    vuelos_guardados += 1
                except ValueError as e:
                    flash(f"Error: {e}", "warning")
                    continue
            
            # Asignar nombre automático (solo si no existe uno custom)
            vuelos_del_grupo = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
            if vuelos_del_grupo:
                # Buscar si algún viaje ya tiene nombre_viaje editado manualmente
                nombre_existente = next((v.nombre_viaje for v in vuelos_del_grupo if v.nombre_viaje), None)

                if not nombre_existente:
                    # No hay nombre custom, generar uno automático
                    vuelos_ordenados = sorted(vuelos_del_grupo, key=lambda x: x.fecha_salida)
                    ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
                    ciudad_nombre = get_ciudad_nombre(ciudad_principal)
                    nombre_existente = f"Viaje a {ciudad_nombre}"

                # Aplicar el nombre (custom o auto) a todos los viajes del grupo
                for v in vuelos_del_grupo:
                    v.nombre_viaje = nombre_existente
            
            db.session.commit()
            flash(f"✓ {vuelos_guardados} vuelo(s) guardado(s)", "success")
            return redirect(url_for('viajes.index'))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            db.session.rollback()
            flash(f"Error procesando: {str(e)}", "error")
            return render_template('carga_rapida.html')
    
    return render_template('carga_rapida.html')


@viajes_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    viaje = Viaje.query.get_or_404(id)
    db.session.delete(viaje)
    db.session.commit()
    return redirect(url_for('viajes.index'))


@viajes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """MVP-EDIT: Editar reserva existente"""
    from config.schemas import get_all_tipos

    viaje = Viaje.query.get_or_404(id)

    # Verificar que el usuario puede editar este viaje
    if viaje.user_id != current_user.id:
        flash("No tenés permiso para editar esta reserva", "error")
        return redirect(url_for('viajes.index'))

    # Permitir cambiar tipo via query param (para preview de campos)
    tipo_actual = request.args.get('tipo', viaje.tipo or 'vuelo')
    schema = get_schema(tipo_actual)

    if request.method == 'POST':
        try:
            # Construir datos desde form
            nuevo_tipo = request.form.get('tipo', tipo_actual)
            nuevos_datos = {}

            schema_post = get_schema(nuevo_tipo)
            for campo in schema_post['campos']:
                key = campo['key']

                if campo['type'] == 'list':
                    # Parsear campos de lista (pasajeros, vehículos, etc.)
                    items = []
                    idx = 0
                    while True:
                        item = {}
                        has_data = False
                        for subfield in campo.get('item_fields', []):
                            form_key = f"{key}[{idx}][{subfield}]"
                            value = request.form.get(form_key, '').strip()
                            if value:
                                has_data = True
                                item[subfield] = value
                        if not has_data:
                            break
                        if item:
                            items.append(item)
                        idx += 1
                    if items:
                        nuevos_datos[key] = items
                else:
                    # Campo simple
                    value = request.form.get(key, '').strip()
                    if value:
                        nuevos_datos[key] = value

            # Actualizar viaje
            viaje.tipo = nuevo_tipo
            viaje.datos = nuevos_datos

            # Actualizar campos legacy para compatibilidad
            viaje.origen = nuevos_datos.get('origen', nuevos_datos.get('puerto_embarque', nuevos_datos.get('lugar_retiro', '')))
            viaje.destino = nuevos_datos.get('destino', nuevos_datos.get('puerto_desembarque', nuevos_datos.get('lugar_devolucion', '')))
            viaje.fecha_salida = None
            fecha_str = nuevos_datos.get('fecha_salida', nuevos_datos.get('fecha_embarque', nuevos_datos.get('fecha_checkin', nuevos_datos.get('fecha', ''))))
            if fecha_str:
                try:
                    viaje.fecha_salida = datetime.strptime(fecha_str, '%Y-%m-%d')
                except:
                    pass

            viaje.aerolinea = nuevos_datos.get('aerolinea', nuevos_datos.get('compania', nuevos_datos.get('empresa', '')))
            viaje.numero_vuelo = nuevos_datos.get('numero_vuelo', '')
            viaje.codigo_reserva = nuevos_datos.get('codigo_reserva', '')

            db.session.commit()
            flash("✓ Reserva actualizada", "success")
            return redirect(url_for('viajes.index'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            db.session.rollback()
            flash(f"Error al guardar: {str(e)}", "error")

    # GET: Preparar datos para template
    datos = viaje.datos or {}
    tipos_disponibles = get_all_tipos()

    return render_template('editar.html',
                         viaje=viaje,
                         schema=schema,
                         datos=datos,
                         tipos_disponibles=tipos_disponibles,
                         modo='editar')


@viajes_bp.route('/guardar-vuelos', methods=['POST'])
@login_required
def guardar_vuelos():
    """Guarda los vuelos seleccionados en la base de datos"""
    try:
        # Verificar duplicados
        primer_vuelo_data = None
        json_field = 'vuelo_json_0'
        if json_field in request.form:
            vuelo_json = request.form.get(json_field)
            if vuelo_json:
                try:
                    primer_vuelo_data = json.loads(vuelo_json)
                except:
                    pass
        
        if primer_vuelo_data:
            codigo = primer_vuelo_data.get('codigo_reserva')
            if codigo:
                duplicado = Viaje.query.filter_by(codigo_reserva=codigo).first()
                if duplicado:
                    flash(f'Este viaje ya existe (código {codigo})', 'error')
                    return redirect(url_for('viajes.carga_rapida'))
        
        # Generar ID único para este grupo
        grupo_id = str(uuid.uuid4())[:8]
        vuelos_guardados = 0
        
        # Iterar sobre todos los vuelos enviados
        index = 0
        while True:
            checkbox_name = f'vuelo_{index}'
            json_field = f'vuelo_json_{index}'
            
            if json_field not in request.form:
                break
            
            if checkbox_name in request.form:
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
                
                pasajeros_json = json.dumps(vuelo_data.get('pasajeros', []))

                # Detectar tipo y mapear campos
                tipo = vuelo_data.get('tipo', 'vuelo')
                proveedor = None
                ubicacion = None
                precio = vuelo_data.get('precio_total')

                if tipo == 'vuelo':
                    proveedor = vuelo_data.get('aerolinea')
                elif tipo == 'hotel':
                    proveedor = vuelo_data.get('nombre_propiedad')
                    ubicacion = vuelo_data.get('direccion')
                elif tipo == 'crucero':
                    proveedor = vuelo_data.get('compania') or vuelo_data.get('embarcacion')
                elif tipo == 'auto':
                    proveedor = vuelo_data.get('empresa')
                elif tipo == 'restaurante':
                    proveedor = vuelo_data.get('nombre')
                    ubicacion = vuelo_data.get('direccion')
                elif tipo == 'espectaculo':
                    proveedor = vuelo_data.get('evento')
                    ubicacion = vuelo_data.get('venue')
                elif tipo == 'actividad':
                    proveedor = vuelo_data.get('proveedor') or vuelo_data.get('nombre')
                    ubicacion = vuelo_data.get('punto_encuentro')
                elif tipo == 'tren':
                    proveedor = vuelo_data.get('operador')
                elif tipo == 'transfer':
                    proveedor = vuelo_data.get('empresa')

                nuevo_viaje = Viaje(
                    user_id=current_user.id,
                    tipo=tipo,
                    descripcion=vuelo_data.get('descripcion', ''),
                    origen=vuelo_data.get('origen', ''),
                    destino=vuelo_data.get('destino', ''),
                    grupo_viaje=grupo_id,
                    fecha_salida=fecha_salida,
                    fecha_llegada=fecha_llegada,
                    hora_salida=hora_salida,
                    hora_llegada=hora_llegada,
                    aerolinea=vuelo_data.get('aerolinea', '') if tipo == 'vuelo' else None,
                    numero_vuelo=vuelo_data.get('numero_vuelo', '') if tipo == 'vuelo' else None,
                    codigo_reserva=vuelo_data.get('codigo_reserva', ''),
                    terminal=vuelo_data.get('terminal', '') if tipo == 'vuelo' else None,
                    puerta=vuelo_data.get('puerta', '') if tipo == 'vuelo' else None,
                    asiento=vuelo_data.get('pasajeros', [{}])[0].get('asiento', '') if tipo == 'vuelo' and isinstance(vuelo_data.get('pasajeros'), list) and vuelo_data.get('pasajeros') else None,
                    pasajeros=pasajeros_json,
                    equipaje_facturado=vuelo_data.get('equipaje_facturado', '') if tipo == 'vuelo' else None,
                    equipaje_mano=vuelo_data.get('equipaje_mano', '') if tipo == 'vuelo' else None,
                    notas=vuelo_data.get('notas', ''),
                    # Nuevos campos multi-tipo
                    proveedor=proveedor,
                    ubicacion=ubicacion,
                    precio=precio,
                    raw_data=json.dumps(vuelo_data, ensure_ascii=False)
                )
                
                db.session.add(nuevo_viaje)
                vuelos_guardados += 1
            
            index += 1
        
        # Asignar nombre automático (solo si no existe uno custom)
        vuelos_del_grupo = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
        if vuelos_del_grupo:
            # Buscar si algún viaje ya tiene nombre_viaje editado manualmente
            nombre_existente = next((v.nombre_viaje for v in vuelos_del_grupo if v.nombre_viaje), None)

            if not nombre_existente:
                # No hay nombre custom, generar uno automático
                vuelos_ordenados = sorted(vuelos_del_grupo, key=lambda x: x.fecha_salida)
                ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
                ciudad_nombre = get_ciudad_nombre(ciudad_principal)
                nombre_existente = f"Viaje a {ciudad_nombre}"

            # Aplicar el nombre (custom o auto) a todos los viajes del grupo
            for v in vuelos_del_grupo:
                v.nombre_viaje = nombre_existente
        
        db.session.commit()
        return redirect(url_for('viajes.index'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return f"Error: {str(e)}", 500


@viajes_bp.route('/agrupar-manual', methods=['POST'])
@login_required
def agrupar_manual():
    grupos_ids = request.form.getlist('grupos_ids')
    if len(grupos_ids) < 2:
        return redirect(url_for('viajes.index'))
    
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
        # Buscar si alguno de los viajes que se están agrupando tiene nombre_viaje custom
        nombre_existente = next((v.nombre_viaje for v in todos_vuelos if v.nombre_viaje), None)

        if not nombre_existente:
            # No hay nombre custom, generar uno automático
            vuelos_ordenados = sorted(todos_vuelos, key=lambda x: x.fecha_salida)
            ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
            ciudad_nombre = get_ciudad_nombre(ciudad_principal)
            nombre_existente = f"Viaje a {ciudad_nombre}"

        # Aplicar grupo y nombre (custom o auto) a todos los viajes
        for v in todos_vuelos:
            v.grupo_viaje = nuevo_grupo
            v.nombre_viaje = nombre_existente
    
    db.session.commit()
    session['auto_update_calendar'] = nuevo_grupo
    
    return redirect(url_for('viajes.index'))


@viajes_bp.route('/editar-nombre-viaje', methods=['POST'])
@login_required
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
    
    return redirect(url_for('viajes.index'))


@viajes_bp.route('/desagrupar', methods=['POST'])
@login_required
def desagrupar():
    viaje_id = request.form.get('viaje_id')
    viaje = Viaje.query.get_or_404(int(viaje_id))
    viaje.grupo_viaje = None
    db.session.commit()
    return redirect(url_for('viajes.index'))


@viajes_bp.route('/eliminar-grupo', methods=['POST'])
@login_required
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
    return redirect(url_for('viajes.index'))


@viajes_bp.route('/desagrupar-grupo', methods=['POST'])
@login_required
def desagrupar_grupo():
    """Separa vuelos por código de reserva"""
    from collections import defaultdict
    
    grupo_id = request.form.get('grupo_id')
    
    if grupo_id and not grupo_id.startswith('solo_'):
        viajes = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
        
        # Agrupar por código de reserva
        por_reserva = defaultdict(list)
        for viaje in viajes:
            codigo = viaje.codigo_reserva or 'sin_codigo'
            por_reserva[codigo].append(viaje)
        
        if len(por_reserva) <= 1:
            db.session.commit()
            return redirect(url_for('viajes.index'))
        
        # Crear nuevo grupo para cada reserva
        for codigo, vuelos_reserva in por_reserva.items():
            nuevo_grupo = str(uuid.uuid4())[:8]

            # Buscar si algún viaje del subgrupo tiene nombre_viaje custom
            nombre_existente = next((v.nombre_viaje for v in vuelos_reserva if v.nombre_viaje), None)

            if not nombre_existente:
                # No hay nombre custom, generar uno automático
                vuelos_ordenados = sorted(vuelos_reserva, key=lambda x: x.fecha_salida)
                ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
                ciudad_nombre = get_ciudad_nombre(ciudad_principal)
                nombre_existente = f"Viaje a {ciudad_nombre}"

            for viaje in vuelos_reserva:
                viaje.grupo_viaje = nuevo_grupo
                viaje.nombre_viaje = nombre_existente
        
        db.session.commit()
    
    return redirect(url_for('viajes.index'))


@viajes_bp.route('/eliminar-multiples', methods=['POST'])
@login_required
def eliminar_multiples():
    """Elimina múltiples grupos/viajes de una vez"""
    grupos_ids = request.form.getlist('grupos_ids')
    
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
    return redirect(url_for('viajes.index'))


# ============================================
# PERFIL DE USUARIO
# ============================================

def detect_email_provider(email):
    """Detecta proveedor de email y disponibilidad de OAuth"""
    domain = email.split('@')[-1].lower()

    # Gmail
    if 'gmail.com' in domain or 'googlemail.com' in domain:
        return {
            'provider': 'gmail',
            'name': 'Gmail',
            'oauth_available': True,
            'oauth_implemented': True
        }

    # Outlook/Hotmail/Live
    elif any(d in domain for d in ['outlook.', 'hotmail.', 'live.', 'msn.']):
        return {
            'provider': 'microsoft',
            'name': 'Outlook',
            'oauth_available': True,
            'oauth_implemented': True  # MVP14h
        }

    # Yahoo
    elif 'yahoo.' in domain:
        return {
            'provider': 'yahoo',
            'name': 'Yahoo',
            'oauth_available': True,
            'oauth_implemented': False  # Próximamente
        }

    # iCloud
    elif 'icloud.com' in domain or 'me.com' in domain or 'mac.com' in domain:
        return {
            'provider': 'icloud',
            'name': 'iCloud',
            'oauth_available': True,
            'oauth_implemented': False  # Próximamente
        }

    # Otros proveedores no soportados
    else:
        return {
            'provider': 'other',
            'name': 'Otro',
            'oauth_available': True,
            'oauth_implemented': True
        }

@viajes_bp.route('/perfil')
@login_required
def perfil():
    """Perfil con lista unificada de emails"""
    emails_adicionales = UserEmail.query.filter_by(user_id=current_user.id).all()
    gmail_connections = EmailConnection.query.filter_by(
        user_id=current_user.id,
        provider='gmail',
        is_active=True
    ).all()
    microsoft_connections = EmailConnection.query.filter_by(
        user_id=current_user.id,
        provider='microsoft',
        is_active=True
    ).all()

    # Crear diccionarios de conexiones por email
    gmail_by_email = {conn.email: conn for conn in gmail_connections}
    microsoft_by_email = {conn.email: conn for conn in microsoft_connections}

    # Lista unificada de emails
    unified_emails = []
    seen_emails = set()

    # 1. Email principal
    principal = {
        'email': current_user.email,
        'is_principal': True,
        'gmail_connection': gmail_by_email.get(current_user.email),
        'microsoft_connection': microsoft_by_email.get(current_user.email),
        'user_email_id': None,
        'provider_info': detect_email_provider(current_user.email)
    }
    unified_emails.append(principal)
    seen_emails.add(current_user.email.lower())

    # 2. Gmail connections (que no sean el principal)
    for conn in gmail_connections:
        if conn.email.lower() not in seen_emails:
            unified_emails.append({
                'email': conn.email,
                'is_principal': False,
                'gmail_connection': conn,
                'microsoft_connection': None,
                'user_email_id': None,
                'provider_info': detect_email_provider(conn.email)
            })
            seen_emails.add(conn.email.lower())

    # 3. Microsoft connections (que no sean el principal ni Gmail)
    for conn in microsoft_connections:
        if conn.email.lower() not in seen_emails:
            unified_emails.append({
                'email': conn.email,
                'is_principal': False,
                'gmail_connection': None,
                'microsoft_connection': conn,
                'user_email_id': None,
                'provider_info': detect_email_provider(conn.email)
            })
            seen_emails.add(conn.email.lower())

    # 4. Emails adicionales (que no tengan conexión ni sean el principal)
    for ue in emails_adicionales:
        if ue.email.lower() not in seen_emails:
            unified_emails.append({
                'email': ue.email,
                'is_principal': False,
                'gmail_connection': gmail_by_email.get(ue.email),
                'microsoft_connection': microsoft_by_email.get(ue.email),
                'user_email_id': ue.id,
                'provider_info': detect_email_provider(ue.email)
            })
            seen_emails.add(ue.email.lower())

    # 5. Detectar alias corporativos (emails con mismo dominio que conexiones Microsoft)
    # Extraer dominios de conexiones Microsoft activas
    ms_domains = {}  # domain -> email conectado
    for conn in microsoft_connections:
        domain = conn.email.split('@')[1].lower() if '@' in conn.email else None
        if domain:
            ms_domains[domain] = conn.email

    # Para cada email, verificar si es alias de una conexión Microsoft
    for email_info in unified_emails:
        email = email_info['email']
        domain = email.split('@')[1].lower() if '@' in email else None

        # Si no tiene conexión Microsoft propia y su dominio está conectado
        if not email_info['microsoft_connection'] and domain and domain in ms_domains:
            email_info['connected_via'] = ms_domains[domain]
        else:
            email_info['connected_via'] = None

    return render_template('perfil.html',
                           unified_emails=unified_emails,
                           emails_adicionales=emails_adicionales,
                           gmail_connections=gmail_connections,
                           microsoft_connections=microsoft_connections)


@viajes_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    current_user.nombre = request.form.get('nombre', '').strip().title()
    current_user.nombre_pax = request.form.get('nombre_pax', '').strip().title() or None
    current_user.apellido_pax = request.form.get('apellido_pax', '').strip().title() or None
    # MVP11: Toggle combinar vuelos
    current_user.combinar_vuelos = request.form.get('combinar_vuelos') == 'on'
    db.session.commit()
    flash('Perfil actualizado', 'success')
    return redirect(url_for('viajes.perfil'))


@viajes_bp.route('/add-email', methods=['POST'])
@login_required
def add_email():
    email = request.form.get('email', '').strip().lower()
    if not email:
        flash('Email inválido', 'error')
        return redirect(url_for('viajes.perfil'))
    
    existe = UserEmail.query.filter_by(email=email).first()
    if existe:
        flash('Ese email ya está registrado', 'error')
        return redirect(url_for('viajes.perfil'))
    
    nuevo = UserEmail(user_id=current_user.id, email=email)
    db.session.add(nuevo)
    db.session.commit()
    flash(f'Email {email} agregado', 'success')
    return redirect(url_for('viajes.perfil'))


@viajes_bp.route('/remove-email/<int:email_id>', methods=['POST'])
@login_required
def remove_email(email_id):
    email = UserEmail.query.get(email_id)
    if email and email.user_id == current_user.id:
        db.session.delete(email)
        db.session.commit()
        flash('Email eliminado', 'success')
    return redirect(url_for('viajes.perfil'))


@viajes_bp.route('/preferencias')
@login_required
def preferencias():
    gmail_connections = EmailConnection.query.filter_by(
        user_id=current_user.id,
        provider='gmail',
        is_active=True
    ).all()
    return render_template('preferencias.html', gmail_connections=gmail_connections)


@viajes_bp.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    # Toggle maestro de notificaciones
    current_user.notif_email_master = request.form.get('notif_email_master') == 'on'

    # Sub-preferencias (solo si master está ON)
    if current_user.notif_email_master:
        current_user.notif_delay = request.form.get('notif_delay') == 'on'
        current_user.notif_cancelacion = request.form.get('notif_cancelacion') == 'on'
        current_user.notif_gate = request.form.get('notif_gate') == 'on'

    # Preferencia de visualización
    current_user.combinar_vuelos = request.form.get('combinar_vuelos') == 'on'

    db.session.commit()
    flash('Preferencias actualizadas', 'success')
    return redirect(url_for('viajes.preferencias'))


# ============================================
# MVP14e: Custom Senders (Remitentes de Confianza)
# ============================================

@viajes_bp.route('/add-sender', methods=['POST'])
@login_required
def add_sender():
    """Agrega un remitente a la whitelist personal"""
    sender = request.form.get('sender', '').strip().lower()
    
    if not sender:
        flash('Ingresá un email o dominio válido', 'error')
        return redirect(url_for('viajes.preferencias'))
    
    # Validar formato básico
    if '@' not in sender and not sender.startswith('@'):
        sender = '@' + sender
    
    if current_user.add_custom_sender(sender):
        db.session.commit()
        if sender.startswith('@'):
            flash(f'Dominio {sender} agregado. Ahora detectaremos emails de cualquier dirección de ese dominio.', 'success')
        else:
            flash(f'Remitente {sender} agregado', 'success')
    else:
        flash('Ese remitente ya está en tu lista', 'info')
    
    return redirect(url_for('viajes.preferencias'))


@viajes_bp.route('/remove-sender/<path:sender>', methods=['POST'])
@login_required
def remove_sender(sender):
    """Elimina un remitente de la whitelist personal"""
    if current_user.remove_custom_sender(sender):
        db.session.commit()
        flash(f'Remitente eliminado', 'success')
    return redirect(url_for('viajes.preferencias'))
