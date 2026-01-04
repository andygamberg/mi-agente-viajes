/**
 * Pull to Refresh - Mi Agente Viajes PWA
 *
 * Implementa gesto de pull-to-refresh para móviles
 * Solo activo cuando está en modo standalone (PWA instalada)
 */

(function() {
    'use strict';

    // Solo activar en PWA instalada
    const isPWA = window.matchMedia('(display-mode: standalone)').matches ||
                  window.navigator.standalone === true;

    if (!isPWA) {
        console.log('[PTR] Not in PWA mode, pull-to-refresh disabled');
        return;
    }

    // Deshabilitar pull-to-refresh nativo de Safari en iOS
    document.body.style.overscrollBehavior = 'contain';
    document.documentElement.style.overscrollBehavior = 'contain';

    let touchStartY = 0;
    let touchCurrentY = 0;
    let refreshing = false;
    let ptrElement = null;

    const PULL_THRESHOLD = 80; // Pixels necesarios para activar refresh
    const MAX_PULL = 120; // Máximo pull visible

    // ============================================
    // CREAR INDICADOR VISUAL
    // ============================================

    function createPTRIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'ptr-indicator';
        indicator.innerHTML = `
            <style>
                #ptr-indicator {
                    position: fixed;
                    top: -80px;
                    left: 0;
                    right: 0;
                    height: 80px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: linear-gradient(180deg, #F5F5F7 0%, transparent 100%);
                    transition: transform 0.2s ease-out, opacity 0.2s;
                    z-index: 9999;
                    pointer-events: none;
                }
                #ptr-indicator.pulling {
                    transition: none;
                }
                #ptr-indicator.refreshing {
                    transform: translateY(80px);
                }
                .ptr-spinner {
                    width: 32px;
                    height: 32px;
                    border: 3px solid #D2D2D7;
                    border-top-color: #0071E3;
                    border-radius: 50%;
                    animation: ptr-spin 0.8s linear infinite;
                }
                .ptr-arrow {
                    width: 24px;
                    height: 24px;
                    color: #0071E3;
                    transition: transform 0.3s;
                }
                .ptr-arrow.ready {
                    transform: rotate(180deg);
                }
                @keyframes ptr-spin {
                    to { transform: rotate(360deg); }
                }
            </style>
            <div class="ptr-content">
                <svg class="ptr-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"
                          d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
                </svg>
            </div>
        `;
        document.body.appendChild(indicator);
        return indicator;
    }

    // ============================================
    // TOUCH HANDLERS
    // ============================================

    function onTouchStart(e) {
        // Solo activar si está en el top de la página
        if (window.scrollY > 0) {
            console.log('[PTR] Ignoring touch - not at top (scrollY:', window.scrollY, ')');
            return;
        }

        // Solo activar en páginas principales (no modales, no formularios)
        const target = e.target;
        if (target.closest('.modal') ||
            target.closest('form') ||
            target.closest('input') ||
            target.closest('textarea')) {
            console.log('[PTR] Ignoring touch - inside form/modal');
            return;
        }

        touchStartY = e.touches[0].clientY;
        console.log('[PTR] Touch start at Y:', touchStartY);
    }

    function onTouchMove(e) {
        if (!touchStartY || refreshing) return;

        touchCurrentY = e.touches[0].clientY;
        const pullDistance = touchCurrentY - touchStartY;

        // Solo procesar si está tirando hacia abajo y en el top
        if (pullDistance > 0 && window.scrollY === 0) {
            console.log('[PTR] Pull distance:', pullDistance);

            // Prevenir scroll nativo mientras hace pull
            if (pullDistance > 10) {
                e.preventDefault();
                console.log('[PTR] Preventing default scroll');
            }

            const cappedDistance = Math.min(pullDistance, MAX_PULL);
            const progress = cappedDistance / PULL_THRESHOLD;

            if (!ptrElement) {
                ptrElement = createPTRIndicator();
            }

            // Actualizar posición del indicador
            ptrElement.classList.add('pulling');
            ptrElement.style.transform = `translateY(${cappedDistance}px)`;
            ptrElement.style.opacity = Math.min(progress, 1);

            // Animar flecha
            const arrow = ptrElement.querySelector('.ptr-arrow');
            if (arrow) {
                if (progress >= 1) {
                    arrow.classList.add('ready');
                } else {
                    arrow.classList.remove('ready');
                }
            }
        }
    }

    function onTouchEnd(e) {
        if (!touchStartY || refreshing) return;

        const pullDistance = touchCurrentY - touchStartY;

        if (pullDistance >= PULL_THRESHOLD && window.scrollY === 0) {
            // Activar refresh
            triggerRefresh();
        } else {
            // Reset si no llegó al threshold
            resetPTR();
        }

        touchStartY = 0;
        touchCurrentY = 0;
    }

    // ============================================
    // REFRESH LOGIC
    // ============================================

    function triggerRefresh() {
        if (refreshing) return;

        refreshing = true;

        if (!ptrElement) {
            ptrElement = createPTRIndicator();
        }

        // Cambiar a spinner
        const content = ptrElement.querySelector('.ptr-content');
        content.innerHTML = '<div class="ptr-spinner"></div>';

        // Animar a posición visible
        ptrElement.classList.remove('pulling');
        ptrElement.classList.add('refreshing');
        ptrElement.style.opacity = '1';

        // Ejecutar refresh
        performRefresh().finally(() => {
            // Esperar un poquito para que se vea el spinner
            setTimeout(() => {
                resetPTR();
                refreshing = false;
            }, 400);
        });
    }

    async function performRefresh() {
        console.log('[PTR] Refreshing...');

        try {
            // 1. Actualizar Service Worker si hay nueva versión
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.getRegistration();
                if (registration) {
                    await registration.update();
                }
            }

            // 2. Recargar datos de la página actual
            // Si está en index, refrescar viajes
            if (window.location.pathname === '/' || window.location.pathname === '/index') {
                if (typeof window.loadViajes === 'function') {
                    await window.loadViajes();
                } else {
                    // Fallback: recargar página
                    window.location.reload();
                }
            } else {
                // Otras páginas: recargar
                window.location.reload();
            }

            console.log('[PTR] Refresh complete');
        } catch (error) {
            console.error('[PTR] Refresh failed:', error);
        }
    }

    function resetPTR() {
        if (!ptrElement) return;

        ptrElement.classList.remove('pulling', 'refreshing');
        ptrElement.style.transform = '';
        ptrElement.style.opacity = '0';

        setTimeout(() => {
            if (ptrElement && !refreshing) {
                ptrElement.remove();
                ptrElement = null;
            }
        }, 300);
    }

    // ============================================
    // INIT
    // ============================================

    document.addEventListener('touchstart', onTouchStart, { passive: true });
    document.addEventListener('touchmove', onTouchMove, { passive: false });
    document.addEventListener('touchend', onTouchEnd, { passive: true });

    console.log('[PTR] Pull-to-refresh enabled');
})();
