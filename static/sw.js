/**
 * Service Worker - Mi Agente Viajes PWA
 * Versión: 2.0 (con Offline Data)
 * 
 * Estrategias de cache:
 * - Assets estáticos: Cache First
 * - API calls: Network First con fallback a cache
 * - Navegación: Network First con offline fallback
 */

const CACHE_VERSION = 'v5-network-first-js';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DATA_CACHE = `data-${CACHE_VERSION}`;

// Assets estáticos para precachear al instalar
const STATIC_ASSETS = [
  '/',
  '/offline',
  '/static/manifest.json',
  '/static/favicon.svg',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/static/js/pwa.js',
  '/static/js/offline-storage.js'
];

// Rutas de API que queremos cachear para offline
const API_ROUTES = [
  '/api/viajes',
  '/api/viajes/count'
];

// ============================================
// HELPERS
// ============================================

function isApiRequest(pathname) {
  return API_ROUTES.some(route => pathname.startsWith(route));
}

function isJavaScript(pathname) {
  return pathname.endsWith('.js');
}

function isStaticAsset(pathname) {
  return pathname.startsWith('/static/') ||
         pathname.endsWith('.css') ||
         pathname.endsWith('.png') ||
         pathname.endsWith('.svg') ||
         pathname.endsWith('.ico') ||
         pathname.endsWith('.woff2');
}

function isHTMLPage(pathname) {
  return !pathname.includes('.') || pathname.endsWith('.html');
}

// ============================================
// INSTALL - Precachear assets estáticos
// ============================================
self.addEventListener('install', (event) => {
  console.log('[SW] Installing v2...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return Promise.allSettled(
          STATIC_ASSETS.map(url => 
            cache.add(url).catch(err => {
              console.warn(`[SW] Failed to cache: ${url}`, err);
            })
          )
        );
      })
      .then(() => {
        console.log('[SW] Static assets cached');
        return self.skipWaiting();
      })
  );
});

// ============================================
// ACTIVATE - Limpiar caches viejos
// ============================================
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating v2...');
  
  const currentCaches = [STATIC_CACHE, DATA_CACHE];
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter(name => !currentCaches.includes(name))
            .map(name => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Activated');
        return self.clients.claim();
      })
  );
});

// ============================================
// FETCH STRATEGIES
// ============================================

// Cache First: Buscar en cache, si no hay ir a network
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

// Network First: Ir a network, si falla usar cache
async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    throw error;
  }
}

// Network First para API con respuesta JSON cacheada
async function networkFirstAPI(request) {
  const cache = await caches.open(DATA_CACHE);
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      // Clonar y cachear
      cache.put(request, response.clone());
      console.log('[SW] API cached:', request.url);
    }
    return response;
  } catch (error) {
    console.log('[SW] API offline, using cache:', request.url);
    const cached = await cache.match(request);
    
    if (cached) {
      // Agregar header indicando que es de cache
      const headers = new Headers(cached.headers);
      headers.set('X-From-Cache', 'true');
      
      return new Response(cached.body, {
        status: cached.status,
        statusText: cached.statusText,
        headers: headers
      });
    }
    
    // Si no hay cache, devolver respuesta vacía pero válida
    return new Response(JSON.stringify({ 
      viajes: [], 
      fromCache: true,
      error: 'No cached data available'
    }), {
      status: 200,
      headers: { 
        'Content-Type': 'application/json',
        'X-From-Cache': 'true',
        'X-Cache-Empty': 'true'
      }
    });
  }
}

// Network First con fallback a página offline
async function networkFirstWithOffline(request) {
  const cache = await caches.open(STATIC_CACHE);
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Page offline, checking cache');
    
    // Intentar cache primero
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    
    // Si es navegación, mostrar página offline
    const offlinePage = await cache.match('/offline');
    if (offlinePage) {
      return offlinePage;
    }
    
    throw error;
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
  
  // Ignorar requests de extensiones y websockets
  if (request.url.includes('chrome-extension') || 
      request.url.includes('ws://') ||
      request.url.includes('wss://')) {
    return;
  }
  
  // API requests: Network First con cache especial
  if (isApiRequest(url.pathname)) {
    event.respondWith(networkFirstAPI(request));
    return;
  }

  // JavaScript files: Network First (para debug - siempre buscar versión nueva)
  if (isJavaScript(url.pathname)) {
    event.respondWith(networkFirst(request, STATIC_CACHE));
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

  // Todo lo demás: Network First
  event.respondWith(networkFirst(request, STATIC_CACHE));
});

// ============================================
// SYNC - Para sincronizar datos cuando vuelve conexión
// ============================================
self.addEventListener('sync', (event) => {
  console.log('[SW] Sync event:', event.tag);
  
  if (event.tag === 'sync-viajes') {
    event.waitUntil(syncViajes());
  }
});

async function syncViajes() {
  console.log('[SW] Syncing viajes...');
  
  try {
    // Notificar a los clients que sincronicen
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({ type: 'SYNC_VIAJES' });
    });
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

// ============================================
// PUSH NOTIFICATIONS (Fase 3 - preparado)
// ============================================
self.addEventListener('push', (event) => {
  console.log('[SW] Push received:', event);
  
  if (!event.data) return;
  
  const data = event.data.json();
  
  const options = {
    body: data.body || 'Tienes una actualización',
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
  console.log('[SW] Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'close') return;
  
  const url = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(url);
            return client.focus();
          }
        }
        return clients.openWindow(url);
      })
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
  
  if (event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_VERSION });
  }
  
  if (event.data.type === 'CLEAR_CACHE') {
    caches.keys().then(names => {
      names.forEach(name => caches.delete(name));
    });
  }
  
  if (event.data.type === 'CACHE_VIAJES') {
    // Forzar cache de viajes
    caches.open(DATA_CACHE).then(cache => {
      fetch('/api/viajes').then(response => {
        if (response.ok) {
          cache.put('/api/viajes', response);
          console.log('[SW] Viajes cached on demand');
        }
      });
    });
  }
});

console.log('[SW] Service Worker v2 loaded');
