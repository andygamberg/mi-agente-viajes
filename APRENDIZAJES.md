# 📚 APRENDIZAJES - Mi Agente Viajes

**Proyecto:** Mi Agente Viajes
**Última actualización:** 15 Diciembre 2025

Este archivo documenta lecciones aprendidas, bugs resueltos y decisiones técnicas importantes.

---

## 🎨 Design System - Sesión 21

### Íconos SVG monocromo vs Badges coloridos

**ANTES:** Badges con colores por tipo (verde hotel, azul barco, violeta show)
**DESPUÉS:** Íconos SVG Heroicons en negro, sin texto
**RAZÓN:** Más elegante, consistente con estética Apple/B&O, menos ruido visual
**IMPLEMENTACIÓN:** Heroicons outline 20x20, stroke-width 1.5, color #1f2937

```html
<!-- Ejemplo de uso -->
<div class="type-icons">
    <svg class="type-icon" fill="none" viewBox="0 0 20 20" stroke="currentColor">
        <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z"/>
    </svg>
</div>
```

### Eventos all-day en iCal

- **Hoteles, autos, cruceros largos** → all-day (sin hora específica)
- **Ferries cortos, vuelos, shows** → hora exacta
- **Formato iCal:** `DTSTART;VALUE=DATE` vs `DTSTART` con hora
- **DTEND en all-day:** día DESPUÉS del último (convención iCal)

```python
# Ejemplo: Hotel 3 noches (check-in 21/12, check-out 24/12)
event.add('dtstart', date(2025, 12, 21))  # Primera noche
event.add('dtend', date(2025, 12, 25))    # Día después del check-out (exclusivo)
```

### Privacidad - Precio oculto

**Decisión:** No mostrar precios en UI ni calendario
**RAZÓN:** Calendario puede sincronizarse/compartirse, info sensible
**IMPLEMENTACIÓN:** El precio sigue en BD para uso interno/futuro

---

## 🐛 Bugs y Soluciones - Sesión 21

### Bug: Items no-vuelo desaparecían en grupos

**CAUSA:** Función `deduplicar_vuelos_en_grupo` usaba `numero_vuelo` como clave
Hoteles/shows tienen `numero_vuelo=None` → todos se colapsaban como "duplicados"

**FIX:** Non-vuelo usa `(v.id,)` como clave única

```python
# ANTES (malo)
clave = (v.numero_vuelo, v.fecha_salida, v.origen, v.destino)

# DESPUÉS (correcto)
if v.tipo == 'vuelo':
    clave = (v.numero_vuelo, v.fecha_salida, v.origen, v.destino)
else:
    clave = (v.id,)  # Cada item no-vuelo es único
```

### Bug: Botón Desagrupar oculto

**CAUSA:** CSS tenía `max-height: 2000px` en card-body
Grupos grandes (muchos segmentos) superaban el límite

**FIX:** Aumentar a `max-height: 8000px`

```css
.card:not(.collapsed) .card-body {
    max-height: 8000px;  /* Aumentado desde 2000px */
    opacity: 1;
}
```

### Bug: 4 registros para mismo espectáculo

**CAUSA:** Claude devolvía 4 objetos separados para 4 entradas

**FIX:** Mejorar prompt para consolidar en 1 objeto con `detalles_entradas[]`

```python
# ANTES (malo) - Claude devolvía:
[
  {"tipo": "espectaculo", "evento": "La Fenice", "entradas": 1, ...},
  {"tipo": "espectaculo", "evento": "La Fenice", "entradas": 1, ...},
  {"tipo": "espectaculo", "evento": "La Fenice", "entradas": 1, ...},
  {"tipo": "espectaculo", "evento": "La Fenice", "entradas": 1, ...}
]

# DESPUÉS (correcto) - Claude devuelve:
{
  "tipo": "espectaculo",
  "evento": "Venere e Adone",
  "entradas": 4,
  "detalles_entradas": [
    {"puesto": 1, "ubicacion": "Palco centrale-parapetto", "precio": "€209,00"},
    {"puesto": 2, "ubicacion": "Palco centrale-parapetto", "precio": "€209,00"},
    {"puesto": 3, "ubicacion": "Palco centrale-dietro", "precio": "€165,00"},
    {"puesto": 4, "ubicacion": "Palco centrale-dietro", "precio": "€165,00"}
  ],
  "precio_total": "€748,00"
}
```

**RESULTADO:** 1 registro en BD con array de ubicaciones/precios

### Bug: Título "Viaje a None"

**CAUSA:** `nombre_viaje` en BD ya tenía string `"None"` guardado (no Python `None`)

**FIX:** Validar que `nombre_viaje` no contenga string `"None"` antes de usarlo

```jinja2
{# ANTES (malo) #}
{% if primer_vuelo.nombre_viaje %}
    {% set titulo_default = primer_vuelo.nombre_viaje %}
{% endif %}

{# DESPUÉS (correcto) #}
{% if primer_vuelo.nombre_viaje and 'None' not in primer_vuelo.nombre_viaje %}
    {% set titulo_default = primer_vuelo.nombre_viaje %}
{% endif %}
```

**TAMBIÉN:** Múltiples lugares calculaban título de forma inconsistente → unificado

### Bug: Persistencia de nombre editado

**CAUSA:** Múltiples funciones modifican `nombre_viaje` sin verificar si existe custom

**FUNCIONES AFECTADAS:**
- `carga_rapida`
- `agrupar_automatico`
- `agrupar_manual`
- `desagrupar_grupo`

**FIX:** Pattern de preservación de nombre custom

```python
# Buscar si algún viaje ya tiene nombre_viaje editado manualmente
nombre_existente = next((v.nombre_viaje for v in viajes if v.nombre_viaje), None)

if not nombre_existente:
    # No hay nombre custom, generar uno automático
    nombre_existente = f"Viaje a {ciudad_nombre}"

# Aplicar el nombre (custom o auto) a todos los viajes del grupo
for v in viajes:
    v.nombre_viaje = nombre_existente
```

---

## 🎯 Multi-Tipo de Reservas - MVP15

### Campos dinámicos por tipo

**PROBLEMA:** Tabla `viaje` diseñada para vuelos (numero_vuelo, aerolinea, origen, destino)
**SOLUCIÓN:** Campos genéricos + `raw_data` JSON

| Campo | Uso |
|-------|-----|
| `tipo` | vuelo, hotel, barco, espectaculo, restaurante, actividad, auto, tren, transfer |
| `proveedor` | Aerolínea, hotel, empresa, venue, restaurante |
| `ubicacion` | Dirección, venue, punto de encuentro |
| `precio` | Precio total en cualquier moneda |
| `raw_data` | JSON completo de Claude (fallback para campos no mapeados) |

### Layout condicional en UI

**DECISIÓN:** Diferentes layouts según tipo de reserva

```jinja2
{% if vuelo.tipo == 'vuelo' %}
    {# Transporte: origen → destino #}
    <div class="segment-route">{{ vuelo.origen }} → {{ vuelo.destino }}</div>
{% else %}
    {# Lugares fijos: proveedor + ubicación #}
    <div class="segment-location">
        <div class="proveedor">{{ vuelo.proveedor }}</div>
        <div class="ubicacion">{{ vuelo.ubicacion }}</div>
    </div>
{% endif %}
```

### Whitelist expandida

**ANTES:** 60 dominios (aerolíneas)
**DESPUÉS:** 136 dominios (aerolíneas + hoteles + cruceros + actividades)

**Fuentes agregadas:**
- Hoteles: Booking, Airbnb, Marriott, Hilton, IHG
- Cruceros: MSC, Royal Caribbean, Norwegian, Costa
- Actividades: Civitatis, GetYourGuide, Viator
- Autos: Hertz, Avis, Enterprise, Localiza
- Shows: Ticketmaster, entradas.com
- Restaurantes: OpenTable, TheFork, Resy

---

## 🔧 Técnicas y Patterns

### Deduplicación por contenido

**CONTEXTO:** No todos los emails tienen `codigo_reserva`

**SOLUCIÓN:** Fallback a contenido (vuelo + fecha + ruta)

```python
def check_duplicate_by_content(user_id, numero_vuelo, fecha_salida, origen, destino):
    """Detecta duplicado por contenido del vuelo"""
    if not all([numero_vuelo, fecha_salida]):
        return False

    return Viaje.query.filter_by(
        user_id=user_id,
        numero_vuelo=numero_vuelo,
        fecha_salida=fecha_salida,
        origen=origen,
        destino=destino
    ).first() is not None
```

**USO:**
1. Primero: check por `codigo_reserva`
2. Si no hay código: check por contenido
3. Solo crear viaje si ambos fallan

### Extracción de PDFs adjuntos

**CONTEXTO:** Agencias envían confirmación en PDF, no en body del email

**SOLUCIÓN:** Extraer y procesar PDFs con PyPDF2

```python
def extract_pdf_attachments(service, msg_id, payload):
    """Extrae PDFs de attachments del email"""
    attachments = []

    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('filename', '').lower().endswith('.pdf'):
                att_id = part['body'].get('attachmentId')
                if att_id:
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=msg_id, id=att_id
                    ).execute()

                    data = base64.urlsafe_b64decode(attachment['data'])
                    attachments.append({
                        'filename': part['filename'],
                        'data': data
                    })

    return attachments
```

### Consolidación en prompts de Claude

**TÉCNICA:** Dar ejemplos CORRECTO e INCORRECTO en el prompt

```
IMPORTANTE - CONSOLIDACIÓN DE ENTRADAS:
Para espectáculos/eventos con múltiples entradas del MISMO evento:
- Crear UN SOLO objeto con el total de entradas
- Incluir array "detalles_entradas"
- NO crear objetos separados

Ejemplo CORRECTO:
{
  "tipo": "espectaculo",
  "entradas": 4,
  "detalles_entradas": [...]
}

Ejemplo INCORRECTO (NO hacer esto):
[
  {"tipo": "espectaculo", "entradas": 1},
  {"tipo": "espectaculo", "entradas": 1},
  ...
]
```

---

## 📊 Performance y Optimización

### Deduplicación en grupos

**PROBLEMA:** Vuelos idénticos de distintas reservas se mostraban duplicados
**CONTEXTO:** Cuando 2+ personas reservan mismo vuelo (código diferente, vuelo idéntico)

**SOLUCIÓN:** `deduplicar_vuelos_en_grupo()`

```python
def deduplicar_vuelos_en_grupo(viajes):
    """Combina vuelos idénticos, agrupa pasajeros por código de reserva"""
    vistos = {}

    for viaje in viajes:
        if viaje.tipo == 'vuelo':
            clave = (viaje.numero_vuelo, viaje.fecha_salida, viaje.origen, viaje.destino)
        else:
            clave = (viaje.id,)  # Non-vuelo siempre único

        if clave not in vistos:
            vistos[clave] = viaje
            viaje._es_combinado = False
        else:
            # Combinar pasajeros
            vuelo_base = vistos[clave]
            vuelo_base._es_combinado = True
            # ... merge logic

    return list(vistos.values())
```

### All-day vs Hora específica

**DECISIÓN:** Determinar dinámicamente según tipo y duración

```python
def _es_evento_allday(viaje):
    """Hoteles y autos: siempre all-day"""
    if viaje.tipo in ['hotel', 'auto']:
        return True

    """Cruceros: all-day solo si duran >24h"""
    if viaje.tipo in ['crucero', 'barco']:
        if viaje.fecha_llegada and viaje.fecha_salida:
            duracion = viaje.fecha_llegada - viaje.fecha_salida
            return duracion.total_seconds() > 24 * 3600
        return False

    """Todo lo demás: hora específica"""
    return False
```

---

## 🚨 Decisiones de Producto

### No mostrar precio en UI

**FECHA:** 15 Dic 2025
**RAZÓN:** Privacidad - calendario se sincroniza/comparte
**IMPACTO:** Precio sigue en BD para stats futuras
**ARCHIVOS:**
- `blueprints/calendario.py` - Quitado de description
- `templates/index.html` - Quitado de info-rows

### Título inteligente por tipo

**REGLA:** El título del grupo debe reflejar el tipo de viaje

```python
if tiene_hotel:
    titulo = f"Viaje a {ciudad_hotel}"
elif tiene_barco:
    titulo = f"Viaje a {destino_barco}"
else:
    titulo = f"Viaje a {destino_ultimo_vuelo}"
```

### Íconos monocromo sin texto

**RAZÓN:** Reducir ruido visual, más profesional
**ANTES:** `[VUELO ×5] [HOTEL]`
**DESPUÉS:** `✈️ 🏨`

---

---

## 🐛 Sesión 21 - Bugs Adicionales (15 Dic 2025)

### Bug: 'int' object is not iterable

**CONTEXTO:** Emails de veleros/charters (Moorings, Belize)

**CAUSA:** Claude devuelve `pasajeros: 8` (int) para veleros/charters
El código intentaba iterar como lista: `for p in pasajeros`

**FIX:** Validar `isinstance(pasajeros, int)` antes de iterar

```python
if pasajeros:
    if isinstance(pasajeros, int):
        pasajeros_json = json.dumps([{"cantidad": pasajeros}])
    elif isinstance(pasajeros, list):
        pasajeros_json = json.dumps([{"nombre": p} for p in pasajeros])
```

**UBICACIÓN:** `blueprints/viajes.py` línea 367-373, `blueprints/gmail_webhook.py` línea 365+

### Bug: Gmail OAuth expirado

**SÍNTOMA:** `RefreshError: invalid_client: The OAuth client was not found`

**CAUSA:** Credenciales OAuth de Gmail caducaron o fueron revocadas

**IMPACTO:** Push notifications de Gmail **NO funcionan**. Webhook recibe notificaciones pero no puede procesar emails.

**FIX:** Reconectar Gmail desde la app
1. Ir a app → Perfil → Emails
2. Desconectar Gmail
3. Reconectar Gmail
4. Verificar webhook funciona

### Bug: Expediciones sin fecha

**SÍNTOMA:** `NotNullViolation: null value in column "fecha_salida"`

**CAUSA:** Emails de expediciones (Antártida) no tienen fecha específica. Claude devolvía objeto sin fecha.

**FIX 1:** Prompt de Claude mejorado
```
IMPORTANTE - VALIDACIÓN:
- Si no podés extraer una fecha válida → NO incluyas el objeto en el array
- NUNCA devolver objetos con fecha_salida: null
```

**FIX 2:** Validación pre-guardado en webhook y carga_rapida
```python
fecha_str = v.get('fecha_salida') or v.get('fecha_embarque') or v.get('fecha') or ...
if not fecha_str:
    print(f"⚠️ Reserva sin fecha, ignorando")
    continue
```

### Bug: codigo_reserva demasiado largo

**SÍNTOMA:** `StringDataRightTruncation: value too long for type character varying(50)`

**CAUSA:** Códigos de expediciones muy largos: `Antarctica_Photo_Expedition_with_AntonioS.Chamorro_2026` (60 chars)

**FIX 1:** Aumentar límite en BD
```sql
ALTER TABLE viaje ALTER COLUMN codigo_reserva TYPE VARCHAR(255);
```

**FIX 2:** Truncar en código si es muy largo
```python
if len(codigo) > 250:
    codigo = codigo[:250]
```

---

## 📚 Metodología - Debugging Multi-Capa

**Proceso para bugs de extracción/guardado:**

1. **Identificar síntoma exacto**
   - Error de BD? → Ver constraint violado
   - No aparece en UI? → Ver qué hay en BD

2. **Verificar qué devuelve Claude**
   - Revisar logs: `📝 JSON RECIBIDO DE CLAUDE:`
   - Verificar estructura del objeto

3. **Verificar qué se guarda en BD**
   - Ver logs SQL: `INSERT INTO viaje ...`
   - Ver parámetros enviados

4. **Verificar qué muestra el template**
   - Leer código Jinja2
   - Ver qué variables están disponibles

5. **Buscar la capa donde falla**
   - Claude → Guardado → Template
   - Identificar transformaciones entre capas

**Ejemplos reales:**
- **La Fenice 4 registros:** Falla en capa Claude (prompt)
- **Título "None":** Falla en capa Template (filtros)
- **Expedición sin fecha:** Falla en capa Guardado (validación)

---

## 🧪 Testing con Datos Reales

**Lección:** PDFs reales revelan edge cases que casos de prueba no cubren

**Casos edge encontrados:**
- **La Fenice:** 4 entradas del mismo evento → necesita consolidación
- **Buquebus:** Ferry con vehículos → necesita hora específica
- **Moorings:** Charter con pasajeros como int → necesita validación de tipos
- **Antártida:** Expedición sin fecha confirmada → necesita rechazo graceful

**Pattern:** Siempre que se agrega un tipo nuevo:
1. Probar con PDF/email real
2. Ver qué devuelve Claude
3. Ver qué se guarda
4. Ver qué se muestra
5. Iterar hasta que funcione

---

## 🔄 Historial de Cambios

| Fecha | Aprendizaje |
|-------|-------------|
| 15 Dic 2025 | Documento creado - Sesión 21 |
| 15 Dic 2025 | Design System: SVG monocromo |
| 15 Dic 2025 | Bugs: Desagrupar oculto, título "None", persistencia nombre |
| 15 Dic 2025 | MVP15: Multi-tipo completado |
| 15 Dic 2025 | Privacidad: Precio oculto en UI |
| 15 Dic 2025 | Bugs adicionales: int pasajeros, Gmail OAuth, expediciones, codigo_reserva largo |
| 15 Dic 2025 | Metodología: Debugging multi-capa, Testing con datos reales |

---

*Este archivo es un living document. Agregar aprendizajes significativos después de cada sesión importante.*
