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
