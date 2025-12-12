# 🎨 UX/UI ROADMAP - Mi Agente Viajes

**Última actualización:** 12 Diciembre 2025
**Versión:** 2.3 (toggle funcional clickeable + eliminación de botones confusos)

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

### 2. Empty States Educativos
**"Pantallas vacías son oportunidades, no errores"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Explicar cómo llenar la sección | "No hay datos" sin contexto |
| Incluir CTA principal | Solo texto informativo |
| Diseño atractivo (icono, copy amigable) | Texto gris plano |
| Escalar: un empty state por tipo | Modal genérico para todo |

**Fórmula:** "2 partes instrucción, 1 parte delight"

### 3. Contextual Over Modal
**"Ayuda donde se necesita, no popups genéricos"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Tip-boxes en secciones relevantes | Modal de onboarding con 5 pasos |
| Badges con tooltips explicativos | Banners que interrumpen |
| Inline hints en formularios | Páginas de ayuda separadas |
| Info aparece cuando es útil | Info aparece "por si acaso" |

### 4. Mobile-First Responsive
**"Diseñar para thumb, escalar para mouse"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Touch targets mínimo 44px | Botones pequeños |
| Navegación thumb-friendly | Menús en esquinas superiores |
| Texto legible sin zoom (16px mínimo) | Texto 12px en mobile |

### 5. Feedback Inmediato
**"El usuario siempre sabe qué está pasando"**

| ✅ Hacer | ❌ Evitar |
|----------|----------|
| Loading states claros | Pantalla congelada |
| Confirmaciones de acciones | Acciones silenciosas |
| Errores específicos y accionables | "Error desconocido" |

### 6. Estética Apple/B&O
**"Menos es más, tipografía como protagonista"**

| Aspecto | Especificación |
|---------|----------------|
| Background | #FAFAFA o #FFFFFF |
| Text primary | #1D1D1F |
| Text secondary | #86868B |
| Accent | #0071E3 (Apple blue) |
| Border radius | 12px (cards), 8px (buttons) |

---

## 📧 MVP14-UX: DISEÑO UNIFICADO DE EMAILS

### Problema identificado (11 Dic 2025)

Existía duplicación confusa entre dos pantallas:

| Ubicación | Sección | Propósito |
|-----------|---------|-----------|
| Preferencias | "Cuentas de email" | OAuth para detección automática |
| Mi Perfil | "Emails adicionales" | Aceptar reenvíos desde esas direcciones |

**Resultado:** Usuario no entiende la diferencia, emails aparecen en ambos lados.

### Solución: Una sola lista con toggle inteligente

**Principio:** Un email = una entrada. El toggle activa/desactiva OAuth si está disponible.

### Diseño de "Mis emails" (en Mi Perfil)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Mis emails                                                          │
│ Emails desde donde podés reenviar confirmaciones.                   │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ andy@gamberg.com.ar                               Principal     │ │
│ │                                                                 │ │
│ │ Detección automática                              [====ON====]  │ │
│ │ ✓ Gmail conectado • Última actividad: hace 5 min                │ │
│ │                                          [Escanear ahora]       │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ andy@ggya.com.ar                                       Quitar   │ │
│ │                                                                 │ │
│ │ Detección automática                              [====ON====]  │ │
│ │ ✓ Gmail conectado • 3 viajes detectados                         │ │
│ │                                          [Escanear ahora]       │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ andy.gamberg@familiabercomat.com                       Quitar   │ │
│ │                                                                 │ │
│ │ Detección automática                                            │ │
│ │ ┌─────────────────────────────────────────────────────────────┐ │ │
│ │ │ [G] Conectar con Gmail  │  [M] Conectar con Outlook/365    │ │ │
│ │ └─────────────────────────────────────────────────────────────┘ │ │
│ │                                                                 │ │
│ │ ⓘ Si tu empresa usa otro proveedor, reenviá a                   │ │
│ │    misviajes@gamberg.com.ar                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ correo@proveedorraro.com                               Quitar   │ │
│ │                                                                 │ │
│ │ Detección automática                              [disabled]    │ │
│ │ ⓘ Proveedor no soportado                                        │ │
│ │    Reenviá confirmaciones a misviajes@gamberg.com.ar            │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ [+ Agregar email]                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Estados del toggle

| Estado | UI | Condición |
|--------|-----|-----------|
| **ON** (conectado) | Toggle verde + stats | OAuth activo |
| **OFF** (disponible) | Botones Gmail/Outlook | Proveedor soportado, sin conexión |
| **Disabled** | Toggle gris + tooltip | Proveedor no soportado |

### Detección de proveedor

| Dominio | Proveedor | OAuth disponible |
|---------|-----------|------------------|
| gmail.com, googlemail.com | Gmail | ✅ |
| outlook.com, hotmail.com, live.com | Microsoft | ✅ |
| Dominio corporativo | Mostrar ambas opciones | Usuario elige |

**Para dominios corporativos:** Mostrar botones Gmail y Outlook/365. Si falla OAuth → "Proveedor no soportado, usá reenvío manual".

### Flujos de interacción

**Agregar email nuevo:**
```
1. Click [+ Agregar email]
2. Ingresa email
3. Sistema muestra opciones de conexión según proveedor detectado
```

**Activar detección (toggle ON):**
```
1. Click en [Conectar con Gmail] o [Conectar con Outlook/365]
2. Redirect a OAuth
3. Callback exitoso → Toggle ON, muestra stats
```

**Desactivar detección (toggle OFF):**
```
1. Click en toggle ON
2. Confirmación: "¿Desconectar detección automática?"
3. [Desconectar] → Revoca token, toggle OFF
4. Email sigue en lista (puede reenviar manualmente)
```

### Modelo de datos

```
User (1) → (N) UserEmail (1) → (0..1) EmailConnection

UserEmail:
- user_id
- email
- is_primary

EmailConnection:
- user_email_id (FK)
- provider (gmail | microsoft)
- access_token
- refresh_token
- last_scan
- trips_detected
```

---

## 🚀 ONBOARDING POST-REGISTRO

### Pantalla de bienvenida (después de crear cuenta)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│         [Icono avión - SVG]                                 │
│                                                             │
│         ¡Bienvenido, Andy!                                  │
│                                                             │
│  Hay 2 formas de cargar tus viajes:                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ⚡ Automático (recomendado)                            │  │
│  │                                                        │  │
│  │ Conectá tu email y detectamos vuelos,                  │  │
│  │ hoteles y reservas automáticamente.                    │  │
│  │                                                        │  │
│  │ [G] Conectar Gmail    [M] Conectar Outlook             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│              ─── o ───                                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✉️ Reenvío manual                                      │  │
│  │                                                        │  │
│  │ Reenviá confirmaciones a:                              │  │
│  │ misviajes@gamberg.com.ar           [Copiar]            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│                    [Omitir por ahora]                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Post-conexión OAuth exitosa

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│         [Icono check verde - SVG]                           │
│                                                             │
│         ¡Gmail conectado!                                   │
│                                                             │
│  Vamos a detectar automáticamente tus confirmaciones        │
│  de vuelos, hoteles y reservas.                             │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Tip: Completá tu nombre en pasajes para que te        │  │
│  │ reconozcamos automáticamente como pasajero.           │  │
│  │                                                        │  │
│  │ Nombre: [Andres    ]  Apellido: [Gamberg   ]          │  │
│  │                                                        │  │
│  │ [Guardar]                                              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│                    [Ir a mis viajes]                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Toast de feedback (después de escaneo)

```
┌────────────────────────────────────────────────────────────┐
│ ✓ 2 vuelos y 1 hotel detectados                   [Ver]  ✕ │
└────────────────────────────────────────────────────────────┘
```

---

## 🏗️ NUEVA ARQUITECTURA DE PANTALLAS

### Antes (confuso)

```
Mi Perfil
├── Datos personales
├── Emails adicionales  ← DUPLICADO
└── Preferencias y notificaciones → link

Preferencias
├── Cuentas de email (OAuth) ← DUPLICADO
├── Remitentes de confianza
└── Notificaciones
```

### Después (simplificado)

```
Mi Perfil
├── Datos personales (nombre, nombre_pax, apellido_pax)
├── Mis emails (unificado: lista + toggle OAuth)
├── Calendario (link personal)
└── [Preferencias avanzadas] → link o acordeón

Preferencias (solo configuración avanzada)
├── Remitentes de confianza (custom senders)
├── Notificaciones
└── Combinar vuelos duplicados
```

---

## 🗂️ UX PARA TIPOS DE EVENTOS (FUTURO)

### Timeline unificado (Homepage futura)

```
Próximos eventos                                    
                                                    
┌─────────────────────────────────────────────────┐
│ 📅 15 Dic                                       │
│                                                 │
│ ┌─ Vuelo ─────────────────────────────────────┐ │
│ │ AR1234 • EZE → GRU                    10:00 │ │
│ │ Aerolíneas Argentinas                       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ Hotel ─────────────────────────────────────┐ │
│ │ Pousada Maravilha              Check-in 15h │ │
│ │ Fernando de Noronha • 6 noches              │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 📅 17 Dic                                       │
│                                                 │
│ ┌─ Restaurante ───────────────────────────────┐ │
│ │ Mergulhão                             20:00 │ │
│ │ 4 personas • Frutos del mar                 │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Cards por tipo (Progressive Disclosure)

**Card colapsada (igual para todos):**
- Icono de tipo + Título + Hora
- Subtítulo contextual
- Badge si hay alerta

**Card expandida (específica por tipo):**

| Tipo | Campos visibles al expandir |
|------|----------------------------|
| Vuelo | Pasajeros, terminal, puerta, código reserva |
| Hotel | Dirección, # habitación, huéspedes |
| Restaurante | Dirección, preferencias, ocasión |
| Cita | Profesional, especialidad, motivo |

### Empty States por tipo

| Tipo | Icono SVG | Título |
|------|-----------|--------|
| Vuelos | paper-airplane | Tus próximos vuelos |
| Hoteles | building-office | Tus próximas estadías |
| Restaurantes | cake | Tus reservas gastronómicas |
| Citas | calendar | Tus próximas citas |

---

## 📋 CHECKLIST PRE-IMPLEMENTACIÓN

```
□ ¿Usa progressive disclosure? (no muestra todo de entrada)
□ ¿Los empty states son educativos? (no solo "no hay datos")
□ ¿La ayuda es contextual? (no modals genéricos)
□ ¿Funciona bien en mobile? (touch targets, thumb reach)
□ ¿Hay feedback de acciones? (loading, success, error)
□ ¿Sigue la estética Apple? (minimalismo, espaciado)
□ ¿El copy es amigable? (vos en lugar de usted)
```

---

## 🗂️ INVENTARIO DE EMPTY STATES

| Sección | Estado | Implementado |
|---------|--------|--------------|
| Viajes próximos (0) | Empty state educativo | ✅ MVP12 |
| Viajes pasados (0) | No mostrar sección | ✅ Ya OK |
| **Mis emails (0)** | **Botón agregar + tip de beneficios** | **📅 MVP14-UX** |
| Hoteles (0) | Empty state educativo | 📅 MVP-HOTEL |
| Restaurantes (0) | Empty state educativo | 📅 MVP-REST |
| Citas (0) | Empty state educativo | 📅 MVP-CITA |
| Viajes compartidos (0) | Empty state + invitar | 📅 MVP15 |

---

## 🔄 INVENTARIO DE PROGRESSIVE DISCLOSURE

| Componente | Qué se oculta | Trigger para mostrar |
|------------|---------------|----------------------|
| Formulario manual | Campos avanzados | Click "Más detalles" |
| Carga rápida | Textarea email | Click "¿No tenés PDF?" |
| Card de viaje | Segmentos y pasajeros | Click en card |
| Viajes pasados | Lista completa | Scroll o click |
| Menú principal | Opciones secundarias | Click hamburger |
| **Email sin OAuth** | **Opciones de conexión** | **Inline siempre visible** |
| **Preferencias avanzadas** | **Remitentes, notificaciones** | **Link o acordeón** |

---

## ✅ COMPLETADO

### MVP14-UX: Unificación Emails (12 Dic 2025)
- [x] Unificar emails en perfil (12 Dic 2025)
- [x] Eliminar duplicación de Preferencias
- [x] Toggle funcional clickeable para desconectar
- [x] Detección automática de proveedor (Gmail/Outlook/corporativo)
- [x] Eliminar botones confusos en emails corporativos

### Fix UX (11 Dic 2025)
- [x] Toolbar feedback inmediato en modo agrupar/eliminar
- [x] Tipografía consistente en remitentes de confianza

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

### Alta Prioridad

| Tarea | Descripción | Esfuerzo |
|-------|-------------|----------|
| Onboarding post-registro | Pantalla de bienvenida con opciones OAuth | 2-3h |
| Stats por email | trips_detected, last_activity | 1h |

### Media Prioridad

| Tarea | Descripción | Esfuerzo |
|-------|-------------|----------|
| MVP-REF | Refactor BD (Viaje → Evento + extensiones) | 8-10h |
| Dark mode | Toggle en perfil | 4h |
| Microsoft OAuth | Conectar Outlook/365 | 6-8h |

### Baja Prioridad
- [ ] Autocomplete aerolíneas
- [ ] Swipe actions en mobile
- [ ] Skeleton loaders
- [ ] Animaciones de transición

---

## 📝 GLOSARIO DE UX

| Término | Definición | Ejemplo en proyecto |
|---------|------------|---------------------|
| Progressive Disclosure | Revelar info gradualmente | Acordeón "Más detalles" |
| Empty State | Diseño de pantalla sin datos | Homepage sin viajes |
| Contextual Help | Ayuda donde se necesita | Tooltip en badge |
| Toggle | Interruptor on/off | Detección automática |
| Toast | Notificación temporal | "Viaje guardado ✓" |

---

## 🔗 REFERENCIAS

- [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/)
- [Laws of UX](https://lawsofux.com/)
- [Userpilot: Progressive Disclosure](https://userpilot.com/blog/progressive-disclosure/)

---

**Este documento es la fuente de verdad para decisiones de UX.**
**Actualizar cuando se agreguen nuevos principios o patterns.**
