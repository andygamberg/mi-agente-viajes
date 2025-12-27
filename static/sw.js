/**
 * Service Worker - Mi Agente Viajes PWA
 * Versión: 1.0
 * 
 * Estrategias:
 * - Assets estáticos: Cache First
 * - API calls: Network First con fallback a cache
 * - Navegación: Network First con offline fallback
 */

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DATA_CACHE = `data-${CACHE_VERSION}`;

// Assets para precachear en install
const PRECACHE_ASSETS = [
  '/',
  '/offline',
  '/static/manifest.json',
  '/static/favicon.svg',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Rutas de API para cachear
const API_PATTERNS = [
  '/api/viajes',
  '/api/viajes/count'
];

// ============================================
// HELPERS
// ============================================

function isApiRequest(pathname) {
  return API_PATTERNS.some(pattern => pathname.startsWith(pattern));
}

function isStaticAsset(pathname) {
  return pathname.startsWith('/static/') || 
         pathname.endsWith('.css') || 
         pathname.endsWith('.js') ||
         pathname.endsWith('.png') ||
         pathname.endsWith('.svg') ||
         pathname.endsWith('.ico');
}

// ============================================
// INSTALL - Precachear assets críticos
// ============================================
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Precaching assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch((err) => console.error('[SW] Precache failed:', err))
  );
});

// ============================================
// ACTIVATE - Limpiar caches viejos
// ============================================
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== STATIC_CACHE && name !== DATA_CACHE)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// ============================================
// FETCH STRATEGIES
// ============================================

// Cache First: Busca en cache, si no existe va a network
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.error('[SW] Cache first failed:', error);
    throw error;
  }
}

// Network First: Intenta network, si falla usa cache
async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Network failed, trying cache');
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    throw error;
  }
}

// Network First con fallback a página offline
async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Offline, serving cached or offline page');
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    // Servir página offline
    return caches.match('/offline');
  }
}

// ============================================
// FETCH - Interceptar requests
// ============================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Solo manejar requests del mismo origen
  if (url.origin !== location.origin) {
    return;
  }
  
  // Ignorar requests de extensiones, websockets, etc.
  if (request.method !== 'GET') {
    return;
  }
  
  // API requests: Network First
  if (isApiRequest(url.pathname)) {
    event.respondWith(networkFirst(request, DATA_CACHE));
    return;
  }
  
  // Assets estáticos: Cache First
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }
  
  // Navegación HTML: Network First con offline fallback
  if (request.mode === 'navigate') {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }
});

// ============================================
// SYNC - Background sync para cuando vuelve conexión
// ============================================
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-viajes') {
    event.waitUntil(syncViajes());
  }
});

async function syncViajes() {
  // Placeholder para sync de datos offline
  // Se implementará en Fase 2
  console.log('[SW] Syncing viajes data...');
}

// ============================================
// PUSH - Preparado para notificaciones (Fase 3)
// ============================================
self.addEventListener('push', (event) => {
  console.log('[SW] Push received');
  
  if (!event.data) return;
  
  const data = event.data.json();
  const options = {
    body: data.body || 'Actualización de vuelo',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/'
    },
    actions: [
      { action: 'open', title: 'Ver' },
      { action: 'close', title: 'Cerrar' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Mi Agente Viajes', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');
  event.notification.close();
  
  if (event.action === 'close') return;
  
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    clients.openWindow(url)
  );
});

// ============================================
// MESSAGE - Comunicación con la app
// ============================================
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data.type === 'CACHE_VIAJES') {
    // Cachear datos de viajes manualmente
    caches.open(DATA_CACHE).then((cache) => {
      cache.put('/api/viajes', new Response(JSON.stringify(event.data.viajes)));
    });
  }
});
