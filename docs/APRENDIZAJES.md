# Aprendizajes del Proyecto Mi Agente Viajes

Registro de errores, soluciones y patrones descubiertos durante el desarrollo.
Objetivo: evitar repetir errores y propagar conocimiento a otros proyectos.

---

## Errores y Soluciones

### 1. Archivos múltiples causan "incompatible messages"
**Problema:** Crear varios archivos en una sola respuesta causa error de sistema
**Causa:** Limitación de Claude Code con múltiples file_create consecutivos
**Solución:** Crear UN archivo a la vez, esperar confirmación del usuario
**Sesión:** Mis Viajes 16
**Aplicable a:** Cualquier proyecto con Claude Code

### 2. Multi-file deployments requieren orden específico
**Problema:** Errores de deploy cuando archivos dependen unos de otros
**Causa:** Orden de creación no respeta dependencias
**Solución:** Agrupar por ubicación (root primero, luego templates, luego static)
**Sesión:** Mis Viajes 16
**Aplicable a:** Proyectos Flask con templates

### 3. Gmail OAuth requiere configuración específica de scopes
**Problema:** Token de Gmail no permite leer emails
**Causa:** Scope incorrecto o insuficiente
**Solución:** Usar scope `gmail.readonly` y verificar en Google Cloud Console
**Sesión:** Mis Viajes 14
**Aplicable a:** Cualquier integración OAuth con Google

### 4. Cloud Run cold starts afectan UX
**Problema:** Primera request después de inactividad tarda ~5 segundos
**Causa:** Container se apaga después de inactividad
**Solución:** Configurar `min-instances=1` (tiene costo) o aceptar el delay
**Sesión:** Mis Viajes 12
**Aplicable a:** Todos los proyectos en Cloud Run

### 5. PDF parsing falla con ciertos formatos
**Problema:** Algunos PDFs de aerolíneas no se parsean correctamente
**Causa:** Estructura no estándar del PDF
**Solución:** Usar Claude API para extracción inteligente en lugar de regex
**Sesión:** Mis Viajes 10
**Aplicable a:** Proyectos que procesan PDFs de terceros

### 6. Verificar estado actual antes de proponer cambios
**Problema:** Proponer fixes para cosas que ya están implementadas
**Causa:** No verificar el estado actual del código/UI antes de sugerir
**Solución:** Siempre verificar en browser/código antes de proponer cambios
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto, especialmente con múltiples sesiones

### 7. Contexto de conversaciones no persiste entre Claude.ai y Claude Code
**Problema:** Claude Code no sabe lo que se discutió en Claude.ai
**Causa:** Son instancias separadas sin memoria compartida
**Solución:** Documentar specs complejas en archivos del repo (ej: docs/MVP14-UX-SPEC.md)
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto con workflow Claude.ai + Claude Code

### 8. gcloud no disponible por defecto en Codespaces
**Problema:** `gcloud: command not found` al intentar deploy
**Causa:** Codespaces no incluye gcloud CLI por defecto
**Solución:** Instalar gcloud + Service Account (ver docs/GCLOUD_SETUP.md)
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto GCP en Codespaces

### 9. Service Account requiere 6 roles específicos para deploy
**Problema:** Deploy falla con "Permission denied" múltiples veces
**Causa:** Cada paso del deploy requiere permisos diferentes
**Solución:** Agregar TODOS los roles de una vez (ver docs/GCLOUD_SETUP.md):
- Administrador de almacenamiento
- Administrador de Artifact Registry  
- Administrador de Cloud Run
- Editor de Cloud Build
- Usuario de cuenta de servicio
- Consumidor de Service Usage
**Sesión:** Meta 1
**Aplicable a:** Cualquier deploy a Cloud Run con Service Account

### 10. Interfaces GCP pueden estar en español
**Problema:** Instrucciones en inglés no coinciden con UI en español
**Causa:** GCP usa el idioma del browser/cuenta
**Solución:** Dar instrucciones en ambos idiomas o usar IDs de roles (ej: `roles/storage.admin`)
**Sesión:** Meta 1
**Aplicable a:** Cualquier documentación de GCP/AWS/Azure

### 11. Permisos de GCP tardan en propagarse
**Problema:** "Permission denied" inmediatamente después de agregar rol
**Causa:** Propagación de permisos no es instantánea
**Solución:** Esperar 1-2 minutos después de agregar roles antes de reintentar
**Sesión:** Meta 1
**Aplicable a:** Cualquier cambio de IAM en GCP

### 12. Codespaces secrets requieren rebuild para aplicar
**Problema:** Variable de entorno no disponible después de agregar secret
**Causa:** Secrets se cargan al crear/rebuild del container
**Solución:** Hacer "Rebuild Container" después de agregar secrets
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto en Codespaces con secrets

### 13. Extensiones VS Code se pierden con Codespace rebuild
**Problema:** Después de rebuild, Claude Code y otras extensiones desaparecen
**Causa:** Codespaces reinstala el container desde cero
**Solución:** Agregar extensiones a .devcontainer/devcontainer.json en customizations.vscode.extensions
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto en Codespaces con extensiones

### 14. settings.json con permisos invertidos
**Problema:** Claude Code no ejecutaba git/gcloud aunque debía
**Causa:** Permisos estaban en "deny" en lugar de "allow"
**Solución:** Revisar settings.json, verificar que comandos deseados estén en "allow"
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto con Claude Code

### 15. settings.local.json conflicta con settings.json
**Problema:** Permisos duplicados o contradictorios entre ambos archivos
**Causa:** Claude Code crea settings.local.json automáticamente con "Yes, and don't ask again"
**Solución:** Consolidar todo en settings.json y eliminar settings.local.json
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto con Claude Code

### 16. Verificar que archivo existe antes de editarlo
**Problema:** Intentar editar archivo que no existe (ej: base.html)
**Causa:** Asumir estructura sin verificar
**Solución:** Usar `ls templates/` o `find . -name "*.html"` antes de editar
**Sesión:** Meta 1
**Aplicable a:** Cualquier edición de código

### 17. "Yes, and don't ask again" para comandos seguros
**Problema:** Claude Code pregunta permiso para cada comando, interrumpe flujo
**Causa:** Comandos no están en allow list
**Solución:** Usar opción 2 "Yes, and don't ask again" para git, gcloud, curl, etc.
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto con Claude Code

### 18. Arquitectura de modelos: Opus + Sonnet
**Problema:** ¿Qué modelo usar en cada capa?
**Decisión:** Opus 4.5 en Claude.ai (planificación, decisiones complejas) + Sonnet 4 en Claude Code (ejecución, tareas específicas)
**Razón:** Opus piensa mejor, Sonnet ejecuta más rápido y económico
**Sesión:** Meta 1
**Aplicable a:** Workflow agéntico con múltiples instancias de Claude

### 19. Sync 🔄 después de cada push
**Problema:** Claude.ai no ve cambios recientes del repo
**Causa:** Project Knowledge no se actualiza automáticamente
**Solución:** Después de git push, hacer sync manual en Claude.ai (botón 🔄)
**Sesión:** Meta 1
**Aplicable a:** Cualquier proyecto con Claude.ai + Project Knowledge

### 20. Jinja2 no permite reasignar variables en loops
**Problema:** Error al intentar reasignar variable dentro de {% for %} loop
**Causa:** Jinja2 no permite `{% set var = valor %}` para modificar variables del scope externo
**Solución:** Usar `{% set ns = namespace(var=valor) %}` y luego `ns.var`
**Sesión:** MVP14-UX
**Aplicable a:** Cualquier proyecto Flask/Jinja2

### 21. Claude Code ignora prompts que empiezan con "/"
**Problema:** Prompt con instrucciones se interpreta como comando slash
**Causa:** Claude Code trata líneas que empiezan con "/" como comandos especiales
**Solución:** No comenzar prompts con "/". Usar "Actualizar..." en lugar de "/actualizar..."
**Sesión:** MVP14-UX
**Aplicable a:** Cualquier uso de Claude Code

### 22. Claude Code se pone lento con contexto >60%
**Problema:** Respuestas lentas cuando el contexto está >60% lleno
**Causa:** Token budget limitado, procesamiento más lento con contexto grande
**Solución:** Iniciar nueva sesión cuando contexto >50%, usar Task tool para exploraciones
**Sesión:** MVP14-UX
**Aplicable a:** Cualquier proyecto con Claude Code

### 23. gcloud --set-env-vars reemplaza todas las variables
**Problema:** Al usar `gcloud run services update --set-env-vars` se perdieron todas las variables existentes
**Causa:** `--set-env-vars` REEMPLAZA todas las variables, no las agrega
**Solución:** Usar `--update-env-vars` para agregar/actualizar sin borrar las existentes
**Sesión:** MVP14h
**Aplicable a:** Cualquier deploy a Cloud Run con múltiples env vars

### 24. DATABASE_URL incorrecta causa errores SSL con Render
**Problema:** App mostraba errores `SSL connection has been closed unexpectedly` al usar BD de Render
**Causa:** Se restauró DATABASE_URL vieja que apuntaba a Render en lugar de Cloud SQL
**Solución:** Verificar que DATABASE_URL apunte a Cloud SQL: `postgresql://postgres:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT:REGION:INSTANCE`
**Sesión:** MVP14h
**Aplicable a:** Proyectos Flask en Cloud Run con Cloud SQL

### 25. Backfill en primera conexión mejora UX dramáticamente
**Problema:** Usuarios conectan cuenta pero no ven viajes históricos, solo futuros
**Causa:** Scanner por defecto busca últimos 30 días, pierde emails más antiguos
**Solución:** Detectar primera conexión (last_scan=NULL) y buscar 180 días, pero solo crear viajes futuros
**Sesión:** MVP14h
**Aplicable a:** Cualquier integración de email/calendario que sincroniza datos históricos

### 26. Campos de BD deben tener defaults para evitar rollbacks silenciosos
**Problema:** Scanner reporta "4 viajes creados" pero no aparecen en la app
**Causa:** Campo NOT NULL sin default causa rollback de transacción completa, pero counter ya incrementó
**Solución:** Todos los campos NOT NULL deben tener `default=''` o `default=0` en el modelo
**Sesión:** MVP14h
**Aplicable a:** Cualquier proyecto SQLAlchemy/Flask

### 27. Claude Code local (VS Code + Mac) funciona igual que Codespaces sin límites
**Problema:** Codespaces tiene límite de 120 horas/mes en plan free
**Causa:** GitHub cobra por uso de Codespaces
**Solución:** Usar Claude Code localmente: `brew install node && npm install -g @anthropic-ai/claude-code && claude`
**Sesión:** MVP14h
**Aplicable a:** Cualquier proyecto que usa Claude Code

### 28. --update-env-vars vs --set-env-vars: uno agrega, el otro reemplaza
**Problema:** Después de usar `--set-env-vars` para configurar una variable, todas las demás desaparecen
**Causa:** `--set-env-vars` reemplaza TODAS las variables, `--update-env-vars` solo actualiza/agrega las especificadas
**Solución:** Usar siempre `--update-env-vars` para agregar o modificar variables sin afectar las existentes
**Sesión:** MVP14h
**Aplicable a:** Cualquier deploy a Cloud Run con múltiples env vars

### 29. Template inheritance reduce código duplicado significativamente
**Problema:** Cada template tenía ~100-200 líneas de CSS duplicado
**Solución:** Crear base.html con header, menú y estilos comunes. Templates extienden con {% extends "base.html" %}
**Resultado:** Reducción de 67-93 líneas por template, menú consistente en toda la app
**Sesión:** Mis Viajes 20
**Aplicable a:** Cualquier proyecto Flask/Jinja con múltiples templates

### 30. OAuth Client ID debe coincidir con el proyecto correcto
**Problema:** "OAuth client was not found" / "invalid_client" error
**Causa:** Client ID en Cloud Run era de otro proyecto GCP (684337806599 vs 454542398872)
**Solución:** Verificar en Google Console que el Client ID existe y actualizar env vars con el correcto
**Sesión:** Mis Viajes 20
**Aplicable a:** Cualquier integración OAuth con múltiples proyectos GCP

---

## Patrones Exitosos

### A. Workflow de desarrollo MVP-a-MVP
1. Definir scope mínimo del MVP
2. Implementar en una sesión
3. Deploy + smoke tests
4. Validar con usuario real
5. Documentar aprendizajes
6. Siguiente MVP

### B. Commits frecuentes con mensajes descriptivos
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `refactor:` mejora sin cambio de comportamiento
- `docs:` documentación
- `style:` formato, no afecta lógica

### C. Smoke tests post-deploy
```bash
./smoke_tests.sh
```
Verificar endpoints críticos antes de considerar deploy exitoso.

### D. Documentación en el repo
- README.md: setup inicial
- METODOLOGIA_TRABAJO.md: cómo trabajamos
- docs/: documentación técnica específica
- APRENDIZAJES.md: este archivo

### E. Workflow agéntico de 3 capas
1. **Andy**: Visión, decisiones de producto, validación
2. **Claude.ai**: Arquitectura, planificación, diseño
3. **Claude Code**: Implementación, git, deploy

---

## 🔄 Sesión 22 - Fixes y Decisiones (15 Dic 2025)

### Fix: Sistema 1 (misviajes@) multi-tipo

**PROBLEMA:** Reenvío de emails a misviajes@gamberg.com.ar solo procesaba vuelos. BQB, Moorings, Antártida se ignoraban o guardaban con campos incorrectos.

**SÍNTOMAS:**
- BQB mostraba código de reserva como nombre de pasajero
- Origen/destino no aparecían en ferries/cruceros
- Faltaban horas de llegada
- Antártida: "Hijo de Andres Gamberg" en vez de "MARTIN GAMBERG"

**CAUSA RAÍZ:** `gmail_to_db.py` tenía:
1. `tipo='vuelo'` hardcodeado (línea 309)
2. Mapeo de campos genérico, diferente a `carga_rapida()`
3. Pasajeros recibía código de reserva en vez de lista de nombres

**SOLUCIÓN:** Replicar lógica exacta de `blueprints/viajes.py` `carga_rapida()` en `gmail_to_db.py`:
- Mapeo específico por tipo (crucero→puerto_embarque, hotel→huespedes, etc.)
- Formateo correcto de pasajeros como lista de dicts con nombres
- Normalización de campos de fecha por tipo

**COMMITS:** 2cf2099, 34dd070, 7910879, 63b5292, 48504e1, d3e62bc

**LECCIÓN:** Cuando dos flujos hacen lo mismo (guardar reserva), deben usar la misma lógica. No reinventar el mapeo.

### Decisión de producto: Edición > Extracción perfecta

**CONTEXTO:** Después de múltiples fixes, seguían apareciendo edge cases:
- Moorings: pasajero vacío (Claude no extrajo nombre)
- Antártida: "Hijo de Andres Gamberg" en vez de "MARTIN GAMBERG" (Claude infirió mal)
- BQB: vehículos/patentes no se muestran
- Nadine Sierra: faltan hora y detalles de entradas

**DECISIÓN:** En vez de perseguir extracción 100% perfecta (infinitos edge cases), implementar MVP-EDIT de edición completa de reservas.

**BENEFICIOS:**
- Claude hace 80% del trabajo de extracción
- Usuario corrige/completa el 20% restante
- Un solo MVP resuelve todos los edge cases futuros
- Menos código de extracción = menos bugs

### Workflow agéntico - Lecciones

**ERROR COMETIDO:** Claude.ai intentó ejecutar comandos gcloud/SQL en su entorno (no tiene acceso).

**CORRECCIÓN IMPLEMENTADA:**
1. Claude.ai NO ejecuta comandos de infraestructura
2. Para diagnóstico de producción → preparar prompt completo para Claude Code (que SÍ tiene acceso)
3. Buscar en repo/memoria ANTES de preguntar a Andy
4. Separar siempre en bloques independientes: "Para tu terminal" vs "Prompt para Claude Code"

---

## 🔄 Sesión 24 - MVP-EDIT y Fixes (14 Dic 2025)

### Jinja2 no soporta {% continue %} ni {% break %}
**PROBLEMA:** Error 500 con estas instrucciones dentro de loops/condicionales

**SOLUCIÓN:** Usar `{% if %}...{% endif %}` anidados en lugar de break/continue

**APLICABLE A:** Cualquier proyecto Flask/Jinja2

**EJEMPLO:**
```jinja2
{# ❌ NO funciona #}
{% for item in items %}
    {% if condition %}
        {% break %}
    {% endif %}
{% endfor %}

{# ✅ Funciona #}
{% for item in items %}
    {% if condition %}
        {# Mostrar algo #}
    {% endif %}
{% endfor %}
```

### Cloud Run no captura logging.info()
**PROBLEMA:** Logs de aplicación no visibles en Cloud Logging, solo HTTP requests

**SOLUCIÓN:**
1. Usar `print()` en lugar de `logging.info()`
2. Agregar `ENV PYTHONUNBUFFERED=1` en Dockerfile
3. Agregar `--access-logfile -` y `--error-logfile -` a gunicorn
4. Agregar `--log-level info` a gunicorn

**APLICABLE A:** Proyectos Python/Gunicorn en Cloud Run

**EJEMPLO:**
```dockerfile
ENV PYTHONUNBUFFERED=1
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:app"]
```

### Validar tipo antes de iterar en templates
**PROBLEMA:** Error "object of type 'int' has no len()" cuando datos legacy tienen formato inconsistente (ej: `pasajeros: 4` en vez de `pasajeros: [{...}]`)

**SOLUCIÓN:** Validar que es iterable, no string, y no number antes de usar `|length` o iterar

**APLICABLE A:** Templates que manejan datos de BD con formatos mixtos/legacy

**EJEMPLO:**
```jinja2
{# ❌ Falla si pasajeros es int #}
{% if d.pasajeros and d.pasajeros|length > 0 %}
    {% for p in d.pasajeros %}
        {{ p.nombre }}
    {% endfor %}
{% endif %}

{# ✅ Maneja int, string, array #}
{% if d.pasajeros and (d.pasajeros is iterable and d.pasajeros is not string and d.pasajeros is not number) and d.pasajeros|length > 0 %}
    {% for p in d.pasajeros %}
        {{ p.nombre }}
    {% endfor %}
{% endif %}
```

### Flujos duplicados deben usar misma función
**PROBLEMA:** `microsoft_scanner.py` guardaba `pasajeros='[]'` hardcodeado, ignorando datos de Claude. `gmail_to_db.py` usaba `save_reservation()` correctamente.

**SOLUCIÓN:** Ambos scanners (Gmail y Microsoft) deben usar `save_reservation()` para guardar reservas

**APLICABLE A:** Sistemas con múltiples puntos de entrada que hacen la misma operación

**BENEFICIOS:**
- Una sola función de mapeo → menos duplicación
- Bugs se fixean en un solo lugar
- Cambios de schema se propagan automáticamente
- Más fácil de mantener

**LECCIÓN:** Cuando dos flujos hacen lo mismo, abstraer en función compartida desde el principio.

### Microsoft scanner logging detallado
**PROBLEMA:** No se podía diagnosticar qué extraía Claude ni por qué se marcaban duplicados

**SOLUCIÓN:** Agregar logging detallado en cada paso:
```python
print(f"✅ Claude extrajo {len(vuelos)} reserva(s)")
for idx, vuelo in enumerate(vuelos):
    print(f"  [{idx+1}] {vuelo.get('origen')} → {vuelo.get('destino')} | Pasajeros: {len(vuelo.get('pasajeros', []))}")

if codigo and check_duplicate(codigo, user_id):
    print(f"⏭️ Duplicado por código: {codigo}")
```

**APLICABLE A:** Cualquier sistema de procesamiento asíncrono (crons, workers, webhooks)

**BENEFICIOS:**
- Debugging más rápido
- Visibilidad de qué está pasando en producción
- Usuarios pueden reportar problemas específicos con contexto

---

## Sesión 26 (17 Dic 2025)

### Tipografía accesible con rem
- **Problema**: font-size en px ignora configuración "Texto más grande" de iOS/Android
- **Solución**: Migrar todo a rem con `html { font-size: 100%; -webkit-text-size-adjust: 100%; }`
- **Escala**: 16px = 1rem base, mínimo 0.75rem (12px) para legibilidad
- **Archivos**: base.html, index.html, login.html, y todos los templates standalone

### JavaScript no accede a preferencia 12h/24h del OS
- **Problema**: `navigator.language` solo devuelve idioma, no preferencia de formato hora
- **Solución**: Sistema híbrido:
  1. Campo `formato_hora` en BD (null=auto, '24h', '12h')
  2. Heurística por locale (US/AU/PH → 12h, resto → 24h)
  3. UI en Preferencias para override manual
- **Beneficio**: Funciona automático para mayoría, configurable para el resto

### Flask-Migrate en Cloud Run
- **Problema**: Deploy de código NO ejecuta migraciones automáticamente
- **Síntoma**: App caída con 500 porque columna no existe
- **Solución**: Ejecutar migración manualmente post-deploy:
```bash
  # Opción 1: Cloud Run Job
  # Opción 2: Script directo con DATABASE_URL
```
- **Prevención**: Siempre verificar que columnas nuevas existan después de deploy

### Auto-capitalización CSS
- **Solución**: `text-transform: capitalize` en inputs de nombres y ciudades
- **Limitación**: Solo visual, el valor guardado mantiene el case original
- **Campos**: origen, destino, puertos, nombres de pasajeros

---

## Checklist para Nuevos Proyectos

### Setup inicial
- [ ] Crear repo en GitHub
- [ ] Configurar Codespaces
- [ ] Copiar scripts/setup-gcloud.sh
- [ ] Crear Service Account con 6 roles
- [ ] Agregar GCLOUD_SERVICE_KEY como secret
- [ ] Ejecutar setup-gcloud.sh
- [ ] Verificar deploy funciona

### Documentación mínima
- [ ] README.md con setup
- [ ] APRENDIZAJES.md (copiar estructura)
- [ ] docs/GCLOUD_SETUP.md (copiar y adaptar)

### Claude Code
- [ ] Crear CLAUDE.md con instrucciones
- [ ] Configurar .claude/settings.json con permisos
- [ ] Probar ciclo completo: edit → commit → push → deploy

---

## Decisiones Arquitectónicas Descartadas

### Modelo de Eventos con tablas de extensión (Dic 2025)

**Propuesta original:** Crear tabla base Evento con tablas de extensión 1:1 (DetalleVuelo, DetalleHotel, etc.)

**Por qué se descartó:** Se optó por JSONB en columna datos porque:
- Más simple de implementar
- No requiere JOINs
- Flexibilidad para agregar campos sin migraciones
- Claude ya retorna JSON estructurado

**Decisión final:** Modelo híbrido con columnas legacy para índices + JSONB para datos completos.

---

## Sesión 26 (17 Dic 2025)

### 31. Tipografía accesible con rem
**Problema:** iOS/Android ignoraban preferencias de texto grande porque usábamos px fijos
**Solución:** Migrar de px a rem con base 16px, agregar html { font-size: 100%; -webkit-text-size-adjust: 100%; }
**Mínimo:** 0.75rem (12px) para legibilidad

### 32. JavaScript no accede a preferencia 12h/24h del OS
**Problema:** navigator.language solo devuelve idioma, no preferencia de formato hora
**Solución:** Sistema híbrido: preferencia en BD (null/24h/12h) + heurística por locale + UI en Preferencias

### 33. Flask-Migrate en Cloud Run no es automático
**Problema:** Deploy NO ejecuta flask db upgrade automáticamente
**Solución:** Verificar columnas nuevas existen post-deploy, usar Cloud Run Job o script manual

### 34. Instrucciones para Claude Code deben ser ultra-específicas
**Problema:** Tasks "sencillos" como agregar menú kebab requirieron múltiples correcciones (centrado, z-index, overflow)
**Causa raíz:** Instrucciones vagas asumen que CC "entenderá" el contexto visual
**Solución:** Antes de enviar prompt a CC:
1. Especificar dimensiones exactas (px/rem, colores hex, clases Tailwind)
2. Describir posición relativa a elementos existentes
3. Listar casos edge (texto largo, mobile, etc.)
4. Incluir criterio de verificación visual
**Regla:** Si el task requiere UI, incluir wireframe ASCII o referencia visual
**Sesión:** 27

### 35. Emails deben seguir el Design System
**Contexto:** Emails de notificación (check-in, FR24 changes) usan CSS inline
**Principio:** Mantener consistencia visual con la app:
- Colores: usar misma paleta (--text: #1d1d1f, --text-muted: #6e6e73, --accent: #0071e3)
- Tipografía: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- Border-radius: 12px para cards, 8px para elementos internos
- Sin emojis decorativos excesivos, preferir iconos SVG cuando sea posible
**Aplicable a:** Todos los emails transaccionales futuros
**Sesión:** 27

---

## Sesión 27: Auditoría UX/Técnica (17-18 Dic 2025)

### 36. Verificar deuda técnica antes de migraciones BD
**Contexto:** Antes de agregar columnas nuevas, revisar si ya existen en modelo
**Problema:** Campos FR24 ya existían pero no se usaban
**Solución:** Auditoría de schema antes de proponer cambios
**Aplicable a:** Cualquier migración de BD

### 37. Deploy incremental con sync entre prompts
**Contexto:** Cambios grandes (4+ archivos) deben dividirse
**Problema:** Un error pequeño se propaga y es difícil de diagnosticar
**Solución:** Commit → Deploy → Verificar → Siguiente cambio
**Aplicable a:** Refactors de UI, cambios estructurales

### 38. Inconsistencias de design system emergen con features nuevas
**Contexto:** Badges/menú nuevos revelaron divergencia base.html vs index.html
**Problema:** Estilos duplicados, comportamientos diferentes
**Solución:** Auditoría completa cuando se detecta primera inconsistencia
**Aplicable a:** Cualquier feature que toque múltiples templates

### 39. Detección de duplicados debe considerar múltiples campos
**Contexto:** Mismo PNR pero año diferente = viaje nuevo, no duplicado
**Problema:** Solo verificaba codigo_reserva, ignoraba fecha
**Solución:** Verificar código + fecha (diferencia >90 días = permitir)
**Aplicable a:** Cualquier lógica de deduplicación

### 40. Benchmark contra líderes antes de implementar
**Contexto:** Auditoría UX comparó con Flighty, TripIt, Kayak
**Beneficio:** Identificar gaps y oportunidades de diferenciación
**Insight clave:** Flighty ganó Apple Design Award por ser "boringly obvious"
**Aplicable a:** Cualquier feature de UX importante

---

## Sesión 28: Fix Menú Kebab Segmentos Individuales (19 Dic 2025)

### 41. Menú kebab debe renderizarse para segmentos individuales
**Problema:** Cruceros/barcos creados manualmente no mostraban el menú de 3 puntitos (editar/eliminar)
**Causa raíz:** El menú kebab solo se renderizaba dentro del bloque `{% if es_multi %}`, ignorando viajes de un solo segmento
**Solución:** Agregar bloque `{% else %}` con el menú para segmentos individuales, con CSS `.segment-header-single` posicionado absoluto
**Sesión:** 28
**Aplicable a:** Cualquier acción que deba estar disponible tanto en grupos como en segmentos individuales

---

## Sesión 31: OAuth Fixes y Email Filter (23 Dic 2025)

### 42. db.create_all() NO agrega columnas a tablas existentes
**Problema:** App caída con "column email_connection.last_expiry_warning does not exist"
**Causa:** Agregué campo al modelo pero `db.create_all()` solo crea tablas nuevas, no modifica existentes
**Solución:** Usar `ALTER TABLE ADD COLUMN IF NOT EXISTS` en endpoint migrate-db
**Sesión:** 31
**Aplicable a:** Cualquier proyecto Flask/SQLAlchemy sin Flask-Migrate

### 43. Email filter debe incluir nombres de adjuntos, no solo subject+body
**Problema:** Email con subject "Tra prueba" descartado aunque tenía PDF "Reserva de viaje..."
**Causa:** `email_parece_reserva()` solo revisaba subject + body[:2000]
**Solución:** Extraer nombres de archivos adjuntos del payload (sin descargar contenido) e incluirlos en el filtro
**Sesión:** 31
**Aplicable a:** Cualquier sistema de filtrado de emails con adjuntos

### 44. Microsoft OAuth token_expiry debe guardarse explícitamente
**Problema:** Scanner Microsoft daba 401 aunque tenía refresh_token válido
**Causa:** `token_expiry` siempre era NULL, entonces `is_token_expired()` nunca triggereaba refresh
**Solución:** Calcular y guardar token_expiry en connect Y en refresh: `datetime.utcnow() + timedelta(seconds=expires_in - 300)`
**Sesión:** 31
**Aplicable a:** Cualquier integración OAuth que dependa de token expiry

### 45. Gmail watches expiran cada 7 días
**Problema:** Gmail push notifications dejaron de llegar silenciosamente
**Causa:** Gmail API watches tienen máximo 7 días de vida
**Solución:** Agregar `renew_expired_watches()` al cron check-flights que corre cada hora
**Sesión:** 31
**Aplicable a:** Cualquier integración con Gmail Push Notifications

### 46. Microsoft refresh tokens expiran después de 90 días de inactividad
**Problema:** Usuarios que no reciben emails de viaje por 90 días pierden la conexión
**Causa:** Política de Microsoft - refresh tokens inactivos expiran
**Solución:** Sistema proactivo de avisos a los 60 días de inactividad con email al usuario
**Sesión:** 31
**Aplicable a:** Cualquier app con Microsoft OAuth donde usuarios pueden tener períodos de inactividad

### 47. Deduplicación de vuelos debe considerar campos de identidad inmutables
**Problema:** Vuelo de vuelta sobreescribía vuelo de ida (ambos con mismo PNR)
**Causa:** Merge actualizaba todos los campos incluyendo numero_vuelo, origen, destino
**Solución:** Campos inmutables en merge: `['tipo', 'codigo_reserva', 'numero_vuelo', 'origen', 'destino', 'fecha_salida', 'hora_salida']`
**Sesión:** 31
**Aplicable a:** Cualquier sistema de merge/update de registros con campos de identidad

### 48. iOS requiere apple-touch-icon en raíz
**Problema:** iOS ignora el meta tag apple-touch-icon y muestra inicial genérica
**Causa:** Safari busca /apple-touch-icon.png en raíz antes de leer meta tags
**Solución:** Servir /apple-touch-icon.png desde raíz además del meta tag
**Sesión:** 32
**Aplicable a:** Cualquier PWA que quiera icono correcto en iOS

### 49. PWA offline requiere visita previa
**Contexto:** IndexedDB se llena cuando el usuario navega online
**Implicación:** Primera visita debe ser online para cachear datos
**Solución:** Documentar en UX que modo offline solo funciona después de visita inicial
**Sesión:** 32
**Aplicable a:** Cualquier PWA con datos dinámicos offline

### 50. Tracking de emails procesados reduce costos API 95%
**Problema:** Cron cada 15 min reprocesaba los mismos ~10 emails, generando ~960 llamadas a Claude/día ($10/día)
**Causa:** No había tracking de qué emails ya se procesaron - se llamaba a Claude para cada email en cada ejecución del cron
**Solución:**
1. Nuevo modelo `ProcessedEmail` con `connection_id` + `message_id` (unique constraint)
2. Verificar si email existe ANTES de llamar a Claude
3. Marcar email como procesado DESPUÉS de llamar a Claude (con o sin reservas)
4. Cambiar modelo de Sonnet ($3/M tokens) a Haiku ($0.25/M tokens) - suficiente para extracción de datos estructurados
**Resultado:** De ~$300/mes a ~$10-20/mes en API costs
**Archivos modificados:** models.py, blueprints/gmail_webhook.py, utils/gmail_scanner.py, utils/microsoft_scanner.py, utils/claude.py
**Sesión:** Mis Viajes 34
**Aplicable a:** Cualquier proceso batch/cron que use LLMs - siempre trackear qué items ya se procesaron

### 51. Haiku es suficiente para extracción de datos estructurados
**Problema:** Usar Sonnet para extraer JSON de emails es overkill y caro
**Causa:** Se eligió Sonnet por defecto sin evaluar si era necesario
**Solución:** Haiku ($0.25/M tokens) extrae datos estructurados igual de bien que Sonnet ($3/M tokens) para este caso de uso
**Cuándo usar cada modelo:**
- Haiku: extracción de datos, parsing, clasificación, tareas simples
- Sonnet: razonamiento complejo, código, análisis profundo
- Opus: tareas que requieren máxima inteligencia
**Sesión:** Mis Viajes 34
**Aplicable a:** Cualquier uso de Claude API - elegir el modelo mínimo necesario

### 52. Reservas manuales guardan datos en JSONB
**Problema:** Calendario mostraba horarios incorrectos para vuelos cargados manualmente
**Causa:** El código leía `viaje.hora_salida` directo de columna legacy, pero reservas manuales guardan en `viaje.datos` (JSONB)
**Solución:** Siempre usar `get_dato(viaje, 'campo')` que lee JSONB con fallback a legacy
**Sesión:** 35
**Aplicable a:** Cualquier código que lea datos de reservas
