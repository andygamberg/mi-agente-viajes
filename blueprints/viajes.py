"""
Blueprint de Viajes - Mi Agente Viajes
Rutas: /, /agregar, /carga-rapida, /eliminar, /agrupar, /perfil, etc.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from datetime import datetime
import json
import uuid

from models import db, Viaje, User, UserEmail
from utils.iata import get_ciudad_nombre
from utils.claude import extraer_info_con_claude
from utils.helpers import calcular_ciudad_principal, normalize_name, get_viajes_for_user

viajes_bp = Blueprint('viajes', __name__)


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
    
    # ONBOARDING: Mostrar si nombre_pax vacío Y tiene 0 viajes
    show_onboarding = (not current_user.nombre_pax) and (len(viajes) == 0)
    
    # Badge de perfil incompleto (mostrar si nombre_pax vacío)
    profile_incomplete = not current_user.nombre_pax
    
    return render_template('index.html', 
                           proximos=proximos, 
                           pasados=pasados,
                           show_onboarding=show_onboarding,
                           profile_incomplete=profile_incomplete)


@viajes_bp.route('/agregar', methods=['GET', 'POST'])
@login_required
def agregar():
    if request.method == 'POST':
        try:
            fecha_salida_str = request.form.get('fecha_salida')
            if not fecha_salida_str:
                return "Error: Falta fecha de salida", 400
            
            hora_salida = request.form.get('hora_salida', '')
            
            if hora_salida:
                fecha_salida = datetime.strptime(f"{fecha_salida_str} {hora_salida}", '%Y-%m-%d %H:%M')
            else:
                fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
            
            fecha_llegada = None
            fecha_llegada_str = request.form.get('fecha_llegada')
            hora_llegada = request.form.get('hora_llegada', '')
            if fecha_llegada_str:
                if hora_llegada:
                    fecha_llegada = datetime.strptime(f"{fecha_llegada_str} {hora_llegada}", '%Y-%m-%d %H:%M')
                else:
                    fecha_llegada = datetime.strptime(fecha_llegada_str, '%Y-%m-%d')
            
            nuevo_viaje = Viaje(
                user_id=current_user.id,
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
            
            db.session.add(nuevo_viaje)
            db.session.commit()
            
            return redirect(url_for('viajes.index'))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    return render_template('agregar.html')


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
            
            for vuelo_data in vuelos:
                # Parsear fechas
                fecha_salida_str = vuelo_data.get('fecha_salida')
                hora_salida = vuelo_data.get('hora_salida', '')
                
                if not fecha_salida_str:
                    continue
                
                if hora_salida:
                    fecha_salida = datetime.strptime(f"{fecha_salida_str} {hora_salida}", '%Y-%m-%d %H:%M')
                else:
                    fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
                
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
                
                # Convertir pasajeros a JSON
                pasajeros_json = json.dumps(vuelo_data.get('pasajeros', []))
                
                # Crear viaje
                nuevo_viaje = Viaje(
                    user_id=current_user.id,
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
            
            # Asignar nombre automático
            vuelos_del_grupo = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
            if vuelos_del_grupo:
                vuelos_ordenados = sorted(vuelos_del_grupo, key=lambda x: x.fecha_salida)
                ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
                ciudad_nombre = get_ciudad_nombre(ciudad_principal)
                nombre_auto = f"Viaje a {ciudad_nombre}"
                for v in vuelos_del_grupo:
                    v.nombre_viaje = nombre_auto
            
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
                
                nuevo_viaje = Viaje(
                    user_id=current_user.id,
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
            
            index += 1
        
        # Asignar nombre automático
        vuelos_del_grupo = Viaje.query.filter_by(grupo_viaje=grupo_id).all()
        if vuelos_del_grupo:
            vuelos_ordenados = sorted(vuelos_del_grupo, key=lambda x: x.fecha_salida)
            ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
            ciudad_nombre = get_ciudad_nombre(ciudad_principal)
            nombre_auto = f"Viaje a {ciudad_nombre}"
            for v in vuelos_del_grupo:
                v.nombre_viaje = nombre_auto
        
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
        vuelos_ordenados = sorted(todos_vuelos, key=lambda x: x.fecha_salida)
        ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
        ciudad_nombre = get_ciudad_nombre(ciudad_principal)
        nombre_auto = f"Viaje a {ciudad_nombre}"
        for v in todos_vuelos:
            v.grupo_viaje = nuevo_grupo
            v.nombre_viaje = nombre_auto
    
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
            vuelos_ordenados = sorted(vuelos_reserva, key=lambda x: x.fecha_salida)
            ciudad_principal = calcular_ciudad_principal(vuelos_ordenados)
            ciudad_nombre = get_ciudad_nombre(ciudad_principal)
            nombre_auto = f"Viaje a {ciudad_nombre}"
            
            for viaje in vuelos_reserva:
                viaje.grupo_viaje = nuevo_grupo
                viaje.nombre_viaje = nombre_auto
        
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

@viajes_bp.route('/perfil')
@login_required
def perfil():
    emails_adicionales = UserEmail.query.filter_by(user_id=current_user.id).all()
    return render_template('perfil.html', emails_adicionales=emails_adicionales)


@viajes_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    current_user.nombre = request.form.get('nombre', '').strip()
    current_user.nombre_pax = request.form.get('nombre_pax', '').strip() or None
    current_user.apellido_pax = request.form.get('apellido_pax', '').strip() or None
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
