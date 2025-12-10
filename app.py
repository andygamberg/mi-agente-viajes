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

# ============================================
# EXTENSIONS
# ============================================

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor iniciá sesión para acceder'

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

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
