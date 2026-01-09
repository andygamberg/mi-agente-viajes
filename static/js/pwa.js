/**
 * PWA Registration - Mi Agente Viajes
 * 
 * Funcionalidades:
 * - Registro del Service Worker
 * - Detección de actualizaciones
 * - Prompt de instalación
 * - Detección online/offline
 */

(function() {
    'use strict';

    // ============================================
    // SERVICE WORKER REGISTRATION
    // ============================================
    
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', async () => {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });
                
                console.log('[PWA] Service Worker registered:', registration.scope);
                
                // Verificar actualizaciones
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('[PWA] New Service Worker installing...');
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showUpdateNotification();
                        }
                    });
                });
                
                // Verificar actualizaciones periódicamente (cada hora)
                setInterval(() => {
                    registration.update();
                }, 60 * 60 * 1000);
                
            } catch (error) {
                console.error('[PWA] Service Worker registration failed:', error);
            }
        });
        
        // Recargar cuando el nuevo SW tome control
        let refreshing = false;
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            if (!refreshing) {
                refreshing = true;
                window.location.reload();
            }
        });
    }

    // ============================================
    // UPDATE NOTIFICATION
    // ============================================
    
    function showUpdateNotification() {
        const notification = document.createElement('div');
        notification.id = 'pwa-update-notification';
        notification.innerHTML = `
            <style>
                #pwa-update-notification {
                    position: fixed;
                    bottom: 24px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #1D1D1F;
                    color: white;
                    padding: 16px 24px;
                    border-radius: 12px;
                    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    z-index: 10000;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
                    font-size: 1rem;
                    animation: slideUp 0.3s ease;
                }
                @keyframes slideUp {
                    from { transform: translateX(-50%) translateY(100px); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
                #pwa-update-notification button {
                    background: #0071E3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-size: 0.9rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                #pwa-update-notification button:hover {
                    background: #0077ED;
                }
                #pwa-update-notification .dismiss {
                    background: transparent;
                    padding: 8px;
                    opacity: 0.6;
                }
                #pwa-update-notification .dismiss:hover {
                    opacity: 1;
                    background: rgba(255,255,255,0.1);
                }
            </style>
            <span>Nueva version disponible</span>
            <button onclick="updateApp()">Actualizar</button>
            <button class="dismiss" onclick="this.parentElement.remove()">x</button>
        `;
        
        document.body.appendChild(notification);
    }
    
    window.updateApp = function() {
        if (navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
        }
        window.location.reload();
    };

    // ============================================
    // INSTALL PROMPT (A2HS)
    // ============================================
    
    let deferredPrompt = null;
    
    window.addEventListener('beforeinstallprompt', (e) => {
        console.log('[PWA] Install prompt available');
        e.preventDefault();
        deferredPrompt = e;
        
        const installBtn = document.getElementById('pwa-install-btn');
        if (installBtn) {
            installBtn.style.display = 'inline-flex';
        }
    });
    
    window.addEventListener('appinstalled', () => {
        console.log('[PWA] App installed');
        deferredPrompt = null;
        
        const installBtn = document.getElementById('pwa-install-btn');
        if (installBtn) {
            installBtn.style.display = 'none';
        }
    });
    
    window.installPWA = async function() {
        if (!deferredPrompt) {
            console.log('[PWA] No install prompt available');
            return false;
        }
        
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log('[PWA] Install prompt outcome:', outcome);
        deferredPrompt = null;
        
        return outcome === 'accepted';
    };
    
    window.isPWAInstalled = function() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    };

    // ============================================
    // ONLINE/OFFLINE DETECTION
    // ============================================
    
    function updateOnlineStatus() {
        const isOnline = navigator.onLine;
        document.body.classList.toggle('offline', !isOnline);
        
        window.dispatchEvent(new CustomEvent('connectionchange', { 
            detail: { online: isOnline } 
        }));
        
        if (isOnline) {
            console.log('[PWA] Back online');
            if ('serviceWorker' in navigator && window.SyncManager && 'sync' in window.SyncManager) {
                navigator.serviceWorker.ready.then(registration => {
                    registration.sync.register('sync-viajes');
                });
            }
        } else {
            console.log('[PWA] Gone offline');
        }
    }
    
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();

    console.log('[PWA] Module loaded');
})();
