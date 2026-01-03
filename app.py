"""
Mi Agente Viajes - App principal
Refactored: Config + Blueprints
"""
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os

from models import db, User
from auth import auth, login_manager

# Blueprints
from blueprints.viajes import viajes_bp
from blueprints.calendario import calendario_bp
from blueprints.api import api_bp
from blueprints.gmail_oauth import gmail_oauth_bp  # MVP14
from blueprints.gmail_webhook import gmail_webhook_bp  # MVP14c
from blueprints.microsoft_oauth import microsoft_oauth_bp  # MVP14h
from blueprints.pwa import pwa_bp  # PWA
from blueprints.push import push_bp  # Push Notifications
from blueprints.shared import shared_bp  # MVP-SHARE

load_dotenv()

# ============================================
# APP FACTORY
# ============================================

app = Flask(__name__)

# Config
app.secret_key = os.getenv('SECRET_KEY', 'mi-agente-viajes-secret-2024')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mi-agente-viajes-secret-2024')

# Database
if os.getenv('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///viajes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session config - mantener logueado 1 año (como apps nativas)
from datetime import timedelta
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=365)
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# ============================================
# EXTENSIONS
# ============================================

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor iniciá sesión para acceder'

# Crear tablas faltantes (no afecta existentes)
with app.app_context():
    db.create_all()

# ============================================
# TEMPLATE FILTERS
# ============================================

import json

@app.template_filter('fromjson')
def fromjson_filter(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

# ============================================
# BLUEPRINTS
# ============================================

app.register_blueprint(auth)
app.register_blueprint(viajes_bp)
app.register_blueprint(calendario_bp)
app.register_blueprint(api_bp)
app.register_blueprint(gmail_oauth_bp)  # MVP14
app.register_blueprint(gmail_webhook_bp)  # MVP14c
app.register_blueprint(microsoft_oauth_bp)  # MVP14h
app.register_blueprint(pwa_bp)  # PWA
app.register_blueprint(push_bp)  # Push Notifications
app.register_blueprint(shared_bp)  # MVP-SHARE

# ============================================
# JINJA GLOBALS - Schema Helpers
# ============================================

# Registrar helpers de schema en Jinja globals
from utils.schema_helpers import get_dato, get_titulo_card, get_subtitulo_card
from config.schemas import RESERVATION_SCHEMAS, get_schema
from utils.permissions import puede_modificar_segmento

app.jinja_env.globals['get_dato'] = get_dato
app.jinja_env.globals['get_titulo_card'] = get_titulo_card
app.jinja_env.globals['get_subtitulo_card'] = get_subtitulo_card
app.jinja_env.globals['get_schema'] = get_schema
app.jinja_env.globals['RESERVATION_SCHEMAS'] = RESERVATION_SCHEMAS
app.jinja_env.globals['puede_modificar_segmento'] = puede_modificar_segmento

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
