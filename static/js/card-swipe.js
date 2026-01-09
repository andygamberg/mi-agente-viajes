/**
 * Card Swipe Gestures - Mi Agente Viajes
 *
 * Permite swipe left/right en tarjetas de viajes para mostrar acciones:
 * - Swipe izquierda: Borrar (rojo)
 * - Swipe derecha: Agrupar/Editar (azul/verde)
 */

console.log('[CardSwipe] Module loaded');

class CardSwipeHandler {
    constructor() {
        this.activeCard = null;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.isDragging = false;
        this.threshold = 60; // pixels para activar acción
        this.maxSwipe = 120; // máximo desplazamiento

        this.init();
    }

    init() {
        console.log('[CardSwipe] Initializing swipe handlers');

        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.attachListeners());
        } else {
            this.attachListeners();
        }
    }

    attachListeners() {
        const cards = document.querySelectorAll('.card');
        console.log(`[CardSwipe] Found ${cards.length} cards`);

        cards.forEach(card => {
            // Crear wrapper para swipe
            if (!card.querySelector('.swipe-wrapper')) {
                this.wrapCard(card);
            }

            const wrapper = card.querySelector('.swipe-wrapper');

            wrapper.addEventListener('touchstart', (e) => this.onTouchStart(e, card), { passive: true });
            wrapper.addEventListener('touchmove', (e) => this.onTouchMove(e, card), { passive: false });
            wrapper.addEventListener('touchend', (e) => this.onTouchEnd(e, card), { passive: true });
        });
    }

    wrapCard(card) {
        // Crear contenedor de acciones de fondo
        const actionsLeft = document.createElement('div');
        actionsLeft.className = 'swipe-actions swipe-actions-left';
        actionsLeft.innerHTML = `
            <button class="swipe-action swipe-action-edit" data-action="edit">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                <span>Editar</span>
            </button>
            <button class="swipe-action swipe-action-group" data-action="group">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <span>Agrupar</span>
            </button>
        `;

        const actionsRight = document.createElement('div');
        actionsRight.className = 'swipe-actions swipe-actions-right';
        actionsRight.innerHTML = `
            <button class="swipe-action swipe-action-delete" data-action="delete">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
                <span>Borrar</span>
            </button>
        `;

        // Wrapper que se desliza
        const wrapper = document.createElement('div');
        wrapper.className = 'swipe-wrapper';

        // Mover contenido al wrapper
        while (card.firstChild) {
            wrapper.appendChild(card.firstChild);
        }

        // Estructura final
        card.appendChild(actionsLeft);
        card.appendChild(wrapper);
        card.appendChild(actionsRight);

        // Agregar clase para identificar que ya tiene swipe
        card.classList.add('swipe-enabled');

        // Event listeners para las acciones
        actionsLeft.querySelectorAll('.swipe-action').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleAction(e, card));
        });
        actionsRight.querySelectorAll('.swipe-action').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleAction(e, card));
        });
    }

    onTouchStart(e, card) {
        // Ignorar si se toca un botón o link
        if (e.target.closest('button, a, input, select, textarea')) {
            return;
        }

        // No activar si estamos en el top y puede ser pull-to-refresh
        if (window.scrollY === 0 && e.touches[0].clientY < 100) {
            console.log('[CardSwipe] Near top, allowing pull-to-refresh');
            return;
        }

        this.activeCard = card;
        this.startX = e.touches[0].clientX;
        this.startY = e.touches[0].clientY;
        this.isDragging = false;

        const wrapper = card.querySelector('.swipe-wrapper');
        wrapper.style.transition = 'none';
    }

    onTouchMove(e, card) {
        if (!this.activeCard) return;

        const touchX = e.touches[0].clientX;
        const touchY = e.touches[0].clientY;
        const deltaX = touchX - this.startX;
        const deltaY = touchY - this.startY;

        // Determinar si es swipe horizontal
        if (!this.isDragging) {
            if (Math.abs(deltaX) > 10 && Math.abs(deltaX) > Math.abs(deltaY)) {
                this.isDragging = true;
                console.log('[CardSwipe] Started dragging');
            } else if (Math.abs(deltaY) > 10) {
                // Es scroll vertical, cancelar
                this.activeCard = null;
                return;
            }
        }

        if (this.isDragging) {
            // Prevenir scroll mientras hacemos swipe
            e.preventDefault();

            // Limitar el desplazamiento
            this.currentX = Math.max(-this.maxSwipe, Math.min(this.maxSwipe, deltaX));

            const wrapper = card.querySelector('.swipe-wrapper');
            wrapper.style.transform = `translateX(${this.currentX}px)`;

            // Mostrar/ocultar acciones según dirección
            const actionsLeft = card.querySelector('.swipe-actions-left');
            const actionsRight = card.querySelector('.swipe-actions-right');

            if (this.currentX > 0) {
                // Swipe derecha - mostrar acciones izquierdas
                actionsLeft.style.opacity = Math.min(1, this.currentX / this.threshold);
            } else if (this.currentX < 0) {
                // Swipe izquierda - mostrar acciones derechas
                actionsRight.style.opacity = Math.min(1, Math.abs(this.currentX) / this.threshold);
            }
        }
    }

    onTouchEnd(e, card) {
        if (!this.activeCard || !this.isDragging) {
            this.activeCard = null;
            return;
        }

        const wrapper = card.querySelector('.swipe-wrapper');
        wrapper.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

        // Determinar si se activó una acción
        if (Math.abs(this.currentX) >= this.threshold) {
            // Mantener abierto
            if (this.currentX > 0) {
                wrapper.style.transform = `translateX(${this.maxSwipe}px)`;
                card.classList.add('swiped-right');
                card.classList.remove('swiped-left');
                console.log('[CardSwipe] Swiped right - show group/edit');
            } else {
                wrapper.style.transform = `translateX(-${this.maxSwipe}px)`;
                card.classList.add('swiped-left');
                card.classList.remove('swiped-right');
                console.log('[CardSwipe] Swiped left - show delete');
            }
        } else {
            // Volver a posición original
            this.resetCard(card);
        }

        this.activeCard = null;
        this.isDragging = false;
        this.currentX = 0;
    }

    resetCard(card) {
        const wrapper = card.querySelector('.swipe-wrapper');
        wrapper.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        wrapper.style.transform = 'translateX(0)';

        card.classList.remove('swiped-left', 'swiped-right');

        // Fade out acciones
        const actions = card.querySelectorAll('.swipe-actions');
        actions.forEach(action => {
            action.style.opacity = '0';
        });
    }

    handleAction(e, card) {
        e.stopPropagation();
        const action = e.currentTarget.dataset.action;
        const grupoId = card.id.replace('card-', '');

        console.log(`[CardSwipe] Action: ${action} on card: ${grupoId}`);

        // Cerrar el swipe primero
        this.resetCard(card);

        // Ejecutar acción después de la animación
        setTimeout(() => {
            switch (action) {
                case 'delete':
                    this.deleteGroup(grupoId, card);
                    break;
                case 'edit':
                    this.editGroup(grupoId);
                    break;
                case 'group':
                    this.groupTrips(grupoId);
                    break;
            }
        }, 300);
    }

    deleteGroup(grupoId, card) {
        // Usar la función existente de borrar
        if (typeof window.borrarGrupo === 'function') {
            window.borrarGrupo(grupoId);
        } else {
            console.error('[CardSwipe] borrarGrupo function not found');
        }
    }

    editGroup(grupoId) {
        // Redirigir a la página de edición
        const firstTrip = document.querySelector(`#card-${grupoId} [data-viaje-id]`);
        if (firstTrip) {
            const viajeId = firstTrip.dataset.viajeId;
            window.location.href = `/editar/${viajeId}`;
        }
    }

    groupTrips(grupoId) {
        // Abrir el modal de agrupar
        if (typeof window.mostrarModalAgrupar === 'function') {
            window.mostrarModalAgrupar(grupoId);
        } else {
            console.error('[CardSwipe] mostrarModalAgrupar function not found');
        }
    }

    // Resetear todas las tarjetas abiertas
    resetAllCards() {
        document.querySelectorAll('.card.swiped-left, .card.swiped-right').forEach(card => {
            this.resetCard(card);
        });
    }
}

// Inicializar cuando el DOM esté listo
if (typeof window !== 'undefined') {
    window.cardSwipeHandler = new CardSwipeHandler();

    // Resetear al hacer scroll
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            if (window.cardSwipeHandler) {
                window.cardSwipeHandler.resetAllCards();
            }
        }, 150);
    }, { passive: true });
}
