# 🗺️ ROADMAP - Mi Agente Viajes

**Última actualización:** 8 Diciembre 2025
**Versión actual:** MVP8

---

## 🎯 Visión del Producto

Reemplazo moderno de TripCase: sistema inteligente de gestión de viajes con carga automática, sincronización de calendario, y monitoreo de vuelos en tiempo real.

**Usuarios actuales:** Familia y amigos (beta privada)
**Objetivo próximo:** Validar producto antes de escalar

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

### UX Sprint (Prioridad Alta) - En curso
- [x] Header mobile unificado (un solo menú hamburguesa)
- [x] Login con tagline "Tu asistente de viajes personal"
- [x] Perfil con ejemplos claros (PÉREZ/MARÍA LAURA)
- [x] Calendarios separados (Apple / Google)
- [ ] **Onboarding primera vez**
  - Recordar suscribirse al calendario
  - Guiar a completar perfil (nombre_pax/apellido_pax)
  - Explicar cómo reenviar emails
  
- [ ] **Rediseño UI**
  - Estética más moderna (actual se ve "vintage")
  - Mobile-first responsive
  - Placeholders genéricos (Juan Pérez, no nombres reales)

- [ ] **Bugs conocidos**
  - Viajes pasados no despliegan al hacer click

### MVP9: Notificaciones (Prioridad Media)
- [ ] Email cuando se detecta cambio en vuelo (delay, gate, cancelación)
- [ ] Resumen diario/semanal de viajes próximos
- [ ] Push notifications (requiere PWA)

### MVP10: Compartir Viajes (Prioridad Media)
- [ ] Tab "Compartidos" separado de "Mis Viajes"
- [ ] Invitar usuarios por email
- [ ] Rol "asistente" que puede cargar viajes para otros
- [ ] Útil para: secretarias, agentes de viaje, familias

---

## 📋 Backlog (Prioridad Baja)

### Mejoras de Carga

- [ ] **Autocomplete aerolíneas IATA**
  - Similar a origen/destino (ej: escribir "LAN" → sugiere LATAM)
  - Permitir "Otro" para vuelos privados/charters
  - Fallback a input libre si no encuentra en diccionario

- [ ] **Multi-tipo de viaje (no solo vuelos)**
  - Actualmente 100% orientado a vuelos - está bien para MVP
  - Carga manual: campos dinámicos según tipo seleccionado
    * Vuelo: aerolínea, número vuelo, terminal, gate, asiento
    * Hotel: nombre, dirección, check-in/out, nro reserva
    * Tren: operador, estación origen/destino, vagón, asiento
    * Auto rental: empresa, pickup/dropoff location, tipo vehículo
    * Barco/crucero: naviera, puerto embarque/desembarque, cabina
    * Actividad: nombre, ubicación, duración, tickets
  - Carga rápida (PDF): Claude detecta tipo automáticamente
  - Email processor: parsear confirmaciones de Booking, Airbnb, Rentalcars, etc.
  - Cards en index: diseño adaptado por tipo (iconos, campos relevantes)

### Features Generales
- [ ] Escanear pasaporte con cámara (Claude Vision)
- [ ] Compartir itinerario por WhatsApp (info no sensible)
- [ ] Dark mode
- [ ] Multi-idioma (ES/EN/PT)

### Técnico
- [ ] Refactor: renombrar modelo `Viaje` → `Segment` (es confuso)
- [ ] Archivar viajes pasados >1 año (optimización BD)
- [ ] Tests automatizados (pytest)
- [ ] CI/CD con GitHub Actions

### Infraestructura para Escalar
- [ ] Migrar emails a SendGrid/Mailgun (métricas, templates, bounces)
- [ ] CDN para assets estáticos
- [ ] Monitoring (Sentry, Cloud Monitoring)
- [ ] Backup automatizado de BD

---

## 💰 Modelo de Negocio (Ideas)

**Pendiente definir.** Opciones a explorar:

| Modelo | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| Freemium | Gratis hasta X viajes/mes | Fácil adopción | Necesita volumen |
| B2B | Vender a agencias de viaje | Ticket alto | Ciclo venta largo |
| White-label | Licenciar a empresas | Recurrente | Soporte complejo |
| Comisiones | Afiliados con booking/hotels | Pasivo | Depende de terceros |

**Próximo paso:** Validar con 10-20 usuarios beta antes de definir modelo.

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

## 📊 Métricas a Trackear (Futuro)

- Usuarios registrados
- Viajes cargados por método (email vs PDF vs manual)
- Emails procesados exitosamente
- Cambios de vuelo detectados
- Usuarios activos semanales

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
| 8 Dic 2025 | Header mobile unificado | Un solo menú = menos confusión |

---

## 🗑️ Archivos Deprecados

- `ESTADO_ACTUAL.md` → Reemplazado por este ROADMAP
- `REFACTOR_PLAN.md` → Completado, archivar
- `MVP4_RESEARCH.md` → Histórico, mantener como referencia
