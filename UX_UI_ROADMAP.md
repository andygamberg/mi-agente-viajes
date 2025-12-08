# 🎨 UX/UI ROADMAP - Mi Agente Viajes

**Última actualización:** 7 Diciembre 2025
**Estado:** Pendiente (después de MVP6 Multi-usuario)

---

## 📊 ESTADO ACTUAL (v1.2)

### ✅ Implementado
- Cards colapsables con viajes agrupados
- Pasajeros colapsables por segmento
- Desagrupar viajes
- Eliminar múltiples viajes
- Modal "Agregar Viaje" con tip de email
- Auto-refresh polling (120s)
- Carga Rápida (PDF + email text)
- Carga Manual (formulario completo)

### 🔧 Funciona pero necesita mejoras
- Homepage: agregar banner con email de reenvío
- Carga Manual: demasiados campos, simplificar
- Carga Rápida: puede ser más limpia

---

## 🏠 HOMEPAGE - Diseño propuesto

### Con email automation activo:
```
┌─────────────────────────────────────────┐
│  Mis Viajes              [+ Agregar]    │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 📮 Reenviá tus confirmaciones a:    ││
│  │ misviajes@gamberg.com.ar   [Copiar] ││
│  └─────────────────────────────────────┘│
│                                         │
│  ━━━ Tabs (post multi-usuario) ━━━     │
│  [Mis Viajes] [Compartidos]             │
│                                         │
│  Próximos Viajes (3)                    │
│  [Cards...]                             │
│                                         │
│  Pasados (5)                            │
│  [Cards colapsados...]                  │
└─────────────────────────────────────────┘
```

---

## 📝 CARGA MANUAL - Simplificación

### Campos esenciales (siempre visibles):
| Campo | Obligatorio | Notas |
|-------|-------------|-------|
| Tipo | ✅ | Vuelo, Hotel, Auto, Tren, Actividad |
| Origen | ✅ | Autocomplete IATA para vuelos |
| Destino | ✅ | Autocomplete IATA para vuelos |
| Fecha salida | ✅ | |
| Hora salida | ❌ | |
| Código reserva | ❌ | |

### Campos avanzados (acordeón "Más detalles"):
| Campo | Aplica a |
|-------|----------|
| Aerolínea | Vuelo |
| Número vuelo | Vuelo |
| Fecha llegada | Vuelo, Tren |
| Hora llegada | Vuelo, Tren |
| Terminal | Vuelo |
| Puerta | Vuelo |
| Asiento | Vuelo, Tren |
| Hotel nombre | Hotel |
| Dirección | Hotel, Actividad |
| Notas | Todos |

### Autocomplete IATA:
- Al escribir "EZE" → sugiere "Buenos Aires (EZE)"
- Al escribir "Buenos" → sugiere aeropuertos de Buenos Aires
- Usar diccionario IATA_TO_CITY existente

---

## 📄 CARGA RÁPIDA - Simplificación

### Opción A: Solo PDF
- Eliminar textarea de email
- Foco en arrastrar/seleccionar PDF
- Más limpio y simple

### Opción B: Mantener ambos (recomendado)
- PDF como método principal (arriba)
- Textarea como alternativa (abajo, colapsado)
- Texto: "¿No tenés PDF? Pegá el email"

---

## 🆕 TIPOS DE VIAJE A SOPORTAR

| Tipo | Campos específicos | Prioridad |
|------|-------------------|-----------|
| ✈️ Vuelo | Aerolínea, número, terminal, gate | ✅ Ya existe |
| 🏨 Hotel | Nombre hotel, dirección, check-in/out | MVP futuro |
| 🚗 Auto | Empresa, pickup/dropoff location | MVP futuro |
| 🚂 Tren | Operador, estación, vagón/asiento | MVP futuro |
| 📍 Actividad | Nombre, ubicación, duración | MVP futuro |

---

## 🎨 MEJORAS VISUALES PENDIENTES

### Modal "Agregar Viaje"
- [x] Tip de email automático
- [x] Sin "Por Código de Reserva"
- [ ] Iconos más netos (emojis → SVG icons)
- [ ] Animación al abrir/cerrar

### Cards de viajes
- [ ] Indicador visual de "compartido conmigo"
- [ ] Badge de estado (confirmado, cambio detectado)
- [ ] Swipe actions en móvil

### General
- [ ] Dark mode
- [ ] Loading states mejorados
- [ ] Empty states ilustrados
- [ ] Onboarding primera vez

---

## 📱 MOBILE / PWA (MVP8)

- FAB (Floating Action Button) para agregar
- Touch-friendly: botones más grandes
- Swipe para eliminar/archivar
- Pull-to-refresh
- Notificaciones push

---

## 🌍 MULTI-IDIOMA (Futuro)

- Español (default)
- English
- Português
- Cambiar email genérico: mytrips@[dominio]

---

## 📋 ORDEN DE IMPLEMENTACIÓN

1. **MVP6:** Multi-usuario (auth + user_id)
2. **MVP7:** Compartir viajes + tabs
3. **UX Sprint:** Homepage + formularios + visual polish
4. **MVP8:** PWA / móvil
5. **Futuro:** Multi-idioma, dark mode, más tipos de viaje

---

## 📎 REFERENCIAS

- Auditoría UX original: 4 Diciembre 2025
- Spec Multi-usuario: 7 Diciembre 2025
- TripCase como inspiración para UX

---

## 🔧 DEUDA TÉCNICA

### Nomenclatura confusa (CRÍTICO)
**Problema:** El modelo `Viaje` en BD es en realidad un VUELO/SEGMENTO
- Lo que el usuario ve como "Viaje" = `grupo_viaje` 
- Lo que el usuario ve como "Vuelo" = registro `Viaje`

**Solución propuesta:**
```
Trip (Viaje)
├── id, nombre, user_id, shared_with
└── tiene muchos → Segments

Segment (Segmento/Vuelo)
├── id, trip_id
├── tipo (vuelo, hotel, auto, actividad)
├── origen, destino, fechas...
```

**Cuándo:** Sprint de UX/UI completo

---

## 👤 HEADER USUARIO

### Actual
- Muestra: "👤 Nombre | Salir"
- Posición: arriba derecha

### Propuesto (dropdown)
```
👤 Andy Gamberg ▼
├── Mi cuenta
├── Mis emails (agregar/verificar)
├── Compartir con... (gestionar usuarios)
├── ─────────────
└── Cerrar sesión
```

---

## 📧 MÚLTIPLES EMAILS POR USUARIO

### Modelo
```python
class UserEmail(db.Model):
    user_id = ForeignKey(User)
    email = unique, verificado, es_principal
```

### Flujo
1. Usuario registra con email principal
2. En "Mis emails" puede agregar más
3. Sistema envía código verificación
4. Email processor busca remitente en UserEmail → user_id

### Casos de uso
- Email trabajo + personal
- Reenviar desde distintas cuentas
- Familia con emails compartidos

---

## 📲 COMPARTIR POR WHATSAPP

### Info básica (SÍ compartir)
- Vuelo: LH511
- Fecha: 08/06/2026
- Ruta: EZE → FRA
- Sale: 16:40
- Llega: 11:00 (+1)
- Terminal: 1

### Info sensible (NO compartir)
- Asiento
- Clase/cabina
- Viajero frecuente
- Código reserva
- Equipaje

### Implementación
- Botón 📤 en cada card de vuelo
- Genera texto formateado
- Abre `whatsapp://send?text=...`

---

## 🔄 ORDEN DE IMPLEMENTACIÓN ACTUALIZADO

1. ~~MVP6.1: Modelo User~~ ✅
2. ~~MVP6.2: Auth + proteger rutas~~ ✅
3. **MVP6.3: Asignar user_id al crear viajes**
4. **MVP6.4: UserEmail model**
5. **MVP6.5: Email processor multi-usuario**
6. **MVP7: Compartir viajes entre usuarios**
7. **UX Sprint: Refactor nomenclatura + diseño completo**
8. **MVP8: PWA/móvil**
9. **Nice to have: WhatsApp sharing**


---

## 🐛 BUGS / MEJORAS DETECTADAS

### Viajes pasados no despliegan
- Los cards de "Pasados" no expanden para ver vuelos individuales
- Comportamiento inconsistente con "Próximos Viajes"

### Escalabilidad BD - viajes pasados
**Problema:** BD crece indefinidamente con viajes históricos
**Opciones:**
- Archivar viajes >1 año a tabla separada
- Exportar a JSON/backup y eliminar
- Límite de viajes pasados visibles (paginación)
- Cold storage para históricos

