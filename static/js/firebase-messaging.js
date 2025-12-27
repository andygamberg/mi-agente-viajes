/**
 * Firebase Cloud Messaging - Mi Agente Viajes
 * 
 * Maneja push notifications para alertas de vuelos.
 */

// Firebase Config
const firebaseConfig = {
    apiKey: "AIzaSyDCI-hezW3tkakAuQ-2hVh_6757Qltg_4E",
    authDomain: "mi-agente-viajes-2a67b.firebaseapp.com",
    projectId: "mi-agente-viajes-2a67b",
    storageBucket: "mi-agente-viajes-2a67b.firebasestorage.app",
    messagingSenderId: "810177845932",
    appId: "1:810177845932:web:8cb82f9968cebd4ce49d09"
};

const VAPID_KEY = 'BLAz7Ww9K51xhVrFll3kVRNACRbTU8HBVp2zGzcKamgZgjKnqOPpFEQ25jE84_ibLUM4eS-eL6lnlm9Slj_DeD8';

class PushNotifications {
    constructor() {
        this.messaging = null;
        this.token = null;
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
    }

    // ============================================
    // INICIALIZACIÓN
    // ============================================

    async init() {
        if (!this.isSupported) {
            console.log('[Push] Not supported in this browser');
            return false;
        }

        try {
            // Cargar Firebase SDK dinámicamente
            await this.loadFirebaseSDK();
            
            // Inicializar Firebase
            const app = firebase.initializeApp(firebaseConfig);
            this.messaging = firebase.messaging();

            console.log('[Push] Firebase initialized');
            return true;
        } catch (error) {
            console.error('[Push] Init failed:', error);
            return false;
        }
    }

    async loadFirebaseSDK() {
        // Si ya está cargado, salir
        if (window.firebase && window.firebase.messaging) {
            return;
        }

        // Cargar scripts de Firebase
        await this.loadScript('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
        await this.loadScript('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // ============================================
    // PERMISOS Y TOKEN
    // ============================================

    async requestPermission() {
        if (!this.isSupported) {
            return { success: false, error: 'Not supported' };
        }

        try {
            const permission = await Notification.requestPermission();
            
            if (permission !== 'granted') {
                console.log('[Push] Permission denied');
                return { success: false, error: 'Permission denied' };
            }

            console.log('[Push] Permission granted');
            
            // Obtener token
            const token = await this.getToken();
            
            if (token) {
                // Guardar token en el servidor
                await this.saveTokenToServer(token);
                return { success: true, token };
            }

            return { success: false, error: 'Could not get token' };
        } catch (error) {
            console.error('[Push] Permission request failed:', error);
            return { success: false, error: error.message };
        }
    }

    async getToken() {
        if (!this.messaging) {
            await this.init();
        }

        try {
            // Esperar a que el SW esté listo
            const registration = await navigator.serviceWorker.ready;

            const token = await this.messaging.getToken({
                vapidKey: VAPID_KEY,
                serviceWorkerRegistration: registration
            });

            if (token) {
                console.log('[Push] Token obtained');
                this.token = token;
                return token;
            }

            console.log('[Push] No token available');
            return null;
        } catch (error) {
            console.error('[Push] getToken failed:', error);
            return null;
        }
    }

    // ============================================
    // COMUNICACIÓN CON SERVIDOR
    // ============================================

    async saveTokenToServer(token) {
        try {
            const response = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token })
            });

            if (response.ok) {
                console.log('[Push] Token saved to server');
                localStorage.setItem('pushToken', token);
                return true;
            }

            console.error('[Push] Failed to save token');
            return false;
        } catch (error) {
            console.error('[Push] saveToken failed:', error);
            return false;
        }
    }

    async unsubscribe() {
        try {
            const token = this.token || localStorage.getItem('pushToken');
            
            if (token) {
                await fetch('/api/push/unsubscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ token })
                });

                localStorage.removeItem('pushToken');
            }

            if (this.messaging) {
                await this.messaging.deleteToken();
            }

            this.token = null;
            console.log('[Push] Unsubscribed');
            return true;
        } catch (error) {
            console.error('[Push] Unsubscribe failed:', error);
            return false;
        }
    }

    // ============================================
    // ESTADO
    // ============================================

    getPermissionStatus() {
        if (!this.isSupported) {
            return 'unsupported';
        }
        return Notification.permission; // 'granted', 'denied', 'default'
    }

    isSubscribed() {
        return !!localStorage.getItem('pushToken');
    }

    // ============================================
    // LISTENERS
    // ============================================

    onMessage(callback) {
        if (!this.messaging) {
            console.warn('[Push] Messaging not initialized');
            return;
        }

        this.messaging.onMessage((payload) => {
            console.log('[Push] Message received:', payload);
            callback(payload);
        });
    }
}

// Instancia global
window.pushNotifications = new PushNotifications();

// Auto-init si ya tiene permiso
if (Notification.permission === 'granted') {
    window.pushNotifications.init().then(() => {
        // Verificar si el token sigue válido
        const savedToken = localStorage.getItem('pushToken');
        if (savedToken) {
            window.pushNotifications.getToken();
        }
    });
}
