/**
 * Mobile Debug Console - Mi Agente Viajes
 *
 * Muestra logs en pantalla para debugging sin herramientas desktop
 */

(function() {
    'use strict';

    // Solo activar si estamos en PWA
    const isPWA = window.matchMedia('(display-mode: standalone)').matches ||
                  window.navigator.standalone === true;

    if (!isPWA) {
        return;
    }

    // Crear contenedor de debug
    const debugContainer = document.createElement('div');
    debugContainer.id = 'mobile-debug-console';
    debugContainer.style.cssText = `
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        max-height: 200px;
        overflow-y: auto;
        background: rgba(0, 0, 0, 0.9);
        color: #0f0;
        font-family: monospace;
        font-size: 11px;
        padding: 8px;
        z-index: 999999;
        display: none;
        border-top: 2px solid #0f0;
    `;

    // Botón toggle
    const toggleBtn = document.createElement('button');
    toggleBtn.textContent = '🐛';
    toggleBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #000;
        color: #0f0;
        border: 2px solid #0f0;
        font-size: 24px;
        z-index: 9999999;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,255,0,0.3);
    `;

    let isVisible = false;
    toggleBtn.onclick = () => {
        isVisible = !isVisible;
        debugContainer.style.display = isVisible ? 'block' : 'none';
        toggleBtn.textContent = isVisible ? '✖️' : '🐛';
    };

    document.addEventListener('DOMContentLoaded', () => {
        document.body.appendChild(debugContainer);
        document.body.appendChild(toggleBtn);
    });

    // Interceptar console.log
    const originalLog = console.log;
    console.log = function(...args) {
        originalLog.apply(console, args);

        // Solo mostrar logs que empiezan con [PTR]
        const message = args.map(arg =>
            typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
        ).join(' ');

        if (message.includes('[PTR]') || message.includes('[Eruda]')) {
            const logEntry = document.createElement('div');
            logEntry.style.cssText = 'padding: 2px 0; border-bottom: 1px solid #333;';
            logEntry.textContent = new Date().toLocaleTimeString() + ' - ' + message;
            debugContainer.appendChild(logEntry);
            debugContainer.scrollTop = debugContainer.scrollHeight;
        }
    };

    console.log('[MobileDebug] Console initialized - tap 🐛 to view logs');
})();
