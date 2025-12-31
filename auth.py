"""
Autenticación - Mi Agente Viajes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from itsdangerous import URLSafeTimedSerializer

auth = Blueprint('auth', __name__)
login_manager = LoginManager()


def get_serializer():
    """Obtiene el serializer para tokens seguros"""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('viajes.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('¡Bienvenido!', 'success')
            return redirect(next_page or url_for('viajes.index'))
        else:
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('viajes.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        nombre = request.form.get('nombre', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        
        # Validaciones
        if not email or not nombre or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('register.html', nombre=nombre, email=email)

        if password != password2:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html', nombre=nombre, email=email)

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('register.html', nombre=nombre, email=email)

        if User.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con ese email', 'error')
            return render_template('register.html', nombre=nombre, email=email)
        
        # Crear usuario
        user = User(email=email, nombre=nombre)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=True)
        flash(f'¡Cuenta creada! Bienvenido {nombre}', 'success')
        return redirect(url_for('viajes.bienvenida'))
    
    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar recuperación de contraseña"""
    if current_user.is_authenticated:
        return redirect(url_for('viajes.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generar token
            s = get_serializer()
            token = s.dumps(email, salt='password-reset')
            
            # Enviar email
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_reset_email(email, reset_url)
        
        # Siempre mostrar mismo mensaje (seguridad)
        flash('Si el email existe, recibirás instrucciones para recuperar tu contraseña', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Restablecer contraseña con token"""
    if current_user.is_authenticated:
        return redirect(url_for('viajes.index'))
    
    # Verificar token (expira en 1 hora)
    s = get_serializer()
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)
    except:
        flash('El link es inválido o expiró', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        
        if not password or len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('reset_password.html', token=token)
        
        if password != password2:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('reset_password.html', token=token)
        
        # Actualizar contraseña
        user.set_password(password)
        db.session.commit()
        
        flash('¡Contraseña actualizada! Ya podés iniciar sesión', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)


def send_reset_email(to_email, reset_url):
    """Envía email de recuperación de contraseña"""
    from email_processor import send_email
    
    subject = 'Recuperar contraseña - Mis Viajes'
    
    body_html = f'''
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; background: #f5f5f7; border-radius: 12px; padding: 32px;">
            <h1 style="color: #1d1d1f; font-size: 24px; margin-bottom: 16px;">🌍 Mis Viajes</h1>
            <p style="color: #1d1d1f; font-size: 16px; line-height: 1.5;">
                Recibimos una solicitud para restablecer tu contraseña.
            </p>
            <p style="margin: 24px 0;">
                <a href="{reset_url}" 
                   style="background: #0071e3; color: white; padding: 12px 24px; 
                          border-radius: 8px; text-decoration: none; font-weight: 500;">
                    Restablecer Contraseña
                </a>
            </p>
            <p style="color: #6e6e73; font-size: 14px;">
                Este link expira en 1 hora.<br>
                Si no solicitaste esto, ignorá este email.
            </p>
        </div>
    </body>
    </html>
    '''
    
    send_email(to_email, subject, body_html)
