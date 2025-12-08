"""
Autenticación - Mi Agente Viajes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os

auth = Blueprint('auth', __name__)
login_manager = LoginManager()

# Serializer para tokens de reset
def get_serializer():
    secret_key = os.getenv('SECRET_KEY', 'mi-agente-viajes-secret-2024')
    return URLSafeTimedSerializer(secret_key)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('¡Bienvenido!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        nombre = request.form.get('nombre', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        
        # Validaciones
        if not email or not nombre or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('register.html')
        
        if password != password2:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con ese email', 'error')
            return render_template('register.html')
        
        # Crear usuario
        user = User(email=email, nombre=nombre)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'¡Cuenta creada! Bienvenido {nombre}', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        # Siempre mostrar mensaje de éxito (seguridad: no revelar si email existe)
        if user:
            # Generar token
            s = get_serializer()
            token = s.dumps(email, salt='password-reset')
            
            # Enviar email
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_reset_email(user.email, user.nombre, reset_url)
        
        flash('Si el email existe, recibirás instrucciones para recuperar tu contraseña', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Verificar token
    s = get_serializer()
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)  # 1 hora
    except SignatureExpired:
        flash('El link expiró. Solicitá uno nuevo.', 'error')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash('Link inválido', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        
        if password != password2:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('reset_password.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('reset_password.html')
        
        # Actualizar contraseña
        user.set_password(password)
        db.session.commit()
        
        flash('¡Contraseña actualizada! Ya podés iniciar sesión', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html')


def send_reset_email(to_email, nombre, reset_url):
    """Envía email de recuperación de contraseña usando Gmail API"""
    try:
        import json
        import base64
        from email.mime.text import MIMEText
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        DELEGATED_EMAIL = 'misviajes@gamberg.com.ar'
        
        # Credenciales
        creds_json = os.getenv("GMAIL_CREDENTIALS")
        if creds_json:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            credentials = service_account.Credentials.from_service_account_file("gmail-credentials.json", scopes=SCOPES)
        
        delegated_credentials = credentials.with_subject(DELEGATED_EMAIL)
        service = build("gmail", "v1", credentials=delegated_credentials)
        
        # Crear mensaje
        message = MIMEText(f"""Hola {nombre},

Recibimos una solicitud para recuperar tu contraseña de Mis Viajes.

Hacé click en este link para crear una nueva contraseña:
{reset_url}

El link expira en 1 hora.

Si no solicitaste este cambio, podés ignorar este email.

Saludos,
Mis Viajes
""")
        message['to'] = to_email
        message['from'] = DELEGATED_EMAIL
        message['subject'] = '🔑 Recuperar contraseña - Mis Viajes'
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        
        print(f'✅ Email de reset enviado a {to_email}')
        
    except Exception as e:
        print(f'❌ Error enviando email de reset: {e}')
        import traceback
        traceback.print_exc()
