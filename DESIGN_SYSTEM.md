# 🎨 DESIGN SYSTEM - Mi Agente Viajes

**Última actualización:** 17 Diciembre 2025
**Versión:** 1.0

---

## 📐 Principios Fundamentales

1. **Consistencia sobre creatividad** - Cada elemento sigue las mismas reglas
2. **Minimalismo Apple/B&O** - Menos es más, espacio generoso
3. **Accesibilidad primero** - Contraste, touch targets, legibilidad

---

## 🎨 Paleta de Colores

### Colores Base
```css
--bg: #F5F5F7;              /* Fondo principal */
--bg-card: #FFFFFF;          /* Cards y contenedores */
--text: #1D1D1F;             /* Texto principal */
--text-secondary: #86868B;   /* Texto secundario */
--text-muted: #AEAEB2;       /* Texto terciario/hints */
```

### Colores de Acción
```css
--accent: #0071E3;           /* Azul Apple - CTAs principales */
--accent-hover: #0077ED;     /* Hover del accent */
```

### Colores Semánticos
```css
--success: #34C759;          /* Confirmaciones, on-time */
--danger: #FF3B30;           /* Errores, eliminar */
--warning: #FF9500;          /* Alertas, delays */
```

### Gradientes (uso limitado)
```css
/* Solo para elementos hero/destacados */
--gradient-primary: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
```

### Bordes
```css
--border: #D2D2D7;           /* Bordes estándar */
--border-light: #E8E8ED;     /* Bordes sutiles */
```

---

## 📝 Tipografía

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
```

### Font Monospace (código, emails)
```css
font-family: 'SF Mono', Monaco, 'Courier New', monospace;
```

### Unidades y Accesibilidad
```css
/* Base obligatoria en todos los templates */
html {
    font-size: 100%;
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
}
```

**Regla:** Usar rem para font-size, NO px.

### Escala Tipográfica

| Uso | rem | px equivalente | Peso | Letter-spacing |
|-----|-----|----------------|------|----------------|
| Hero | 3.5rem | 56px | 700 | -0.5px |
| Page title | 2rem | 32px | 600 | -0.5px |
| Section | 1.75rem | 28px | 600 | -0.3px |
| Card title | 1.125rem | 18px | 600 | -0.3px |
| Body | 1rem | 16px | 400 | 0 |
| Label | 0.875rem | 14px | 500 | 0 |
| Caption | 0.8125rem | 13px | 400 | 0 |
| Micro (mínimo) | 0.75rem | 12px | 600 | 0.5px (uppercase) |

**Nunca usar** font-size menor a 0.75rem (12px).

---

## 🔲 Espaciado

### Sistema de 8px
```
4px   - micro (gap entre iconos y texto inline)
8px   - xs
12px  - sm
16px  - md
20px  - lg
24px  - xl
32px  - 2xl
48px  - 3xl
```

### Border Radius
```css
--radius: 12px;              /* Estándar (inputs, botones) */
--radius-lg: 16px;           /* Cards grandes */
--radius-sm: 8px;            /* Elementos pequeños */
--radius-full: 100px;        /* Pills, avatares */
```

---

## 🖼️ ICONOGRAFÍA

### ⚠️ REGLA FUNDAMENTAL
```
NUNCA usar emojis en la interfaz de usuario.
Solo se permiten en contenido generado por el usuario.
```

### Librería Oficial
**Heroicons** (https://heroicons.com)
- Estilo: **Outline**
- Stroke width: **1.5** (estándar) o **2** (énfasis)

### Tamaños

| Contexto | Tamaño | Clase sugerida |
|----------|--------|----------------|
| Inline con texto | 16px | `icon-sm` |
| Botones | 20px | `icon-md` |
| Headers/acciones | 24px | `icon-lg` |
| Hero/empty states | 48px | `icon-xl` |

### Colores
- Heredan del parent via `currentColor`
- Nunca hardcodear color en el SVG
- Usar clases de color existentes

### Catálogo de Iconos en Uso

| Concepto | Icono | SVG |
|----------|-------|-----|
| Email/correo | envelope | `<path d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/>` |
| Globo/mundo | globe-americas | `<path d="M6.115 5.19A9 9 0 1017.885 5.19M6.115 5.19A8.965 8.965 0 0112 3c1.929 0 3.716.607 5.18 1.64M6.115 5.19l5.135 5.136m6.635-4.726l-5.135 5.136m0 0L12 12m.75-1.5l5.385 5.385M12 12l-5.385 5.385m10.77 0A9 9 0 0112 21a9 9 0 01-5.385-1.615m10.77 0l-5.135-5.135m-5.385 5.135l5.135-5.135"/>` |
| Documento subir | document-arrow-up | `<path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>` |
| Editar/escribir | pencil-square | `<path d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/>` |
| Avión/vuelo | paper-airplane | `<path d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/>` |
| Calendario | calendar | `<path d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"/>` |
| Menú hamburger | bars-3 | `<path d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"/>` |
| Chevron derecha | chevron-right | `<path d="M8.25 4.5l7.5 7.5-7.5 7.5"/>` |
| Chevron abajo | chevron-down | `<path d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>` |
| Flecha atrás | arrow-left | `<path d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>` |
| Check/éxito | check-circle | `<path d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>` |
| Info | information-circle | `<path d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>` |
| Cerrar | x-mark | `<path d="M6 18L18 6M6 6l12 12"/>` |
| Plus/agregar | plus | `<path d="M12 4.5v15m7.5-7.5h-15"/>` |
| Usuario | user | `<path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>` |

### Cómo Usar

```html
<!-- Inline con texto (16px) -->
<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="..."/>
</svg>

<!-- En botón (20px) -->
<button class="btn">
    <svg class="icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="..."/>
    </svg>
    Texto
</button>

<!-- Hero/empty state (48px) -->
<div class="empty-state-icon">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="..."/>
    </svg>
</div>
```

### CSS para Iconos
```css
/* Clases de tamaño */
.icon-sm { width: 16px; height: 16px; }
.icon-md { width: 20px; height: 20px; }
.icon-lg { width: 24px; height: 24px; }
.icon-xl { width: 48px; height: 48px; }

/* Alineación con texto */
svg {
    flex-shrink: 0;
    vertical-align: middle;
}
```

---

## 🔘 Botones

### Jerarquía

| Tipo | Uso | Estilo |
|------|-----|--------|
| Primary | Acción principal (1 por pantalla) | Fondo accent, texto blanco |
| Secondary | Acciones alternativas | Fondo blanco, borde, texto oscuro |
| Text | Acciones terciarias | Sin fondo ni borde, solo texto |
| Danger | Acciones destructivas | Texto rojo, hover fondo rojo claro |

### Tamaños
```css
/* Estándar */
padding: 10px 20px;
font-size: 14px;

/* Pequeño */
padding: 8px 14px;
font-size: 13px;

/* Grande */
padding: 14px 24px;
font-size: 16px;
```

### Estados
- Default
- Hover (elevar ligeramente, cambio de color sutil)
- Active (presionado)
- Disabled (opacity 0.5, cursor not-allowed)
- Loading (spinner opcional)

---

## 📱 Responsive

### Breakpoints
```css
/* Mobile first */
@media (max-width: 480px) { /* Small phones */ }
@media (max-width: 768px) { /* Tablets portrait */ }
@media (max-width: 1024px) { /* Tablets landscape */ }
```

### Touch Targets
- Mínimo **44px × 44px** para elementos interactivos en mobile
- Espaciado adecuado entre targets

---

## ✅ Checklist Pre-Implementación

Antes de agregar cualquier elemento de UI, verificar:

- [ ] ¿Usa colores del sistema?
- [ ] ¿Usa tipografía del sistema?
- [ ] ¿Usa iconos SVG (no emojis)?
- [ ] ¿Respeta espaciado de 8px?
- [ ] ¿Funciona en mobile?
- [ ] ¿Touch targets ≥ 44px?

---

## 📋 Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 10 Dic 2025 | Documento inicial creado |
| 10 Dic 2025 | Regla de no-emojis establecida |
| 17 Dic 2025 | Migración a rem, tabla actualizada con valores, regla de mínimo 0.75rem |
