# 🗺️ ROADMAP - Mi Agente Viajes

**Última actualización:** 9 Diciembre 2025
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

### Dominio y Email Propio

**Estado actual:** misviajes@gamberg.com.ar
**Decisión pendiente:** ¿Cuándo migrar a dominio propio?

| Opción | Pros | Contras |
|--------|------|---------|
| **Migrar ahora** | Branding limpio desde el inicio | Costo, complejidad, aún no sabemos el nombre final |
| **Migrar con usuarios pagos** | Justifica inversión | Más trabajo de migración después |
| **Migrar con nombre final** | Un solo cambio | Retrasa el branding profesional |

**Recomendación:** Migrar cuando tengamos nombre final definido. Mientras tanto, gamberg.com.ar funciona para beta.

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

## 🔥 URGENTE - Bugs en Producción

### 🔴 Calendar feed muestra viajes de TODOS los usuarios
**Reportado por:** Beta user (Pancho)
**Problema:** El feed `/calendar-feed` no filtra por usuario, todos ven todos los viajes
**Impacto:** Privacidad - usuarios ven viajes ajenos en su calendario
**Solución:** Feed con token único por usuario (`/calendar-feed/<token>`)

---

## 🔄 En Progreso / Próximos

### MVP9: Calendar Feed Privado (URGENTE)
**Problema:** Feed actual muestra todos los viajes de todos los usuarios
**Solución:**
- Generar token único por usuario (UUID en tabla User)
- Nuevo endpoint: `/calendar-feed/<token>`
- Solo muestra viajes del usuario dueño del token
- Actualizar UI para mostrar URL personalizada

**Implementación:**
```python
# En User model
calendar_token = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

# Nuevo endpoint
@app.route('/calendar-feed/<token>')
def calendar_feed_user(token):
    user = User.query.filter_by(calendar_token=token).first_or_404()
    viajes = get_viajes_for_user(user)
    # ... generar ical solo con estos viajes
```

### MVP10: Calendario All-Day
**Evento multi-día para viajes completos:**
- Crear evento que abarca desde primer vuelo hasta último
- Aparece como barra en parte superior del calendario
- Nombre: "Viaje a [Ciudad Principal]"
- Además de los eventos individuales de cada vuelo

### MVP11: Deduplicación Inteligente
**Problema:** Mismo vuelo en distintas reservas aparece duplicado.
**Ejemplo:** Familia viaja junta pero Vero+Sol en una reserva (Business) y Andy en otra (Economy).

**Solución:**
- Detectar vuelos idénticos: mismo número + fecha + ruta
- Consolidar en UN solo card con todos los pasajeros
- Cada pasajero muestra: nombre, código reserva, asiento, clase

### MVP12: Onboarding Primera Vez
- Modal de bienvenida con 3 pasos
- Recordar suscribirse al calendario (con SU link personalizado)
- Guiar a completar perfil (nombre_pax/apellido_pax)
- Explicar cómo reenviar emails

### MVP13: Notificaciones Email
- Email cuando se detecta cambio en vuelo (delay, gate, cancelación)
- Resumen diario/semanal de viajes próximos
- Push notifications (requiere PWA)

### MVP14: Gmail/Outlook Integration
**Problema:** Si aerolínea cambia número de vuelo, FR24 pierde tracking. Usuario recibe email pero tiene que reenviar manualmente.

**Solución:** Conectar inbox del usuario (OAuth) para auto-detectar emails de aerolíneas.

| Aspecto | Gmail API | Microsoft Graph | Apple (iCloud) |
|---------|-----------|-----------------|----------------|
| **Complejidad** | Media | Media | Alta |
| **OAuth** | Bien documentado | Bien documentado | Complejo |
| **Costo** | Gratis | Gratis | Gratis pero limitado |

**Consideraciones de privacidad:**
- Solo leer emails de remitentes conocidos (aerolíneas, booking, etc)
- Mostrar al usuario exactamente qué procesamos
- Siempre mantener opción manual como alternativa
- Revocable en cualquier momento

**Fases:**
1. Solo Gmail (80% de usuarios argentinos)
2. Agregar Outlook/Hotmail
3. Evaluar Apple si hay demanda

**Alternativa:** Seguir investigando APIs de aerolíneas por PNR (intentamos y falló, pero puede haber opciones).

### MVP15: Compartir Viajes
- Tab "Compartidos" separado de "Mis Viajes"
- Invitar usuarios por email
- Rol "asistente" que puede cargar viajes para otros
- Útil para: secretarias, agentes de viaje, familias

### MVP16: Backoffice / Admin
**Necesidad:** Ver usuarios y datos sin acceder a BD directamente

**Features básicos:**
- Lista de usuarios (email, nombre, fecha registro, # viajes)
- Ver viajes de un usuario específico
- Estadísticas: usuarios activos, viajes cargados, emails procesados
- Protegido con rol admin

**Features avanzados (futuro):**
- Impersonar usuario (para debugging)
- Enviar email a usuarios
- Desactivar/activar usuarios
- Logs de actividad

---

## 🔒 Preparación para Escalar (Pre-requisitos)

### Auditoría de Seguridad
- [ ] Review de autenticación (tokens, sesiones)
- [ ] Validación de inputs (SQL injection, XSS)
- [ ] Rate limiting en endpoints públicos
- [ ] Secrets management (no hardcodeados)
- [ ] HTTPS everywhere (ya OK en Cloud Run)
- [ ] Backup automático de BD

### Review de Performance
- [ ] Índices en BD (user_id, fecha_salida, grupo_viaje)
- [ ] Query optimization (N+1 queries)
- [ ] Caching donde corresponda
- [ ] Lazy loading de datos pesados
- [ ] Monitoreo de tiempos de respuesta

### Escalabilidad de BD - Viajes Pasados
**Problema:** BD crece indefinidamente con viajes históricos
**Opciones:**
- Archivar viajes >1 año a tabla `viajes_archivo`
- Soft delete con flag `archivado`
- Paginación obligatoria en queries
- Cold storage para históricos (exportar a JSON/S3)

### Requisitos App Store (iOS/Android)
- [ ] PWA compliant
- [ ] Icons en todos los tamaños
- [ ] Splash screens
- [ ] Offline básico
- [ ] Privacy policy
- [ ] Terms of service

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

---

## 🔗 Links Útiles

- **App:** https://mi-agente-viajes-454542398872.us-east1.run.app
- **Repo:** https://github.com/andygamberg/mi-agente-viajes
- **Calendar Feed:** (ahora será por usuario con token)
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
| 9 Dic 2025 | Calendar feed por usuario | Bug de privacidad reportado por beta user |
| 9 Dic 2025 | Gmail/Outlook integration | Solución a limitación de FR24 con cambios de vuelo |
| 9 Dic 2025 | Backoffice admin | Necesario para gestionar usuarios sin BD directa |
