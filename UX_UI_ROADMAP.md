# 🎨 UX/UI ROADMAP - Mi Agente Viajes

**Última actualización:** 10 Diciembre 2025
**Versión:** 2.0 (incorpora principios de diseño)

---

## 🧭 PRINCIPIOS DE DISEÑO

> Estos principios guían TODAS las decisiones de UX del proyecto.
> Antes de implementar cualquier feature, validar contra estos principios.

### 1. Progressive Disclosure
**"Mostrar solo lo necesario, revelar más cuando corresponda"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Acordeones para campos avanzados | Formularios con 20 campos visibles |
| Secciones colapsables | Todo expandido siempre |
| Tooltips para info secundaria | Textos largos explicativos inline |
| Revelar opciones según contexto | Mostrar todas las opciones siempre |

**Ejemplos en el proyecto:**
- Formulario manual: campos básicos visibles, "Más detalles" en acordeón
- Homepage: viajes pasados colapsados por default
- Carga rápida: alternativa email colapsada, PDF es protagonista

**Aplicación futura:**
- Hoteles: campos básicos (nombre, fechas), acordeón para amenities
- Restaurantes: nombre + hora, acordeón para preferencias dietarias

### 2. Empty States Educativos
**"Pantallas vacías son oportunidades, no errores"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Explicar cómo llenar la sección | "No hay datos" sin contexto |
| Incluir CTA principal | Solo texto informativo |
| Diseño atractivo (icono, copy amigable) | Texto gris plano |
| Escalar: un empty state por tipo | Modal genérico para todo |

**Fórmula:** "2 partes instrucción, 1 parte delight"

**Template para nuevos empty states:**
```
┌─────────────────────────────────────────┐
│           [Icono relevante]             │
│                                         │
│     [Título motivacional]               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  [Instrucción principal]        │   │
│  │  [Email/acción destacada]       │   │
│  │  [Nota de contexto]             │   │
│  └─────────────────────────────────┘   │
│                                         │
│            ─── o ───                   │
│                                         │
│     [Alternativa 1]  [Alternativa 2]   │
└─────────────────────────────────────────┘
```

**Aplicación futura:**
- Sección hoteles vacía: "🏨 Tus próximas estadías" + instrucciones
- Sección restaurantes vacía: "🍽️ Tus reservas gastronómicas" + instrucciones
- Calendario sin suscripción: tip educativo de beneficios

### 3. Contextual Over Modal
**"Ayuda donde se necesita, no popups genéricos"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Tip-boxes en secciones relevantes | Modal de onboarding con 5 pasos |
| Badges con tooltips explicativos | Banners que interrumpen |
| Inline hints en formularios | Páginas de ayuda separadas |
| Info aparece cuando es útil | Info aparece "por si acaso" |

**Ejemplos en el proyecto:**
- Badge "Completar perfil" con tooltip que explica beneficio
- Tip en carga rápida: "¿Tenés PDF? Es más fácil"
- Tip en sección calendario: beneficio de suscribirse

**Aplicación futura:**
- Al agregar pasajero: tip "Usá formato APELLIDO/NOMBRES"
- Al compartir viaje: tooltip explicando qué verá el otro usuario
- Al conectar Gmail: inline explanation de permisos

### 4. Mobile-First Responsive
**"Diseñar para thumb, escalar para mouse"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Touch targets mínimo 44px | Botones pequeños |
| Navegación thumb-friendly | Menús en esquinas superiores |
| Formularios optimizados para teclado móvil | Campos que requieren precisión |
| Texto legible sin zoom (16px mínimo) | Texto 12px en mobile |
| Swipe gestures donde tenga sentido | Solo clicks |

### 5. Feedback Inmediato
**"El usuario siempre sabe qué está pasando"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Loading states claros | Pantalla congelada |
| Confirmaciones de acciones | Acciones silenciosas |
| Errores específicos y accionables | "Error desconocido" |
| Estados de éxito celebratorios | Solo desaparecer el form |

**Aplicación futura:**
- Al procesar PDF: "Analizando tu reserva..." con spinner
- Al detectar vuelo: "✈️ Encontramos 3 vuelos" con preview
- Error de email inválido: "Este email ya está registrado" no "Error"

### 6. Estética Apple/B&O
**"Menos es más, tipografía como protagonista"**

| Aspecto | Especificación |
|---------|----------------|
| Background | #FAFAFA o #FFFFFF |
| Text primary | #1D1D1F |
| Text secondary | #86868B |
| Accent | #0071E3 (Apple blue) |
| Borders | #E5E5E5 o ninguno |
| Shadows | Muy sutiles o ninguna |
| Border radius | 12px (cards), 8px (buttons) |
| Font weights | 400 body, 500 labels, 600 headings |
| Font family | -apple-system, SF Pro, Inter |

---

## 📋 CHECKLIST PRE-IMPLEMENTACIÓN

Antes de implementar cualquier feature de UI, verificar:

```
□ ¿Usa progressive disclosure? (no muestra todo de entrada)
□ ¿Los empty states son educativos? (no solo "no hay datos")
□ ¿La ayuda es contextual? (no modals genéricos)
□ ¿Funciona bien en mobile? (touch targets, thumb reach)
□ ¿Hay feedback de acciones? (loading, success, error)
□ ¿Sigue la estética Apple? (minimalismo, espaciado)
□ ¿El copy es amigable? (no técnico, vos en lugar de usted)
```

---

## 🗂️ INVENTARIO DE EMPTY STATES

| Sección | Estado | Implementado |
|---------|--------|--------------|
| Viajes próximos (0) | Empty state educativo | 🔄 MVP12 |
| Viajes pasados (0) | No mostrar sección | ✅ Ya OK |
| Emails adicionales (0) | Solo muestra principal | ✅ Ya OK |
| Hoteles (0) | Empty state educativo | 📅 Futuro |
| Restaurantes (0) | Empty state educativo | 📅 Futuro |
| Actividades (0) | Empty state educativo | 📅 Futuro |
| Viajes compartidos (0) | Empty state + invitar | 📅 MVP15 |

---

## 🔄 INVENTARIO DE PROGRESSIVE DISCLOSURE

| Componente | Qué se oculta | Trigger para mostrar |
|------------|---------------|----------------------|
| Formulario manual | Campos avanzados | Click "Más detalles" |
| Carga rápida | Textarea email | Click "¿No tenés PDF?" |
| Card de viaje | Segmentos y pasajeros | Click en card |
| Viajes pasados | Lista completa | Scroll o click |
| Pasajeros en vuelo | Lista de nombres | Click "Pasajeros (N)" |
| Menú principal | Opciones secundarias | Click hamburger |

---

## ✅ COMPLETADO

### MVP12: Onboarding con Empty States (10 Dic 2025)
- [x] Empty state educativo en homepage (reemplaza modal)
- [x] Eliminar modal onboarding
- [x] Tooltip en badge "Completar perfil"
- [x] Documentar principios de UX

### MVP11: Deduplicación (10 Dic 2025)
- [x] Toggle en perfil (progressive disclosure de preferencia)
- [x] Badge "Combinado" con tooltip explicativo

### MVP9-10: Calendar (9 Dic 2025)
- [x] Sección calendario en perfil con tip educativo
- [x] Links personalizados por usuario

### Anteriores
- [x] Cards colapsables (progressive disclosure)
- [x] Acordeón en formulario manual
- [x] Drop zone PDF como método principal
- [x] Banner email colapsable

---

## 🔧 PENDIENTE

### Alta Prioridad (post-MVP12)
- [ ] Refactor nomenclatura BD (Viaje → Segment, grupo_viaje → Trip)
- [ ] Dark mode (toggle en perfil)

### Media Prioridad
- [ ] Autocomplete aerolíneas (como IATA)
- [ ] Swipe actions en mobile
- [ ] Pull-to-refresh en PWA

### Baja Prioridad
- [ ] Animaciones de transición
- [ ] Skeleton loaders
- [ ] Compartir por WhatsApp

---

## 📱 APLICACIÓN DE PRINCIPIOS A FEATURES FUTURAS

### Hoteles (MVP futuro)

**Empty State:**
```
🏨
Tus próximas estadías

┌─────────────────────────────────────────┐
│ Reenviá confirmaciones de Booking,      │
│ Airbnb, Hotels.com a:                   │
│                                         │
│ misviajes@gamberg.com.ar    [Copiar]    │
└─────────────────────────────────────────┘

        ─── o ───

   [+ Agregar hotel manualmente]
```

**Formulario (Progressive Disclosure):**
- Visible: Nombre hotel, Ciudad, Check-in, Check-out
- Acordeón: Dirección, # habitación, amenities, notas

### Restaurantes (MVP futuro)

**Empty State:**
```
🍽️
Tus reservas gastronómicas

Reenviá confirmaciones de OpenTable,
TheFork, o el email del restaurante

        ─── o ───

   [+ Agregar reserva manualmente]
```

**Formulario (Progressive Disclosure):**
- Visible: Nombre restaurante, Fecha, Hora, # personas
- Acordeón: Dirección, preferencias, ocasión especial, notas

### Compartir Viajes (MVP15)

**Empty State (Tab "Compartidos"):**
```
👥
Viajes compartidos contigo

Cuando alguien te incluya en una reserva
o te invite a un viaje, aparecerá aquí.

┌─────────────────────────────────────────┐
│ Tip: Completá tu perfil para que te     │
│ reconozcan automáticamente como         │
│ pasajero en reservas.                   │
└─────────────────────────────────────────┘

   [Ir a mi perfil]
```

### Gmail Integration (MVP14)

**Contextual Help (no modal):**
En sección de perfil "Conexiones":
```
┌─────────────────────────────────────────┐
│ 📧 Conectar Gmail                       │
│                                         │
│ Detectamos automáticamente emails de    │
│ aerolíneas y los procesamos por vos.    │
│                                         │
│ Solo leemos emails de remitentes        │
│ conocidos (Despegar, Booking, etc).     │
│                                         │
│ [Conectar Gmail]  [Más info]            │
└─────────────────────────────────────────┘
```

---

## 📝 GLOSARIO DE UX

| Término | Definición | Ejemplo en proyecto |
|---------|------------|---------------------|
| Progressive Disclosure | Revelar info gradualmente según necesidad | Acordeón "Más detalles" |
| Empty State | Diseño de pantalla cuando no hay datos | Homepage sin viajes |
| Contextual Help | Ayuda que aparece donde se necesita | Tooltip en badge |
| Tip Box | Caja destacada con consejo útil | "¿Tenés PDF? Es más fácil" |
| Toast | Notificación temporal no intrusiva | "Viaje guardado ✓" |
| Skeleton | Placeholder mientras carga contenido | (pendiente implementar) |
| CTA | Call to Action - botón/link principal | "Subir PDF" |

---

## 🔗 REFERENCIAS

- [Userpilot: Progressive Disclosure](https://userpilot.com/blog/progressive-disclosure/)
- [Smashing Magazine: Empty States](https://www.smashingmagazine.com/2020/02/empty-states-ux/)
- [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/)
- [Laws of UX](https://lawsofux.com/)

---

**Este documento es la fuente de verdad para decisiones de UX.**
**Actualizar cuando se agreguen nuevos principios o patterns.**
