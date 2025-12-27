/**
 * Offline Storage - Mi Agente Viajes
 * 
 * Maneja IndexedDB para almacenar viajes localmente
 * y sincronizar cuando vuelve la conexión.
 */

const DB_NAME = 'MisViajesDB';
const DB_VERSION = 1;
const STORE_VIAJES = 'viajes';
const STORE_META = 'meta';

class OfflineStorage {
    constructor() {
        this.db = null;
        this.isOnline = navigator.onLine;
        this.init();
        this.setupListeners();
    }

    // ============================================
    // INICIALIZACIÓN
    // ============================================

    async init() {
        try {
            this.db = await this.openDB();
            console.log('[OfflineStorage] Database initialized');
        } catch (error) {
            console.error('[OfflineStorage] Init failed:', error);
        }
    }

    openDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Store para viajes
                if (!db.objectStoreNames.contains(STORE_VIAJES)) {
                    const viajesStore = db.createObjectStore(STORE_VIAJES, { keyPath: 'id' });
                    viajesStore.createIndex('fecha_inicio', 'fecha_inicio', { unique: false });
                    viajesStore.createIndex('updated_at', 'updated_at', { unique: false });
                }

                // Store para metadata (última sync, etc)
                if (!db.objectStoreNames.contains(STORE_META)) {
                    db.createObjectStore(STORE_META, { keyPath: 'key' });
                }

                console.log('[OfflineStorage] Database schema created');
            };
        });
    }

    setupListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            console.log('[OfflineStorage] Online - syncing...');
            this.syncWithServer();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            console.log('[OfflineStorage] Offline mode');
        });
    }

    // ============================================
    // OPERACIONES CRUD
    // ============================================

    async saveViajes(viajes) {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_VIAJES, STORE_META], 'readwrite');
            const store = transaction.objectStore(STORE_VIAJES);
            const metaStore = transaction.objectStore(STORE_META);

            // Limpiar viajes antiguos y guardar nuevos
            store.clear();

            viajes.forEach(viaje => {
                store.put(viaje);
            });

            // Guardar timestamp de última sync
            metaStore.put({
                key: 'lastSync',
                value: new Date().toISOString(),
                count: viajes.length
            });

            transaction.oncomplete = () => {
                console.log(`[OfflineStorage] Saved ${viajes.length} viajes`);
                resolve(viajes.length);
            };

            transaction.onerror = () => reject(transaction.error);
        });
    }

    async getViajes() {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_VIAJES], 'readonly');
            const store = transaction.objectStore(STORE_VIAJES);
            const request = store.getAll();

            request.onsuccess = () => {
                const viajes = request.result || [];
                console.log(`[OfflineStorage] Retrieved ${viajes.length} viajes from cache`);
                resolve(viajes);
            };

            request.onerror = () => reject(request.error);
        });
    }

    async getViaje(id) {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_VIAJES], 'readonly');
            const store = transaction.objectStore(STORE_VIAJES);
            const request = store.get(id);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getLastSync() {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_META], 'readonly');
            const store = transaction.objectStore(STORE_META);
            const request = store.get('lastSync');

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async clearAll() {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_VIAJES, STORE_META], 'readwrite');
            transaction.objectStore(STORE_VIAJES).clear();
            transaction.objectStore(STORE_META).clear();

            transaction.oncomplete = () => {
                console.log('[OfflineStorage] All data cleared');
                resolve();
            };

            transaction.onerror = () => reject(transaction.error);
        });
    }

    // ============================================
    // SYNC CON SERVIDOR
    // ============================================

    async syncWithServer() {
        if (!this.isOnline) {
            console.log('[OfflineStorage] Cannot sync - offline');
            return false;
        }

        try {
            const response = await fetch('/api/viajes');
            if (!response.ok) throw new Error('API error');

            const data = await response.json();
            await this.saveViajes(data.viajes || []);

            // Notificar a la UI que hay datos nuevos
            window.dispatchEvent(new CustomEvent('viajessynced', {
                detail: { count: data.viajes?.length || 0 }
            }));

            return true;
        } catch (error) {
            console.error('[OfflineStorage] Sync failed:', error);
            return false;
        }
    }

    // ============================================
    // FETCH CON FALLBACK OFFLINE
    // ============================================

    async fetchViajes() {
        // Si estamos online, intentar fetch normal y cachear
        if (this.isOnline) {
            try {
                const response = await fetch('/api/viajes');
                if (response.ok) {
                    const data = await response.json();
                    // Guardar en cache para offline
                    await this.saveViajes(data.viajes || []);
                    return { viajes: data.viajes, fromCache: false };
                }
            } catch (error) {
                console.log('[OfflineStorage] Fetch failed, using cache');
            }
        }

        // Fallback a cache
        const viajes = await this.getViajes();
        const lastSync = await this.getLastSync();

        return {
            viajes,
            fromCache: true,
            lastSync: lastSync?.value
        };
    }
}

// Instancia global
window.offlineStorage = new OfflineStorage();

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OfflineStorage;
}
