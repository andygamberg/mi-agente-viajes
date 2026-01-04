/**
 * Missing Passengers Banner - Mi Agente Viajes
 *
 * Detecta reservas con pasajeros/huéspedes faltantes y sugiere completarlos
 * Se activa automáticamente después de cargar una nueva reserva desde email/PDF
 */

(function() {
    'use strict';

    // Verificar pasajeros faltantes después de un guardado exitoso
    window.checkMissingPassengersAfterSave = function(viajeId, source) {
        // Solo verificar para reservas automáticas (no manuales)
        if (source === 'manual') {
            return;
        }

        // Esperar un poquito para que el DOM esté listo
        setTimeout(() => {
            fetch(`/api/check-missing-passengers/${viajeId}`)
                .then(r => r.json())
                .then(data => {
                    if (data.missing && data.suggestion) {
                        showMissingPassengersBanner(data);
                    }
                })
                .catch(err => {
                    console.error('[Missing Passengers] Error checking:', err);
                });
        }, 500);
    };

    function showMissingPassengersBanner(data) {
        // No mostrar si ya existe un banner
        if (document.getElementById('missing-passengers-banner')) {
            return;
        }

        // Crear banner
        const banner = document.createElement('div');
        banner.id = 'missing-passengers-banner';
        banner.className = 'missing-passengers-banner';
        banner.innerHTML = `
            <style>
                .missing-passengers-banner {
                    background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
                    border-radius: 16px;
                    padding: 20px 24px;
                    margin-bottom: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    color: white;
                    position: relative;
                    box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
                    animation: slideIn 0.4s ease;
                }

                @keyframes slideIn {
                    from {
                        transform: translateY(-20px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }

                .missing-passengers-banner.hidden {
                    display: none;
                }

                .banner-content-mp {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    flex: 1;
                }

                .banner-icon-text {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .banner-icon-mp {
                    width: 24px;
                    height: 24px;
                    flex-shrink: 0;
                }

                .banner-title-mp {
                    font-size: 1.125rem;
                    font-weight: 600;
                    margin: 0;
                }

                .banner-text-mp {
                    font-size: 1rem;
                    opacity: 0.95;
                    margin: 0;
                }

                .banner-actions-mp {
                    display: flex;
                    gap: 12px;
                    align-items: center;
                }

                .btn-add-passengers {
                    background: white;
                    color: #FF6B6B;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }

                .btn-add-passengers:hover {
                    background: #f5f5f5;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }

                .btn-dismiss-mp {
                    background: rgba(255,255,255,0.2);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .btn-dismiss-mp:hover {
                    background: rgba(255,255,255,0.3);
                }

                .banner-close-mp {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    font-size: 24px;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                    margin-left: 16px;
                }

                .banner-close-mp:hover {
                    background: rgba(255,255,255,0.3);
                    transform: scale(1.1);
                }

                @media (max-width: 600px) {
                    .missing-passengers-banner {
                        flex-direction: column;
                        align-items: stretch;
                        gap: 16px;
                    }

                    .banner-actions-mp {
                        flex-direction: column;
                        width: 100%;
                    }

                    .btn-add-passengers,
                    .btn-dismiss-mp {
                        width: 100%;
                    }

                    .banner-close-mp {
                        position: absolute;
                        top: 12px;
                        right: 12px;
                        margin: 0;
                    }
                }
            </style>
            <div class="banner-content-mp">
                <div class="banner-icon-text">
                    <svg class="banner-icon-mp" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
                    </svg>
                    <h3 class="banner-title-mp">Falta información de ${data.field_name}</h3>
                </div>
                <p class="banner-text-mp">${data.suggestion}</p>
            </div>
            <div class="banner-actions-mp">
                <button class="btn-add-passengers" onclick="editViajeFromBanner(${data.viaje_id})">
                    Agregar ${data.field_name}
                </button>
                <button class="btn-dismiss-mp" onclick="dismissPassengersBanner()">
                    Ahora no
                </button>
            </div>
            <button class="banner-close-mp" onclick="dismissPassengersBanner()">×</button>
        `;

        // Insertar antes del primer .viajes-section si existe
        const viajesSection = document.querySelector('.viajes-section');
        if (viajesSection) {
            viajesSection.parentNode.insertBefore(banner, viajesSection);
        } else {
            // Fallback: insertar después del header
            const container = document.querySelector('.container');
            if (container && container.firstChild) {
                container.insertBefore(banner, container.firstChild.nextSibling);
            }
        }

        // Auto-ocultar después de 30 segundos si no hay interacción
        setTimeout(() => {
            const bannerEl = document.getElementById('missing-passengers-banner');
            if (bannerEl) {
                bannerEl.style.opacity = '0';
                bannerEl.style.transform = 'translateY(-20px)';
                setTimeout(() => bannerEl.remove(), 300);
            }
        }, 30000);
    }

    window.dismissPassengersBanner = function() {
        const banner = document.getElementById('missing-passengers-banner');
        if (banner) {
            banner.style.opacity = '0';
            banner.style.transform = 'translateY(-20px)';
            setTimeout(() => banner.remove(), 300);
        }
    };

    window.editViajeFromBanner = function(viajeId) {
        // Cerrar banner
        dismissPassengersBanner();

        // Abrir modal de edición (asumiendo que hay una función global)
        if (typeof window.editarViaje === 'function') {
            window.editarViaje(viajeId);
        } else {
            // Fallback: navegar a página de edición si existe
            window.location.href = `/editar/${viajeId}`;
        }
    };

    console.log('[Missing Passengers] Module loaded');
})();
