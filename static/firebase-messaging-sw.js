/**
 * Firebase Messaging Service Worker
 * 
 * Este archivo debe servirse desde la raíz: /firebase-messaging-sw.js
 * Maneja notificaciones push en background.
 */

// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

// Firebase Config
const firebaseConfig = {
    apiKey: "AIzaSyDCI-hezW3tkakAuQ-2hVh_6757Qltg_4E",
    authDomain: "mi-agente-viajes-2a67b.firebaseapp.com",
    projectId: "mi-agente-viajes-2a67b",
    storageBucket: "mi-agente-viajes-2a67b.firebasestorage.app",
    messagingSenderId: "810177845932",
    appId: "1:810177845932:web:8cb82f9968cebd4ce49d09"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Background message:', payload);

    const notificationTitle = payload.notification?.title || 'Mi Agente Viajes';
    const notificationOptions = {
        body: payload.notification?.body || 'Tienes una actualización',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        tag: payload.data?.tag || 'default',
        data: {
            url: payload.data?.url || '/',
            ...payload.data
        },
        actions: [
            { action: 'open', title: 'Ver detalles' },
            { action: 'close', title: 'Cerrar' }
        ]
    };

    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Notification clicked:', event);

    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    const url = event.notification.data?.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Si ya hay una ventana abierta, enfocarla y navegar
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.navigate(url);
                        return client.focus();
                    }
                }
                // Si no hay ventana, abrir una nueva
                return clients.openWindow(url);
            })
    );
});

console.log('[firebase-messaging-sw.js] Loaded');
