# Design System - Segmentos de Reserva

## Filosofía
Inspirado en Apple y Bang & Olufsen: minimalismo, monocromático, jerarquía tipográfica.
**Sin colores de acento.** La información se diferencia por peso, tamaño y espaciado.

## Paleta

| Uso | Color | Hex |
|-----|-------|-----|
| Texto principal | Negro | #1d1d1f |
| Texto secundario | Gris | #6e6e73 |
| Texto terciario | Gris claro | #86868b |
| Bordes | Gris suave | #d2d2d7 |
| Fondo superficie | Casi blanco | #f5f5f7 |
| Fondo cards | Blanco | #ffffff |

## Tipografía

| Elemento | Tamaño | Peso | Color |
|----------|--------|------|-------|
| Ruta (ORI → DES) | 22px | 600 | principal |
| Proveedor/Operador | 14px | 400 | secundario |
| Metadata (hora, terminal) | 13px | 400 | secundario |
| Nombre pasajero | 13px | 500 | principal |
| Badges (asiento, clase) | 12px | 400 | secundario |
| Código reserva | 11px | 500 | terciario, monospace |

## Badges

**Todos los badges usan el mismo estilo:**
- Fondo: #f5f5f7
- Texto: #1d1d1f
- Padding: 2px 8px
- Border-radius: 4px
- Sin bordes de color

La diferencia es solo el contenido: "12A" (asiento), "Business" (clase), "CM*12345" (FFP)

## Estructura de Segmento
```
┌─────────────────────────────────────────┐
│ TÍTULO PRINCIPAL (ruta o nombre)        │  22px, weight 600
│                                         │
│ Proveedor · Número                      │  14px, secundario
│ Salida: 08:30 · Terminal 2 · Puerta B4  │  13px, secundario
│ Llegada: 12:45                          │  13px, secundario
│ Reserva: ABC123                         │  13px, secundario
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ABC123 (si combinado)               │ │  11px, monospace, terciario
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ NOMBRE PASAJERO                 │ │ │  13px, weight 500
│ │ │ [12A] [Business] [FFP123]       │ │ │  12px, badges grises
│ │ └─────────────────────────────────┘ │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Bodega: 2x32kg · Cabina: 1x10kg         │  12px, terciario
└─────────────────────────────────────────┘
```

## Reglas

- **Sin emojis** - nunca
- **Sin colores de acento** - todo monocromático
- **Jerarquía por tipografía** - no por color
- **Consistencia** - mismo estilo para combinados y no combinados
- **Cards de pasajeros** - fondo blanco, borde gris sutil
