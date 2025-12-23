# 🗺️ ROADMAP - Mi Agente Viajes

**Última actualización:** 23 Diciembre 2025

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
| 14-UX | Unificación emails en perfil | 12 Dic 2025 | Toggle visual, detección proveedor, deduplicación |
| **14h** | **Microsoft OAuth** | **12 Dic 2025** | **Outlook, Hotmail, Exchange 365, corporativos** |
| 15 | Onboarding post-registro | 14 Dic 2025 | Pantalla bienvenida con OAuth + nombre pax |
| 15-UX | Template inheritance (base.html) | 14 Dic 2025 | Menú global, reducción código duplicado |
| **15** | **Multi-Tipo de Reservas** | **15 Dic 2025** | **9 tipos: vuelos, hoteles, barcos, shows, restaurantes, actividades, autos, trenes, transfers** |
| BUG-FIX-MULTITYPE | Multi-tipo en Sistema 1 (misviajes@) | 15 Dic 2025 | gmail_to_db.py ahora soporta 9 tipos, replica lógica de carga_rapida() |
| **MVP-EDIT** | **Edición completa de reservas** | **14 Dic 2025** | **Form dinámico desde schemas, menú kebab, vuelos combinados, todos los tipos** |
| **MVP16** | **Carga manual multi-tipo** | **14 Dic 2025** | **/agregar refactorizado con schemas dinámicos, selector tipo, 9 tipos soportados** |
| 26 | UX Mobile + Formato hora | 17 Dic 2025 | Tipografía rem, capitalización, formato hora 24h/12h |
| **27** | **Unificación Preferencias + Merge reservas** | **21 Dic 2025** | **Perfil→Preferencias, merge asientos/actualizaciones, Outlook Calendar** |
| **28** | **DEMO-TRIP + Onboarding UX** | **22 Dic 2025** | **Viaje ejemplo, tips calendario/agrupar, empty state contextual, REDIRECT-SMART** |

### ✅ Completado - Sesión 31 (23 Dic 2025)

#### EMAIL FILTER ENHANCEMENT ✅
- Filtro `email_parece_reserva()` ahora incluye nombres de archivos adjuntos
- Emails con PDFs nombrados "Reserva de viaje..." ya no son descartados
- Implementado en: gmail_webhook.py, gmail_scanner.py, microsoft_scanner.py

#### OAUTH FIXES ✅
- Microsoft: Fix token refresh (token_expiry siempre era NULL)
- Gmail: Auto-renovación de watches expirados (cada 7 días)
- Integrado en cron check-flights

#### OAUTH EXPIRATION WARNING ✅
- Sistema proactivo de avisos para conexiones Microsoft por expirar
- Detecta 60+ días de inactividad (antes de 90 días de expiración)
- Envía email al usuario con instrucciones para reconectar
- Cooldown de 7 días entre avisos (evita spam)
- Nueva columna: `email_connection.last_expiry_warning`

#### DEDUPLICATION FIX ✅
- Vuelos ida/vuelta ya no se sobreescriben entre sí
- Campos inmutables en merge: numero_vuelo, origen, destino, fecha_salida, hora_salida

#### MOBILE-TYPOGRAPHY v4 ✅
- Tipografía mínima aumentada a 20px (1.25rem)
- Para legibilidad con presbicia (+45 años) sin anteojos
- Todos los templates actualizados

### ✅ Completado - Sesión 30 (22 Dic 2025)

#### DEMO-TRIP ✅
- Viaje de ejemplo para nuevos usuarios (no se guarda en BD)
- Fechas dinámicas: 27 días en futuro
- Se oculta cuando usuario tiene viajes reales

#### ONBOARDING TIPS ✅
- Tip calendario post-primer-viaje (session-based, una vez)
- Tip agrupar viajes con 2+ viajes (session-based, una vez)
- Lógica de prioridad: calendar_tip primero, group_tip después

#### EMPTY STATE CONTEXTUAL ✅
- Empty state depende de OAuth conectado (no de cantidad de viajes)
- Muestra opciones de conexión solo si no tiene OAuth

#### REDIRECT-SMART ✅
- Todos los redirects post-guardado incluyen `highlight=grupo_id`
- Viaje recién creado se destaca visualmente

#### UI-POLISH (8 bugs resueltos) ✅
- Fix wizard bienvenida (block names, script tags)
- Calendar links abren en nueva pestaña
- Forms anidados en preferencias separados
- Emails duplicados removidos
- Botón + duplicado removido del header
- Logo unificado (1.25rem)
- Hint formato hora para usuarios 12h

### ✅ Completado - Sesión 29 (21 Dic 2025)

#### UNIFICACIÓN PREFERENCIAS ✅
- Rename: Mi Perfil → Preferencias (template, rutas, menú)
- Redirect legacy /perfil → /preferencias

#### OUTLOOK CALENDAR ✅
- Botón en preferencias y menú
- Wizard post-conexión Microsoft incluye Outlook Calendar

#### MERGE DE RESERVAS ✅
- Actualización incremental de reservas existentes
- Sobreescribe TODOS los campos con nuevos valores (excepto tipo, codigo_reserva)
- Merge inteligente de pasajeros (actualiza existentes, agrega nuevos)
- 4 flujos unificados: Gmail push, Gmail cron, Microsoft, misviajes@
- Soporta: asientos, terminal, puerta, horarios, equipaje, cualquier campo

#### EXTRACCIÓN MEJORADA ✅
- Prompt Claude distingue fecha emisión vs fecha vuelo
- Extrae ambos vuelos (ida y vuelta) correctamente
- Corrección automática de años pasados/futuros

### ✅ Completado - Sesión 25 (16 Dic 2025)

#### BUG-PASSENGER-MATCH ✅
- Matching extendido a huéspedes/participantes en JSONB
- Nueva función `extraer_personas_de_datos()` en utils/helpers.py
- Casos V3, V4, V5 resueltos

#### TIPO BUS ✅
- Schema completo en config/schemas.py
- Prompt Claude actualizado para extraer buses
- Ícono SVG, display en cards, emoji calendario 🚌
- Deduplicación incluida

#### DEDUPLICACIÓN UNIVERSAL ✅
- Aplica a todos los tipos (no solo vuelos)
- Ordenamiento por fecha+hora
- Combina pasajeros, vehículos, huéspedes
- Ferries cortos (<24h) se deduplicam
- Badge "COMBINADO" para todos los tipos

#### CAMPO SOURCE ✅
- Modelo: `source` VARCHAR(20)
- Valores: manual, pdf_upload, gmail, microsoft, email_forward
- Helper `puede_modificar_segmento()` en utils/permissions.py

#### UX-DELETE ✅
- Eliminar segmento individual (reservas editables)
- Eliminar reserva completa por PNR (vuelos bloqueados)
- Vista readonly para vuelos con PNR automático
- Solo vuelos bloqueados por PNR, otros tipos siempre editables

### ✅ Refactor Arquitectónico (9 Dic 2025)

| Cambio | Antes | Después |
|--------|-------|---------|
| app.py | 1,400 líneas (monolito) | 75 líneas (config + factory) |
| Blueprints | No existían | viajes_bp, calendario_bp, api_bp, gmail_oauth_bp, gmail_webhook_bp |
| Utils | Inline en app.py | utils/iata.py, claude.py, helpers.py, gmail_scanner.py |
| Smoke tests | 9 tests | 10 tests (+ calendar auth) |

---

## 📧 Detalle MVP14: Email Integration

### Estrategia de detección por tiers

| Tier | Método | Proveedores | Automatización |
|------|--------|-------------|----------------|
| 1 | OAuth directo | Gmail ✅, Microsoft 365, Outlook.com | Un click |
| 2 | Regla automática | Microsoft (alternativa), Yahoo | Un click |
| 3 | Reenvío guiado | Apple Mail, Outlook app | Tutorial in-app |
| 4 | Manual | Cualquiera | misviajes@gamberg.com.ar ✅ |

### Sub-MVPs completados

| Sub-MVP | Descripción | Estado |
|---------|-------------|--------|
| 14a | Gmail OAuth multi-cuenta | ✅ |
| 14b | Escaneo manual de emails | ✅ |
| 14c | Push notifications (Pub/Sub) | ✅ |
| 14e | Custom senders por usuario | ✅ |
| 14f | Fix multi-cuenta (.first() bug) | ✅ |
| 14g | Extracción PDFs + deduplicación | ✅ |
| 14-UX | Unificación emails en perfil | ✅ |
| **14h** | **Microsoft Graph OAuth (Exchange/365)** | ✅ |

### Sub-MVPs pendientes

| Sub-MVP | Descripción | Prioridad | Esfuerzo |
|---------|-------------|-----------|----------|
| 14i | Apple Mail guía contextual in-app | Media | 2-3h |
| 14j | Outlook app guía contextual in-app | Media | 1h |
| 14-EXT | Extender Claude para detectar todos los tipos de eventos | Alta | 4h |

**Nota:** Microsoft Graph API soporta tanto cuentas corporativas (Exchange/M365) como personales (@outlook.com, @hotmail.com). Una sola implementación cubre ambos casos.

---

## 🔄 Pendientes Técnicos

### Bugs/UX Issues Identificados

| Issue | Descripción | Prioridad | Estado |
|-------|-------------|-----------|--------|
| ~~Menú hamburguesa~~ | ~~Click en "borrar/agrupar" no da feedback~~ | ~~Media~~ | ✅ Resuelto 11 Dic |
| ~~Onboarding email~~ | ~~Usuario conecta Gmail pero no sabe qué esperar~~ | ~~Alta~~ | ✅ Resuelto 12 Dic (14-UX) |
| ~~Sin feedback conexión~~ | ~~No indica estado de detección automática~~ | ~~Media~~ | ✅ Resuelto 12 Dic (14-UX) |

### Pre-escala / Técnico

| Item | Descripción | Prioridad | Status |
|------|-------------|-----------|--------|
| Google OAuth verification | App en modo testing, límite de usuarios. Verificar para producción | Alta | Pendiente |
| Auditoría seguridad | Review completo de seguridad antes de escalar | Alta | Pendiente |
| Performance review | Optimización para escala (queries, caching, etc.) | Media | Pendiente |
| Impacto BD viajes pasados | Evaluar impacto de vuelos históricos en performance | Media | Pendiente |
| Migración a modelo Eventos | Refactor arquitectónico para soportar hoteles, autos, citas | Baja | Planificado |


## 📋 Próximos MVPs

### Prioridad Alta

| MVP | Descripción | Dependencias |
|-----|-------------|--------------|
| ~~**BUG-PASSENGER-MATCH**~~ | ~~Matching pasajeros extender a 9 tipos (no solo vuelos)~~ | ✅ **15 Dic 2025** |
| ~~**UX-DELETE**~~ | ~~Eliminar segmento individual + reserva completa por PNR~~ | ✅ **16 Dic 2025** |
| ~~**UI-POLISH**~~ | ~~Fix 8 bugs de UI detectados en Sesión 27~~ | ✅ **22 Dic 2025** |
| ~~**REDIRECT-SMART**~~ | ~~Redirect inteligente post-guardado~~ | ✅ **22 Dic 2025** |
| ~~**DEMO-TRIP**~~ | ~~Viaje de ejemplo para nuevos usuarios~~ | ✅ **22 Dic 2025** |
| ~~**MOBILE-TYPOGRAPHY**~~ | ~~Aumentar tipografía a mínimo 20px (presbicia)~~ | ✅ **23 Dic 2025** |
| ~~**SECURITY-CLEANUP**~~ | ~~Eliminar endpoints debug antes de escalar~~ | ✅ **21 Dic 2025** |
| **DATA-MIGRATION** | Normalizar campos legacy (pasajeros int→array) | - |
| **Google OAuth** | Verificar app para salir de modo testing | - |

### Prioridad Media

| MVP | Descripción | Dependencias |
|-----|-------------|--------------|
| ~~**TIPOGRAFÍA MOBILE**~~ | ~~Aumentar tamaño de fuentes, usar rem en vez de px~~ | ✅ **17 Dic 2025** |
| ~~**CAPITALIZACIÓN**~~ | ~~Auto-capitalizar nombres de pasajeros y ciudades~~ | ✅ **17 Dic 2025** |
| ~~**SVG /agregar**~~ | ~~Eliminar círculo decorativo inútil~~ | ✅ **17 Dic 2025** |
| ~~**DEMO-TRIP**~~ | ~~Viaje de ejemplo para usuario nuevo~~ | ✅ **22 Dic 2025** |
| **MVP13b** | Envío de notificaciones (email cuando FR24 detecta cambio) | - |
| **14i/14j** | Guías in-app para Apple Mail y Outlook | - |
| **MVP-SHARE** | Compartir viajes entre usuarios | - |
| **BUG** | Moorings/charter: mejorar extracción de info | - |

## Sesión 27: Auditoría UX/UI + Técnica ✅ (17-18 Dic 2025)

### Benchmark Realizado
- **Flighty** (Apple Design Award 2023): "boringly obvious", info siempre visible, diseño aeroportuario
- **TripIt/Kayak**: email forwarding, auto-merge, alertas más rápidas que aerolíneas
- **Objetivo**: Superar en UX a competencia paid siendo free

### Quick Wins Implementados ✅
- [x] Countdown en cards ("En 3 días")
- [x] Badge "Nueva" en reservas recientes (<24h)
- [x] Badge "Cambió" para actualizaciones FR24
- [x] Menú reorganizado con iconos SVG
- [x] Header unificado (botones transparentes)
- [x] Fix duplicados: PNR + fecha (>90 días = viaje nuevo)

### Bugs de UI Detectados (Pendientes)
| # | Bug | Descripción |
|---|-----|-------------|
| 1 | Tipografía nombre viaje | Muy chico, agrandar |
| 2 | Overflow nombre | Limitar chars para no pisar lápiz editar |
| 3 | Fecha fin viaje | Solo muestra inicio, falta finalización |
| 4 | Vuelos overnight | Falta día de llegada (solo hora no alcanza) |
| 5 | Formato vuelo | Debería ser: Salida [día hora] Terminal / Llegada [día hora] Terminal |
| 6 | Flecha expand | No clickeable, confuso (solo header funciona) |
| 7 | SVG tipo | Muy chico vs countdown |
| 8 | Countdown en pasados | NO debe haber countdown en viajes pasados |

### Must-Haves ANTES de MVP-SHARE

**Críticos (bloquean share):**
- [ ] Fix bugs de UI (lista arriba)
- [ ] Redirect inteligente post-guardado

**Altos (afectan retención):**
- [ ] Trip de demo para usuario nuevo
- [ ] Checklist de setup visible
- [ ] Guías 14i/14j (Apple Mail, Outlook)

**Técnicos pre-escala:**
- [x] ~~Eliminar endpoints debug~~ ✅ 21 Dic 2025
- [ ] Fix pasajeros int → array
- [ ] Google OAuth verification

### Auditoría Técnica - Hallazgos

| Área | Estado | Acción |
|------|--------|--------|
| Endpoints debug | ✅ Eliminados | Completado 21 Dic 2025 |
| Pasajeros legacy | 🟡 Algunos int | Migrar a array |
| Performance matching | 🟡 Escala mal | Optimizar con >100 usuarios |
| Google OAuth | 🟡 Modo testing | Verificar antes de beta público |
| JSONB datos | ✅ Funcionando | OK |
| Blueprints | ✅ Limpio | OK |

### Prioridad Baja

| MVP | Descripción | Dependencias |
|-----|-------------|--------------|
| **MVP-SHARE** | Compartir viajes (jerarquía: todo → viaje → reserva → segmento) | - |
| **MVP16** | Backoffice admin (usuarios, stats) | - |
| **MVP-REF** | Refactor BD: Viaje → Evento + extensiones (si es necesario) | - |

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
| 11 Dic 2025 | Arquitectura híbrida para eventos | Evento base + extensiones por tipo (vuelo, hotel, etc.) |
| 11 Dic 2025 | Estrategia email por tiers | OAuth (Gmail/MS), reglas automáticas, guías, reenvío manual |
| 11 Dic 2025 | Microsoft Graph para corporativo | Una API cubre Exchange 365 y Outlook.com personal |
| 14 Dic 2025 | Menú kebab para acciones | Escalable para Eliminar/Compartir, mobile-friendly, mejor UX |
| 14 Dic 2025 | save_reservation() unificado | Gmail y Microsoft scanner usan misma función, evita duplicación |
| 14 Dic 2025 | Logging con print() en Cloud Run | Gunicorn requiere PYTHONUNBUFFERED + --access-logfile - para visibilidad |
| 15 Dic 2025 | Edición > Extracción perfecta | Perseguir 100% extracción automática es infinito. Mejor: extracción "good enough" + edición por usuario. MVP-EDIT resuelve todos los edge cases de una vez. |
| 15 Dic 2025 | gmail_to_db.py replica carga_rapida() | Dos flujos que hacen lo mismo (guardar reserva) deben usar misma lógica de mapeo de campos |
| 15 Dic 2025 | Passenger matching extendido a datos JSONB | BUG-PASSENGER-MATCH: get_viajes_for_user() ahora busca en pasajeros/huespedes/participantes dentro del campo datos, no solo en columna legacy. Soporta formato dict y string. |
| 16 Dic 2025 | Campo source para tracking de origen | Rastreo de origen (manual, pdf_upload, gmail, microsoft, email_forward) permite control granular de permisos de edición |
| 16 Dic 2025 | Solo vuelos bloqueados por PNR | Hoteles, cruceros, restaurantes siempre editables aunque tengan código de reserva. Solo vuelos se bloquean (aerolíneas envían actualizaciones). |
| 16 Dic 2025 | onclick directo vs event delegation | event.stopPropagation() en menú bloquea delegación. Solución: onclick directo en botones. |
| 16 Dic 2025 | Deduplicación de ferries por ruta+fecha+hora | Nombre de embarcación varía ("Buquebus" vs "Ferry Buquebus"), usar hora_embarque como clave. |

---

*Última actualización: 23 Dic 2025*

## ✅ MVP15: Multi-Tipo de Reservas (15 Dic 2025)

### Backend
- ✅ Whitelist expandida de 60 → 136 dominios (aerolíneas, hoteles, cruceros, actividades, autos, shows, restaurantes)
- ✅ Nuevos campos en BD: `ubicacion`, `proveedor`, `precio`, `raw_data`
- ✅ Guardado dinámico por tipo (9 tipos soportados)
- ✅ Consolidación de múltiples entradas del mismo espectáculo en Claude prompt
- ✅ Fix deduplicación: items no-vuelo usan `(v.id,)` como clave única

### Frontend
- ✅ Íconos SVG monocromo por tipo (design system Apple/B&O)
- ✅ Layout condicional: transporte (origen→destino) vs lugares fijos (proveedor+ubicación)
- ✅ Títulos inteligentes por tipo (hotel → ciudad hotel, barco → destino)
- ✅ Persistencia de nombre editado en todas las funciones (carga_rapida, agrupar, desagrupar)
- ✅ Fix botón Desagrupar: max-height aumentado a 8000px
- ✅ Precio oculto en UI por privacidad

### Calendario iCal
- ✅ 9 tipos con emojis identificadores (✈️ 🏨 ⛵ 🎭 🍽️ 🎯 🚗 🚆 🚕)
- ✅ Eventos all-day para hoteles, autos, cruceros largos (>24h)
- ✅ Horarios reales desde raw_data (hora_embarque/hora_desembarque para ferries)
- ✅ Detalles de entradas en espectáculos (detalles_entradas array)
- ✅ Precio oculto en calendario por privacidad

### Pendientes
- [ ] MVP16: Carga Manual Multi-Tipo (UI para agregar hoteles, restaurantes, etc.)
- [ ] Moorings/charter: mejorar extracción (caso específico)

---

## ✅ Completados (14 Dic 2025)

### MVP14h: Microsoft OAuth + Scanner Automático
- ✅ Microsoft OAuth para cuentas personales (Outlook.com, Hotmail)
- ✅ Microsoft OAuth para cuentas corporativas (Exchange 365)
- ✅ Scanner automático de emails Microsoft con Cloud Scheduler (cada 15 min)
- ✅ Backfill en primera conexión (180 días, solo vuelos futuros)
- ✅ Detección automática de alias corporativos (mismo dominio = conectado)
- ✅ Setup local con Claude Code (alternativa a Codespaces sin límites de billing)
- ✅ Fix campo descripcion NOT NULL que causaba rollbacks silenciosos

---
