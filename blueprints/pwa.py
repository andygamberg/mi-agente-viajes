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


@pwa_bp.route('/firebase-messaging-sw.js')
def firebase_messaging_sw():
    """Servir Firebase Messaging Service Worker desde raíz."""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'firebase-messaging-sw.js',
        mimetype='application/javascript'
    )


@pwa_bp.route('/force-update')
def force_update():
    """
    Página especial que desregistra el Service Worker y limpia todo el cache.
    Usar cuando el SW está corrupto o no se actualiza.
    """
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forzar Actualización - Mi Agente Viajes</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 24px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            font-size: 2rem;
            margin-bottom: 16px;
            color: #1D1D1F;
        }
        .status {
            font-size: 1.125rem;
            color: #666;
            margin-bottom: 24px;
            min-height: 60px;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #E5E5E7;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 24px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .success {
            color: #34C759;
            font-size: 4rem;
            margin-bottom: 16px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 12px;
            font-size: 1.125rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .log {
            background: #F5F5F7;
            border-radius: 12px;
            padding: 16px;
            margin-top: 24px;
            font-family: monospace;
            font-size: 0.9rem;
            text-align: left;
            max-height: 200px;
            overflow-y: auto;
            color: #1D1D1F;
        }
        .log div {
            margin-bottom: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 Actualización Forzada</h1>
        <div class="spinner" id="spinner"></div>
        <div class="status" id="status">Limpiando cache...</div>
        <div class="log" id="log"></div>
        <button id="homeBtn" style="display: none;" onclick="window.location.href='/'">
            Volver a Inicio
        </button>
    </div>

    <script>
        const log = (msg) => {
            console.log(msg);
            const logEl = document.getElementById('log');
            const entry = document.createElement('div');
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
            logEl.appendChild(entry);
            logEl.scrollTop = logEl.scrollHeight;
        };

        const updateStatus = (msg) => {
            document.getElementById('status').textContent = msg;
        };

        const showSuccess = () => {
            document.getElementById('spinner').style.display = 'none';
            document.getElementById('status').innerHTML = '<div class="success">✓</div>Actualización completa';
            document.getElementById('homeBtn').style.display = 'inline-block';
        };

        async function forceUpdate() {
            try {
                log('Iniciando actualización forzada...');

                // 1. Desregistrar Service Workers
                if ('serviceWorker' in navigator) {
                    updateStatus('Desregistrando Service Workers...');
                    const registrations = await navigator.serviceWorker.getRegistrations();
                    log(`Encontrados ${registrations.length} Service Workers`);

                    for (const registration of registrations) {
                        await registration.unregister();
                        log(`✓ SW desregistrado: ${registration.scope}`);
                    }
                }

                // 2. Limpiar todos los caches
                updateStatus('Limpiando caches...');
                if ('caches' in window) {
                    const cacheNames = await caches.keys();
                    log(`Encontrados ${cacheNames.length} caches`);

                    for (const name of cacheNames) {
                        await caches.delete(name);
                        log(`✓ Cache eliminado: ${name}`);
                    }
                }

                // 3. Limpiar localStorage y sessionStorage
                updateStatus('Limpiando storage...');
                try {
                    localStorage.clear();
                    sessionStorage.clear();
                    log('✓ LocalStorage y SessionStorage limpiados');
                } catch (e) {
                    log('⚠️ No se pudo limpiar storage: ' + e.message);
                }

                // 4. Limpiar IndexedDB (offline storage)
                updateStatus('Limpiando bases de datos...');
                if ('indexedDB' in window) {
                    try {
                        await indexedDB.deleteDatabase('offline-viajes-db');
                        log('✓ IndexedDB eliminada');
                    } catch (e) {
                        log('⚠️ No se pudo eliminar IndexedDB: ' + e.message);
                    }
                }

                updateStatus('Esperando 2 segundos...');
                await new Promise(resolve => setTimeout(resolve, 2000));

                log('✓ Limpieza completa');
                showSuccess();

            } catch (error) {
                log('❌ Error: ' + error.message);
                updateStatus('Error en la actualización');
                document.getElementById('spinner').style.display = 'none';
                document.getElementById('homeBtn').style.display = 'inline-block';
            }
        }

        // Ejecutar automáticamente al cargar
        forceUpdate();
    </script>
</body>
</html>
    """
