git add -A && git commit -m "MVP14 completo: multi-cuenta, PDFs, deduplicación, UX preferencias"
git push# 🗺️ ROADMAP - Mi Agente Viajes

## 📊 Visión del Producto

**Problema original:** TripCase (app de gestión de viajes) fue discontinuado.

**Visión actual:** Sistema personal de organización que va más allá de viajes:
- Viajes (vuelos, hoteles, autos)
- Reservas (restaurantes, espectáculos)
- Citas (médicas, profesionales)
- Agenda personal inteligente

**Diferenciador:** IA que extrae automáticamente información de emails/PDFs y la organiza.

---

## ✅ MVPs Completados

| MVP | Descripción | Fecha | Notas |
|-----|-------------|-------|-------|
| 1 | Core app + carga manual | Nov 2025 | Flask + PostgreSQL |
| 2 | Extracción de PDFs con Claude | Nov 2025 | Claude API |
| 3 | Sincronización calendario | Nov 2025 | Webcal feed para Apple Calendar |
| 4 | Monitoreo de vuelos | Dic 2025 | Flightradar24 API ($9/mes) |
| 5 | Email automation | Dic 2025 | Gmail API, misviajes@gamberg.com.ar |
| 6 | Multi-usuario | 7 Dic 2025 | Auth, login, registro |
| 7 | Viajes por pasajero | 8 Dic 2025 | Usuario ve viajes donde es pasajero |
| 8 | Recuperar contraseña | 8 Dic 2025 | Email con link seguro |
| 9 | Calendar feed privado | 9 Dic 2025 | Token único por usuario, fix privacidad |
| 10 | Calendario all-day | 9 Dic 2025 | Eventos multi-día para viajes |
| 11 | Deduplicación inteligente | 10 Dic 2025 | Combina vuelos idénticos de distintas reservas |
| 12 | Onboarding UX | 10 Dic 2025 | Empty state educativo, Design System, SVG icons |
| 13 | Preferencias notificaciones | 10 Dic 2025 | UI toggles, campos BD (envío pendiente MVP13b) |
| **14** | **Gmail Push + Multi-cuenta** | **11 Dic 2025** | **OAuth, push notifications, PDFs, deduplicación** |

### Detalle MVP14 (Completado 11 Dic 2025)

| Sub-MVP | Descripción | Estado |
|---------|-------------|--------|
| 14a | Gmail OAuth multi-cuenta | ✅ |
| 14b | Escaneo manual de emails | ✅ |
| 14c | Push notifications (Pub/Sub) | ✅ |
| 14d | Microsoft/Outlook | ⏳ Futuro |
| 14e | Custom senders por usuario | ✅ |
| 14f | Fix multi-cuenta (.first() bug) | ✅ |
| 14g | Extracción PDFs + deduplicación por contenido | ✅ |

### ✅ Refactor Arquitectónico (9 Dic 2025)

| Cambio | Antes | Después |
|--------|-------|---------|
| app.py | 1,400 líneas (monolito) | 75 líneas (config + factory) |
| Blueprints | No existían | viajes_bp, calendario_bp, api_bp, gmail_oauth_bp, gmail_webhook_bp |
| Utils | Inline en app.py | utils/iata.py, claude.py, helpers.py, gmail_scanner.py |
| Smoke tests | 9 tests | 10 tests (+ calendar auth) |

---

## 🔄 Pendientes Técnicos

### Bugs/UX Issues Identificados

| Issue | Descripción | Prioridad |
|-------|-------------|-----------|
| Menú hamburguesa | Click en "borrar/agrupar" no da feedback hasta seleccionar | Media |
| Calendar duplicados | Eventos calendario muestran duplicados en vez de combinados | Media |
| Frequent flyer | Info extraída pero no se muestra en UI | Baja |
| Tooltips | Posicionamiento puede mejorar | Baja |

---

## 📋 Próximos MVPs

### MVP15: Compartir Viajes
- Tab "Compartidos" separado de "Mis Viajes"
- Invitar usuarios por email
- Rol "asistente" que puede cargar viajes para otros

### MVP13b: Envío de Notificaciones
- Enviar email cuando FR24 detecta cambio (delay, gate, cancelación)
- Usar preferencias ya guardadas en BD
- Resumen diario/semanal (opcional)

### MVP16: Backoffice / Admin
- Lista de usuarios (email, nombre, fecha registro, # viajes)
- Ver viajes de un usuario específico
- Estadísticas: usuarios activos, viajes cargados, emails procesados

---

## 🔒 Pre-requisitos para Escalar

### OAuth Google - Verificación
| Item | Estado | Notas |
|------|--------|-------|
| App en producción | ✅ | Ya publicada |
| Límite 100 usuarios | ⚠️ | Requiere verificación para superar |
| Política de Privacidad | ❌ | Crear página /privacy |
| Términos de Servicio | ❌ | Crear página /terms |
| Verificación Google | ❌ | Proceso de ~2 semanas |

### Seguridad
- [ ] Review de autenticación (tokens, sesiones)
- [ ] Validación de inputs (SQL injection, XSS)
- [ ] Rate limiting en endpoints públicos
- [ ] Secrets en env vars (no hardcodeados) ✅
- [ ] Backup automático de BD

### Performance
- [ ] Índices en BD (user_id, fecha_salida)
- [ ] Query optimization
- [ ] Caching donde corresponda

---

## 💰 Modelo de Negocio (Futuro)

| Modelo | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| Freemium | Gratis hasta X reservas/mes | Fácil adopción | Necesita volumen |
| B2B | Vender a agencias de viaje | Ticket alto | Ciclo venta largo |
| White-label | Licenciar a empresas | Recurrente | Soporte complejo |

---

## 🔗 Links Útiles

- **App:** https://mi-agente-viajes-454542398872.us-east1.run.app
- **Repo:** https://github.com/andygamberg/mi-agente-viajes
- **Calendar Feed:** `/calendar-feed/<token>` (token personal en Perfil)
- **Email para reenvíos:** misviajes@gamberg.com.ar

---

## 📝 Historial de Decisiones

| Fecha | Decisión | Contexto |
|-------|----------|----------|
| Nov 2025 | Flask sobre Django | Simplicidad para MVP |
| Nov 2025 | Claude API sobre GPT | Mejor extracción de PDFs |
| Dic 2025 | FR24 sobre FlightAware | Mejor precio, SDK oficial |
| 8 Dic 2025 | Visión expandida | Más allá de vuelos: reservas + agenda |
| 9 Dic 2025 | Refactor a blueprints | app.py de 1400 líneas insostenible |
| 11 Dic 2025 | OAuth manual (requests) | Bypass scope validation de google-auth |
| 11 Dic 2025 | Multi-cuenta Gmail | Usuarios con varias cuentas personales/trabajo |
| 11 Dic 2025 | Extracción de PDFs adjuntos | Emails de agencias tienen info en PDF, no body |
| 11 Dic 2025 | Deduplicación por contenido | Fallback cuando no hay código de reserva |

---

*Última actualización: 11 Dic 2025 - MVP14 completado (14a-14g)*
