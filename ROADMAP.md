# 🗺️ ROADMAP - Mi Agente Viajes

**Última actualización:** 8 Diciembre 2025
**Versión actual:** MVP8

---

## 🎯 Visión del Producto

### Visión Actual
Reemplazo moderno de TripCase: sistema inteligente de gestión de viajes con carga automática, sincronización de calendario, y monitoreo de vuelos en tiempo real.

### Visión Expandida (Futuro)
**Asistente personal de reservas y agenda** que va más allá de viajes:
- Reservas de restaurantes
- Citas médicas
- Eventos y espectáculos
- Actividades cotidianas con fecha/hora/lugar

Un viaje puede no incluir vuelos (solo hotel + actividades). Una reserva puede no ser parte de un viaje (cena del martes).

**Usuarios actuales:** Familia y amigos (beta privada)
**Objetivo próximo:** Validar producto antes de escalar

---

## 🏷️ Rebranding & Naming (Futuro)

### Problema
"Mis Viajes" es limitante: no cubre restaurantes, citas, eventos cotidianos.

### Requisitos de Naming
- **Multi-idioma:** Debe funcionar en ES/EN/PT mínimo
- **Expandible:** No limitado a "viajes" o "vuelos"
- **Memorable:** Fácil de pronunciar en cualquier idioma
- **Disponible:** Dominio .com y App Store

### Opciones a Explorar

| Nombre | Pros | Contras |
|--------|------|---------|
| **Agenda** | Universal (ES/EN/PT similar) | Genérico, mucha competencia |
| **Planr** | Moderno, corto, multi-idioma | Difícil de pronunciar en ES |
| **Itinero** | Latín (universal), elegante | Puede sonar a "itinerario" solo |
| **Reserva** | Claro en ES/PT, "Reserve" EN | Limitado a reservas |
| **Trippa** | Suena amigable, memorable | Puede confundirse con "trip" |
| **Mova** | Corto, moderno, movimiento | Sin significado claro |
| **Plana** | Plan + a, funciona multi-idioma | Puede sonar a "plana/flat" |

### Proceso de Decisión
1. Validar producto actual con usuarios
2. Definir scope final (¿solo viajes? ¿vida completa?)
3. Research de nombres disponibles (dominio + stores)
4. Testing con usuarios en 3 idiomas
5. Decisión final pre-scale

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

---

## 🔄 En Progreso / Próximos

### UX Sprint (Prioridad Alta)
- [x] Login con tagline
- [x] Perfil con explicación y ejemplos
- [x] Header mobile unificado (hamburguesa)
- [x] Botones calendario separados (Apple/Google)
- [ ] **Header web = Header mobile** (consistencia total)
- [ ] **Onboarding primera vez**
  - Recordar suscribirse al calendario
  - Guiar a completar perfil (nombre_pax/apellido_pax)
  - Explicar cómo reenviar emails

- [ ] **Bugs conocidos**
  - Viajes pasados no despliegan al hacer click

### MVP9: Deduplicación Inteligente (Prioridad Alta)
**Problema:** Mismo vuelo en distintas reservas aparece duplicado.
**Ejemplo:** Familia viaja junta pero Vero+Sol en una reserva (Business) y Andy en otra (Economy).

**Solución:**
- Detectar vuelos idénticos: mismo número + fecha + ruta
- Consolidar en UN solo card con todos los pasajeros
- Cada pasajero muestra: nombre, código reserva, asiento, clase
- Calendario: UN evento con descripción consolidada

**Lógica de merge:**
```
Si vuelo.numero_vuelo == otro.numero_vuelo
   AND vuelo.fecha_salida == otro.fecha_salida
   AND vuelo.origen == otro.origen
   AND vuelo.destino == otro.destino
→ Merge pasajeros en un solo registro
```

### MVP10: Notificaciones (Prioridad Media)
- [ ] Email cuando se detecta cambio en vuelo (delay, gate, cancelación)
- [ ] Resumen diario/semanal de viajes próximos
- [ ] Push notifications (requiere PWA)

### MVP11: Compartir Viajes (Prioridad Media)
- [ ] Tab "Compartidos" separado de "Mis Viajes"
- [ ] Invitar usuarios por email
- [ ] Rol "asistente" que puede cargar viajes para otros
- [ ] Útil para: secretarias, agentes de viaje, familias

---

## 📋 Backlog (Prioridad Baja)

### Tipos de Reserva (Expandir más allá de vuelos)

| Tipo | Campos específicos | Icono |
|------|-------------------|-------|
| ✈️ Vuelo | Aerolínea, número, terminal, gate, asiento | Ya existe |
| 🏨 Hotel | Nombre, dirección, check-in/out, # habitación | Pendiente |
| 🚗 Auto | Empresa, pickup/dropoff location, # reserva | Pendiente |
| 🚂 Tren | Operador, estación, vagón, asiento | Pendiente |
| 🚢 Barco/Crucero | Naviera, puerto, cabina | Pendiente |
| 🍽️ Restaurante | Nombre, dirección, hora, # personas | Pendiente |
| 📍 Actividad | Nombre, ubicación, duración, tickets | Pendiente |
| 🏥 Cita médica | Doctor, clínica, dirección | Futuro |
| 🎭 Evento | Nombre, venue, asientos | Futuro |

**Implementación:**
- Campo `tipo` ya existe, expandir opciones
- Campos dinámicos según tipo seleccionado
- Claude auto-detecta tipo en PDF/email
- Cards con diseño adaptado por tipo
- Calendario con iconos/colores por tipo

### Métricas y Dashboard
**Actual:** Solo cuenta vuelos
**Futuro:** Dashboard con:
- Total reservas por tipo
- Próximas 7 días (todas las reservas)
- Estadísticas: ciudades visitadas, aerolíneas usadas, etc.
- Un viaje puede tener 0 vuelos (solo hotel + actividades)

### Mejoras de Carga
- [ ] Autocomplete aerolíneas (como origen/destino IATA)
- [ ] Opción "Otro/Privado" para vuelos charter
- [ ] Escanear pasaporte con cámara (Claude Vision)
- [ ] Compartir itinerario por WhatsApp (info no sensible)

### UI/UX
- [ ] Dark mode
- [ ] Placeholders genéricos (Juan Pérez, no nombres reales)
- [ ] Rediseño visual más moderno

### Multi-idioma
- [ ] Español (default)
- [ ] English
- [ ] Português
- [ ] Infraestructura i18n (flask-babel o similar)
- [ ] Detección automática por browser

---

## 🏗️ Arquitectura Actual

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud Run                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │                 Flask App                        │    │
│  │  • Auth (Flask-Login)                           │    │
│  │  • PDF extraction (Claude API)                  │    │
│  │  • Email processing (Gmail API)                 │    │
│  │  • Flight monitoring (FR24 API)                 │    │
│  │  • Calendar feed (iCal)                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
    ┌─────────────┐              ┌─────────────────┐
    │ Cloud SQL   │              │ Cloud Scheduler │
    │ PostgreSQL  │              │ (cada 15 min)   │
    └─────────────┘              └─────────────────┘
```

**Costos actuales:** ~$19/mes
- Cloud SQL: ~$10
- FR24 API: $9
- Cloud Run: $0 (free tier)

---

## 🔧 Deuda Técnica

### Refactor Nomenclatura (CRÍTICO para escalar)
**Problema actual:**
- Modelo `Viaje` = en realidad es un SEGMENTO/VUELO
- `grupo_viaje` = lo que el usuario ve como "Viaje"

**Solución propuesta:**
```
Trip (Viaje/Reserva)
├── id, nombre, user_id, tipo_general
└── tiene muchos → Segments

Segment (Segmento individual)
├── id, trip_id
├── tipo (vuelo, hotel, auto, restaurante, etc)
├── campos específicos por tipo
```

### Otros
- [ ] Archivar viajes pasados >1 año (optimización BD)
- [ ] Tests automatizados (pytest)
- [ ] CI/CD con GitHub Actions
- [ ] Migrar emails a SendGrid/Mailgun (métricas, templates)

---

## 📊 Métricas a Trackear (Futuro)

- Usuarios registrados
- Reservas cargadas por método (email vs PDF vs manual)
- Reservas por tipo (vuelo, hotel, restaurante, etc)
- Emails procesados exitosamente
- Cambios de vuelo detectados
- Usuarios activos semanales

---

## 💰 Modelo de Negocio (Ideas)

**Pendiente definir.** Opciones a explorar:

| Modelo | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| Freemium | Gratis hasta X reservas/mes | Fácil adopción | Necesita volumen |
| B2B | Vender a agencias de viaje | Ticket alto | Ciclo venta largo |
| White-label | Licenciar a empresas | Recurrente | Soporte complejo |
| Comisiones | Afiliados con booking/hotels | Pasivo | Depende de terceros |

**Próximo paso:** Validar con 10-20 usuarios beta antes de definir modelo.

---

## 🔗 Links Útiles

- **App:** https://mi-agente-viajes-454542398872.us-east1.run.app
- **Repo:** https://github.com/andygamberg/mi-agente-viajes
- **Calendar Feed:** https://mi-agente-viajes-454542398872.us-east1.run.app/calendar-feed
- **Email para reenvíos:** misviajes@gamberg.com.ar

---

## 📝 Historial de Decisiones

| Fecha | Decisión | Contexto |
|-------|----------|----------|
| Nov 2025 | Flask sobre Django | Simplicidad para MVP |
| Nov 2025 | Claude API sobre GPT | Mejor extracción de PDFs |
| Dic 2025 | FR24 sobre FlightAware | Mejor precio, SDK oficial |
| Dic 2025 | Gmail API sobre SendGrid | Ya teníamos dominio configurado |
| 8 Dic 2025 | Gmail send para emails | MVP suficiente, migrar después |
| 8 Dic 2025 | Visión expandida | Más allá de vuelos: reservas + agenda |
| 8 Dic 2025 | Naming multi-idioma | Preparar para escala global |
