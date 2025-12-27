"""
Blueprint PWA - Mi Agente Viajes

Rutas:
- /offline - Página offline para PWA
- /sw.js - Service Worker (servido desde static pero con scope /)
"""

from flask import Blueprint, render_template, send_from_directory, current_app
import os

pwa_bp = Blueprint('pwa', __name__)


@pwa_bp.route('/offline')
def offline():
    """Página mostrada cuando no hay conexión."""
    return render_template('offline.html')


@pwa_bp.route('/sw.js')
def service_worker():
    """
    Servir Service Worker desde raíz para scope completo.

    El SW debe servirse desde / para tener scope sobre toda la app.
    Si se sirve desde /static/, el scope estaría limitado a /static/.
    """
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'sw.js',
        mimetype='application/javascript'
    )


@pwa_bp.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Servir apple-touch-icon desde raíz para compatibilidad iOS."""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'icons'),
        'apple-touch-icon.png',
        mimetype='image/png'
    )
