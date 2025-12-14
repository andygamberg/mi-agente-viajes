# 🗺️ ROADMAP - Mi Agente Viajes

**Última actualización:** 15 Diciembre 2025

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

---

## 🏗️ Refactor Arquitectónico: Modelo de Eventos

### Contexto

La app comenzó como gestor de vuelos pero la visión es más amplia: viajes completos (vuelos + hoteles + autos), reservas (restaurantes, espectáculos), citas (médicas, profesionales). El modelo actual (`Viaje`) está limitado a vuelos.

### Decisión de arquitectura (11 Dic 2025)

**Opción elegida: Modelo Híbrido (Base + Extensiones)**

Después de analizar UX y performance, elegimos arquitectura híbrida:

```
Evento (tabla base)
├── Campos comunes: titulo, fecha_inicio, fecha_fin, lugar, codigo_reserva, trip_id
├── tipo: vuelo | hotel | restaurante | auto | cita | actividad
│
├── DetalleVuelo (extensión 1:1)
│   └── numero_vuelo, aerolinea, origen, destino, pasajeros, terminal...
├── DetalleHotel (extensión 1:1)
│   └── nombre_hotel, habitacion, check_in_hora, huespedes...
├── DetalleRestaurante (extensión 1:1)
│   └── num_personas, tipo_cocina, preferencias...
└── DetalleCita (extensión 1:1)
    └── profesional, especialidad, institucion...
```

### Por qué esta arquitectura

| Criterio | Beneficio |
|----------|-----------|
| UX Timeline | Una query para listado cronológico mixto |
| UX Detalle | Campos tipados con validación por tipo |
| UX Agrupación | `trip_id` agrupa vuelo+hotel+restaurante en un "viaje" |
| Performance | Índices en tabla base, JOINs solo al expandir detalle |
| Extensibilidad | Nuevo tipo = nueva tabla extensión + componente UI |
| Migración | Gradual, sin romper funcionalidad existente |

### MVP-REF: Plan de migración

| Fase | Descripción | Riesgo |
|------|-------------|--------|
| REF-1 | Crear tablas nuevas (Evento, DetalleVuelo) en paralelo | Bajo |
| REF-2 | Script migración: Viaje → Evento + DetalleVuelo | Medio |
| REF-3 | Actualizar blueprints para usar nuevo modelo | Medio |
| REF-4 | Actualizar templates y calendar feed | Bajo |
| REF-5 | Período de coexistencia, validar datos | Bajo |
| REF-6 | Deprecar y eliminar tabla Viaje | Bajo |

### Tipos de eventos planificados

| Tipo | MVP | Campos específicos | Fuentes típicas |
|------|-----|-------------------|-----------------|
| Vuelo | ✅ Ya existe | numero_vuelo, aerolinea, origen, destino, pasajeros, terminal, puerta | Aerolíneas, Despegar, Almundo |
| Hotel | Futuro | nombre_hotel, habitacion, check_in/out, huespedes, amenities | Booking, Airbnb, Hotels.com |
| Auto | Futuro | empresa, modelo, pickup, dropoff, ubicaciones | Hertz, Avis, Localiza |
| Restaurante | Futuro | num_personas, tipo_cocina, preferencias, ocasion | OpenTable, TheFork, email directo |
| Espectáculo | Futuro | venue, asientos, sector | Ticketmaster, Eventbrite, AllAccess |
| Cita médica | Futuro | profesional, especialidad, institucion, motivo | Swiss Medical, OSDE, consultorios |
| Actividad | Futuro | proveedor, tipo_actividad, participantes | Civitatis, GetYourGuide, operadores |

---

## 📋 Próximos MVPs

### Prioridad Alta

| MVP | Descripción | Dependencias |
|-----|-------------|--------------|
| **14-EXT** | Claude detecta hoteles, restaurantes, citas (no solo vuelos) | - |
| **MVP-REF** | Refactor BD: Viaje → Evento + extensiones | 14-EXT |

### Prioridad Media

| MVP | Descripción | Dependencias |
|-----|-------------|--------------|
| **14i/14j** | Guías in-app para Apple Mail y Outlook app | 14-UX |
| **MVP13b** | Envío de notificaciones (email cuando FR24 detecta cambio) | - |
| **MVP15** | Compartir viajes (tab "Compartidos", invitar por email) | MVP-REF |
| **MVP-HOTEL** | Soporte completo para hoteles | MVP-REF |

### Prioridad Baja

| MVP | Descripción | Dependencias |
|-----|-------------|--------------|
| **MVP16** | Backoffice admin (usuarios, stats) | - |
| **MVP-REST** | Soporte para restaurantes | MVP-REF |
| **MVP-CITA** | Soporte para citas médicas | MVP-REF |

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

---

*Última actualización: 15 Dic 2025*

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
