# 🤖 Metodología de Trabajo AI-Assisted Development

**Proyecto:** Mi Agente Viajes
**Última actualización:** 15 Diciembre 2025
**Stack:** Flask + PostgreSQL + Google Cloud Run

---

## 📋 Índice

0. [Primera Acción Obligatoria](#primera-acción-obligatoria) 🚨 CRÍTICO
1. [Sistema Agéntico](#sistema-agéntico) ⭐ NUEVO
2. [Setup del Entorno](#setup-del-entorno)
3. [Flujo de Desarrollo](#flujo-de-desarrollo)
4. [Estructura de Archivos para Deploy](#estructura-de-archivos-para-deploy)
5. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
6. [Convenciones de Comunicación](#convenciones-de-comunicación)
7. [Testing](#testing)
8. [Gestión de Sesiones con Claude](#gestión-de-sesiones-con-claude)
9. [Troubleshooting](#troubleshooting)

---

## 🚨 Primera Acción Obligatoria

**ANTES DE HACER CUALQUIER COSA**, leer estos archivos del repo en orden:

### Lectura Obligatoria (en orden)

1. **ROADMAP.md** - Estado actual del proyecto y próximos pasos
   - ✅ MVPs completados
   - 📋 Próximos MVPs (prioridades)
   - 🔴 Bugs conocidos pendientes

2. **docs/APRENDIZAJES.md** - Bugs resueltos, patrones y decisiones
   - 🐛 Bugs históricos y soluciones
   - 🎨 Design System (íconos, layout, UX)
   - 🔧 Técnicas y patterns (deduplicación, extracción, validación)
   - 📊 Performance y optimización
   - 🚨 Decisiones de producto

3. **METODOLOGIA_TRABAJO.md** - Este archivo
   - 🤖 Sistema agéntico (3 capas)
   - 🔧 Setup y workflow
   - 📝 Convenciones de código y commits

4. **UX_UI_ROADMAP.md** (si existe) - Decisiones de experiencia de usuario
   - Paleta de colores
   - Tipografía
   - Componentes UI

5. **docs/WORKFLOW_AGENTICO.md** - Sistema de 3 capas detallado
   - Roles: Andy (Humano) → Claude.ai (Arquitecto) → Claude Code (Ejecutor)
   - Workflow de decisiones

6. **DESIGN_SYSTEM.md** (si existe) - Sistema de diseño
   - Paleta de colores
   - Tipografía
   - Iconos (Heroicons)
   - Componentes

### ⚠️ Importante

**NO empezar a trabajar sin leer estos archivos.**

La información está en el repo. Buscar antes de preguntar. Andy es la última opción.

**Principio clave:** Claude debe buscar en:
1. Project Knowledge (repo sincronizado)
2. Conversaciones anteriores (conversation_search si está disponible)
3. Documentación del proyecto (archivos arriba)
4. Código fuente (Read, Grep, Glob)

**Solo entonces** preguntar a Andy si algo no está documentado.

---

## 🤖 Sistema Agéntico

> **Implementado:** 12 Diciembre 2025 (Meta 1)

Este proyecto usa un sistema de trabajo de tres capas:

```
Andy (Humano) → Claude.ai (Arquitecto) → Claude Code (Ejecutor)
```

### Archivos del sistema

| Archivo | Propósito |
|---------|-----------|
| CLAUDE.md | Manifiesto operativo |
| .claude/settings.json | Permisos para Claude Code |
| docs/WORKFLOW_AGENTICO.md | Setup completo |
| docs/APRENDIZAJES.md | Lecciones aprendidas |

### Principio fundamental

Andy es la última opción. Claude debe buscar en Project Knowledge, conversaciones pasadas, y terminal antes de preguntar.

---

## 🔧 Setup del Entorno

### GitHub + Claude Integration

1. **Conectar GitHub a Claude:**
   - Claude.ai → Configuración → Conectores → GitHub → Conectar
   - Autorizar app "claude-for-github"

2. **Agregar repo a Project Knowledge:**
   - En el proyecto de Claude → Archivos (Project Knowledge)
   - Click "+" → GitHub → Seleccionar repo
   - Seleccionar todos los archivos

3. **Sincronizar cambios:**
   - Después de cada `git push`, click en 🔄 en sección Archivos
   - Claude tendrá acceso al código actualizado

### GitHub Codespaces

- **Abrir:** github.com/[usuario]/[repo] → Code → Codespaces → Create/Open
- **Es básicamente VS Code en el navegador** con terminal integrada
- **gcloud ya configurado** (si se hizo setup previo)
- **Límite:** 120 horas/mes en plan free

### Setup Local (alternativa a Codespaces)

**Ideal para:** Desarrollo sin límites de horas, mejor performance en Mac/Linux

1. **Instalar Node.js (si no lo tenés):**
   ```bash
   brew install node
   ```

2. **Instalar Claude Code CLI:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

3. **Clonar repo:**
   ```bash
   git clone https://github.com/[usuario]/mi-agente-viajes.git
   cd mi-agente-viajes
   ```

4. **Abrir en VS Code:**
   ```bash
   code .
   ```

5. **Iniciar Claude Code:**
   - Abrir terminal integrada en VS Code (Ctrl+`)
   - Ejecutar: `claude`
   - Claude Code funciona igual que en Codespaces

**Ventajas:**
- ✅ Sin límites de horas
- ✅ Mejor performance (local vs cloud)
- ✅ Funciona offline para edición
- ✅ Mismo workflow que Codespaces

**Nota:** Configurar gcloud localmente usando `scripts/setup-gcloud.sh`

### Credenciales y Variables de Entorno

```bash
# Ver variables en Cloud Run
gcloud run services describe mi-agente-viajes --region us-east1 --format='value(spec.template.spec.containers[0].env)'

# Actualizar variable
gcloud run services update mi-agente-viajes --update-env-vars KEY=value --region us-east1
```

---

## 🔄 Flujo de Desarrollo

### Ciclo típico de una feature

```
1. Discutir requerimiento con Claude (claude.ai)
2. Claude prepara instrucciones de edición
3. Usuario copia instrucciones a Claude Code (sidebar en Codespaces)
4. Claude Code aplica cambios, usuario confirma
5. Usuario ejecuta en terminal: git add . && git commit -m "mensaje" && git push
6. Usuario ejecuta en terminal: gcloud run deploy...
7. Smoke tests: ./smoke_tests.sh
8. Sync repo en Claude (🔄 en Project Knowledge)
```

### Workflow Claude.ai + Claude Code (Codespaces)

| Claude.ai (esta ventana) | Claude Code (sidebar Codespaces) |
|--------------------------|----------------------------------|
| Planning, arquitectura, research | Ejecutar ediciones en archivos |
| Ve todo el contexto del proyecto | Ve solo archivos locales |
| Prepara instrucciones detalladas | Aplica cambios, muestra diff |
| NO puede editar archivos | ✅ Puede hacer git/deploy (Meta 1) |

**Reglas (Meta 1 - Actualizado):**
- Claude Code puede ejecutar git add, commit, push
- Claude Code puede ejecutar gcloud deploy
- Claude Code puede ejecutar smoke tests
- Andy solo aprueba decisiones de producto/UX

### Comandos frecuentes

```bash
# Ver cambios pendientes
git status

# Commit y push en un comando
git add . && git commit -m "descripción del cambio" && git push

# Deploy a Cloud Run
gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated

# Ver logs de Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mi-agente-viajes" --limit 30
```

---

## 📁 Estructura de Archivos para Deploy

### Convención para entrega de archivos

Cuando Claude prepara archivos para deploy, los organiza así:

```
outputs/
├── INSTRUCCIONES.txt      # Pasos claros y concisos
├── raiz/                  # Archivos para raíz del proyecto
│   ├── app.py
│   ├── auth.py
│   └── requirements.txt
├── blueprints/            # Archivos para carpeta blueprints/
│   ├── __init__.py
│   ├── viajes.py
│   ├── calendario.py
│   └── api.py
├── utils/                 # Archivos para carpeta utils/
│   ├── __init__.py
│   ├── iata.py
│   ├── claude.py
│   └── helpers.py
└── templates/             # Archivos para carpeta templates/
    ├── login.html
    └── nueva_pagina.html
```

### Instrucciones estándar

```
INSTRUCCIONES PARA DEPLOY
=========================

1. Descargá todo (se baja como .zip)
2. Descomprimí la carpeta
3. En Codespace:
   - Arrastrá contenido de "raiz/" → raíz del proyecto
   - Arrastrá contenido de "blueprints/" → carpeta blueprints/
   - Arrastrá contenido de "utils/" → carpeta utils/
   - Arrastrá contenido de "templates/" → carpeta templates/
   - Reemplazar cuando pregunte
4. En terminal: git status (verificar archivos)
5. Commit: git add . && git commit -m "mensaje" && git push
6. Deploy: gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated
7. Smoke tests: ./smoke_tests.sh
8. Sync en Claude (🔄)
```

---

## 🏗️ Arquitectura del Proyecto

### Estructura actual (post-refactor 9 Dic 2025)

```
mi-agente-viajes/
├── app.py                 # 75 líneas - Config + Factory + Blueprints
├── auth.py                # Autenticación Flask-Login
├── models.py              # SQLAlchemy models (User, Viaje, UserEmail)
├── blueprints/
│   ├── __init__.py        # Exports de blueprints
│   ├── viajes.py          # Rutas principales: /, /agregar, /perfil, etc.
│   ├── calendario.py      # Calendar feed, export, regenerate token
│   └── api.py             # API endpoints, cron jobs, migrate-db
├── utils/
│   ├── __init__.py        # Exports de utilidades
│   ├── iata.py            # Diccionario IATA → Ciudad
│   ├── claude.py          # Extracción con Claude API
│   └── helpers.py         # Funciones auxiliares
├── templates/             # Jinja2 templates
├── static/                # CSS, JS, imágenes
├── email_processor.py     # Gmail API helpers
├── gmail_to_db.py         # Orquesta email→BD
├── flight_monitor.py      # FR24 API
├── scheduler.py           # Lógica de frecuencia dinámica
└── smoke_tests.sh         # Tests de producción
```

### Blueprints

| Blueprint | Prefijo | Responsabilidad |
|-----------|---------|-----------------|
| `viajes_bp` | `/` | Homepage, CRUD viajes, perfil usuario |
| `calendario_bp` | `/` | Calendar feeds, export iCal |
| `api_bp` | `/api/`, `/cron/` | Endpoints JSON, cron jobs, migración |

### Modelos

| Modelo | Campos clave | Relaciones |
|--------|--------------|------------|
| `User` | email, password_hash, nombre, nombre_pax, apellido_pax, calendar_token, combinar_vuelos | has_many: Viaje, UserEmail |
| `Viaje` | user_id, tipo, origen, destino, fecha_salida, grupo_viaje, pasajeros | belongs_to: User |
| `UserEmail` | user_id, email, verificado | belongs_to: User |

---

## 💬 Convenciones de Comunicación

### Lo que funciona bien

| Práctica | Por qué |
|----------|---------|
| Screenshots | Claude puede ver UI, errores, estado actual |
| Copy-paste de terminal | Muestra output exacto |
| Links clickeables | Usuario puede ir directo sin copiar URLs |
| Tablas para opciones | Fácil comparar y elegir |
| Chunks pequeños | Evita overwhelm, permite validar paso a paso |

### Preferencias del usuario (Andy)

- **Links clickeables** en lugar de URLs para copiar
- **Instrucciones claras y secuenciales** para tareas mecánicas
- **Discusión de opciones** antes de implementar features complejas
- **Validar decisiones** de diseño antes de codear
- **Minimizar riesgo de error** en procesos manuales

### Señales para usar herramientas

| El usuario dice... | Claude debe... |
|--------------------|----------------|
| "deployar", "subir cambios" | Preparar archivos organizados |
| "qué opinás", "cómo lo ves" | Discutir opciones, no codear aún |
| "hacelo", "dale" | Implementar directamente |
| "smoke test" | Dar comandos para ejecutar |
| Screenshot de error | Diagnosticar y proponer fix |

---

## 🧪 Testing

### Smoke Tests

```bash
# Ejecutar smoke tests completos
./smoke_tests.sh
```

### Tests actuales (10)

1. Login page carga
2. Register page carga
3. Home redirige a login (sin auth)
4. Perfil redirige a login (sin auth)
5. API viajes/count responde
6. Cron process-emails funciona
7. Cron check-flights funciona
8. Calendar feed sin token → 403
9. Calendar feed token inválido → 404
10. Migrate DB responde

### Test E2E Manual (post-MVP)

1. Registrar usuario nuevo
2. Verificar 0 viajes
3. Configurar nombre_pax/apellido_pax
4. Desde otro usuario, crear viaje con el nuevo como pasajero
5. Verificar que nuevo usuario ve el viaje
6. Probar logout/login

---

## 🔄 Gestión de Sesiones con Claude

### Cuándo abrir nueva conversación

Claude monitoreará y sugerirá proactivamente nueva sesión cuando:

| Señal | Acción |
|-------|--------|
| ~50+ intercambios | Sugerir corte en próximo punto natural |
| Deploy/feature completado | Buen momento para cerrar y documentar |
| Respuestas más lentas | Indicador de contexto saturado |
| Nueva tarea compleja | Mejor arrancar fresh |
| Cambio de tema grande | Evitar mezclar contextos |

### Checklist de cierre de sesión

Antes de cerrar, asegurar que quede documentado:

```
1. ¿Qué se completó? (commits, deploys, features)
2. ¿Qué quedó pendiente? (próximo paso concreto)
3. ¿Hay algo para actualizar en docs? (ROADMAP, METODOLOGIA, UX_UI)
4. ¿Smoke tests pasaron?
```

### Checklist de inicio de sesión

**OBLIGATORIO** revisar estos archivos antes de empezar:

- `METODOLOGIA_TRABAJO.md` - Workflow y convenciones
- `ROADMAP.md` - Estado actual y próximos pasos
- `DESIGN_SYSTEM.md` - Consistencia visual

Template para primer mensaje:

```
Proyecto: Mi Agente Viajes
Conversación: Mis Viajes XX
Estado: [MVP actual]
Objetivo: [Qué queremos lograr]

Por favor revisá METODOLOGIA, ROADMAP y DESIGN_SYSTEM antes de empezar.
```

---

## 📋 Documentación del Proyecto

### Estructura de Docs

| Documento | Propósito | Cuándo Actualizar |
|-----------|-----------|-------------------|
| `ROADMAP.md` | MVPs, prioridades, decisiones | Al completar/agregar MVP |
| `docs/APRENDIZAJES.md` | Bugs resueltos, patterns, técnicas | Al resolver bug o aprender pattern |
| `docs/CASOS_DE_USO.md` | Matriz de casos de uso con status | Al implementar feature o encontrar bug |
| `docs/QA_CHECKLIST.md` | Procedimientos de testing | Al agregar nuevo tipo de test |
| `METODOLOGIA_TRABAJO.md` | Workflow y convenciones | Al cambiar proceso o herramienta |
| `DESIGN_SYSTEM.md` | Paleta, tipografía, componentes | Al agregar color/componente/patrón |

### Flujo de Actualización

```
Feature implementada → Smoke tests pasan
↓
Actualizar docs/CASOS_DE_USO.md (marcar ✅)
↓
Si aprendiste algo → docs/APRENDIZAJES.md
↓
Si completaste MVP → ROADMAP.md
↓
Commit docs: git add docs/ ROADMAP.md && git commit -m "docs: actualizar post-[feature]"
```

### Checklist Inicio de Sesión

Antes de empezar a trabajar:
- [ ] Leer `ROADMAP.md` - ¿Qué se completó? ¿Qué sigue?
- [ ] Leer `docs/APRENDIZAJES.md` - ¿Qué bugs evitar? ¿Qué patterns usar?
- [ ] Leer `docs/CASOS_DE_USO.md` - ¿Qué funciona? ¿Qué bugs conocidos?
- [ ] Leer `METODOLOGIA_TRABAJO.md` - Workflow actual

### Checklist Cierre de Sesión

Antes de cerrar sesión:
- [ ] Actualizar `docs/CASOS_DE_USO.md` con status de features
- [ ] Actualizar `docs/APRENDIZAJES.md` si hubo bugs/learnings
- [ ] Actualizar `ROADMAP.md` si se completó MVP o hay nueva prioridad
- [ ] Smoke tests: `./smoke_tests.sh` → 10/10
- [ ] Commit documentación
- [ ] Push a GitHub

---

## 📝 Estrategia para Archivos Largos

### El problema

Archivos grandes (>200 líneas) son riesgosos de generar completos en Claude.ai:
- Pueden truncarse al descargar
- Difícil verificar que estén correctos
- Claude puede "congelarse" al crear múltiples archivos grandes

### Solución: Prompt para Claude Code en Codespaces

Cuando un archivo requiere cambios pero es muy largo para regenerar completo:

1. **Claude.ai prepara un prompt detallado** con los cambios específicos
2. **Usuario copia el prompt a Claude Code** (sidebar en Codespaces)
3. **Claude Code aplica los cambios** directamente en el archivo
4. **Usuario verifica con git diff** antes de commitear

### Cuándo usar cada estrategia

| Situación | Estrategia |
|-----------|------------|
| Archivo nuevo < 150 líneas | Claude.ai genera completo |
| Archivo nuevo > 150 líneas | Dividir en partes o usar Claude Code |
| Edición < 20 líneas | Claude.ai da instrucciones, edición manual |
| Edición 20-100 líneas | Prompt para Claude Code |
| Edición > 100 líneas | Evaluar si conviene regenerar |

---

## 🚀 Workflow de Deploy Seguro

### Flujo obligatorio: Commit → Sync → Verificar → Deploy

```
Hacer cambios en Codespaces (manual o con Claude Code)
↓
git add . && git commit -m "descripción" && git push
↓
Sync 🔄 en Project Knowledge de Claude
↓
Pedir a Claude que verifique los cambios en el repo
↓
Si todo OK → Deploy
↓
Smoke tests
↓
Sync 🔄 final
```

### Por qué este orden

| Paso | Propósito |
|------|-----------|
| Commit + Push | Código versionado, rollback posible |
| Sync en Claude | Claude puede ver el código actual |
| Verificar | Claude revisa que cambios estén completos |
| Deploy | Solo después de verificación |

---

## 🔥 Troubleshooting

### Deploy falla

```bash
# Ver logs del build
gcloud builds list --limit 5

# Ver logs de la app
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mi-agente-viajes" --limit 30
```

### Variables de entorno perdidas

```bash
# IMPORTANTE: deploy sin --set-env-vars MANTIENE las variables
# Pero --set-env-vars REEMPLAZA todas

# Ver variables actuales
gcloud run services describe mi-agente-viajes --region us-east1
```

### Rollback

```bash
# Ver revisiones disponibles
gcloud run revisions list --service mi-agente-viajes --region us-east1

# Volver a revisión anterior
gcloud run services update-traffic mi-agente-viajes --to-revisions=REVISION_NAME=100 --region us-east1
```

### Base de datos

```bash
# Conectar a Cloud SQL (NOTA: la base se llama viajes_db)
gcloud sql connect mi-agente-viajes-db --user=postgres --database=viajes_db

# Migrar esquema (desde la app)
curl https://mi-agente-viajes-454542398872.us-east1.run.app/migrate-db
```

### Migración BD olvidada en Cloud Run

**Síntoma:** App devuelve 500 después de deploy que agrega columna nueva.

**Causa:** Cloud Run deploy NO ejecuta `flask db upgrade` automáticamente.

**Solución:**
```bash
# Ver logs para confirmar error de columna
gcloud run services logs read mi-agente-viajes --region us-east1 --limit 50

# Ejecutar migración manual (una de estas opciones):
# 1. Desde Cloud Run Job
# 2. Script Python con DATABASE_URL correcto (recordar URL-encode de caracteres especiales en password)
```

**Prevención:** Después de agregar campo a modelo, verificar:
1. `flask db migrate` genera archivo
2. `flask db upgrade` se ejecuta en producción
3. Smoke test pasa

### Archivo corrupto / deploy roto

**Síntoma:** Internal Server Error después de deploy, logs muestran `TemplateSyntaxError: unexpected end of template`

**Causa:** Archivos grandes (index.html ~1800 líneas) pueden truncarse al descargar de Claude.

**Prevención:** Verificar siempre con `tail -10 archivo` antes de commitear.

```bash
# Si archivo no se commiteó aún:
git checkout HEAD -- templates/archivo.html

# Si archivo corrupto ya se commiteó, restaurar de commit anterior:
git log --oneline -5
git checkout <commit_hash> -- templates/archivo.html
git add . && git commit -m "Rollback archivo a version estable" && git push

# Redeploy
gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated
```

---

## 📊 Estado del Proyecto

### MVPs Completados

| MVP | Descripción | Fecha |
|-----|-------------|-------|
| 1-4 | Core + PDF + Calendar + FR24 | Nov 2025 |
| 5 | Email automation | Dic 2025 |
| 6 | Multi-usuario | 7 Dic 2025 |
| 7 | Viajes por pasajero | 8 Dic 2025 |
| 8 | Recuperar contraseña | 8 Dic 2025 |
| 9 | Calendar feed privado + Refactor arquitectónico | 9 Dic 2025 |
| 10 | Calendario all-day | 9 Dic 2025 |
| 11 | Deduplicación de vuelos compartidos | 10 Dic 2025 |
| 12-14 | Onboarding, Notificaciones, Gmail | 10-11 Dic 2025 |
| Meta 1 | Sistema agéntico | 12 Dic 2025 |
| 14h | Microsoft OAuth | 12 Dic 2025 |
| 15 | Onboarding post-registro + Template inheritance | 14 Dic 2025 |
| **15** | **Multi-Tipo de Reservas (9 tipos)** | **15 Dic 2025** |

### URLs Importantes

- **App:** https://mi-agente-viajes-454542398872.us-east1.run.app
- **Repo:** https://github.com/andygamberg/mi-agente-viajes
- **Calendar Feed:** `/calendar-feed/<token>` (token personal en Perfil)

### Costos Mensuales

| Servicio | Costo |
|----------|-------|
| Cloud SQL | ~$10 |
| FR24 API | $9 |
| Cloud Run | $0 (free tier) |
| **Total** | ~$19/mes |

---

## 🔮 Próximos Pasos

### Alta Prioridad
- [ ] MVP12: Onboarding mejorado (recordatorio calendario + perfil)
- [ ] Deduplicación en calendar feed (fix pendiente)
- [ ] UX: badge combinado solo en segmentos desplegados

### Media Prioridad
- [ ] MVP14: Gmail/Outlook integration (detectar cambios de vuelo)
- [ ] Backoffice admin

### Baja Prioridad
- [ ] Rediseño UI moderno
- [ ] Compartir viajes entre usuarios

---

## 📝 Notas para Nuevas Conversaciones

Al iniciar nueva conversación con Claude, incluir:

```
Proyecto: Mi Agente Viajes
Repo: github.com/andygamberg/mi-agente-viajes (conectado a Project Knowledge)
Stack: Flask + PostgreSQL + Google Cloud Run
URL: https://mi-agente-viajes-454542398872.us-east1.run.app
Estado: MVP15 completado (15 Dic 2025)
Metodología: Ver METODOLOGIA_TRABAJO.md en el repo
```

---

## 🎨 Design System

El proyecto tiene un Design System documentado en `DESIGN_SYSTEM.md` que define:

- Paleta de colores
- Tipografía
- Iconografía (Heroicons, NO emojis)
- Espaciado y border-radius
- Reglas de botones y componentes

**REGLA FUNDAMENTAL:** Nunca usar emojis en la UI. Solo SVG de Heroicons.

Ver `DESIGN_SYSTEM.md` para el catálogo completo de iconos y cómo usarlos.

---

## 💬 Formato de Comunicación Claude.ai ↔ Andy

### Separación de bloques

Cuando Claude.ai prepara comandos o prompts, SIEMPRE separar en bloques independientes para fácil copy-paste:

**Estructura correcta:**
```
## Para tu terminal

**Comando 1 - [descripción]:**
```bash
[bloque de código]
```

**Comando 2 - [descripción]:**
```bash
[bloque de código]
```

---

## Prompt para Claude Code

```
[bloque de código separado]
```
```

**Estructura incorrecta:**
- ❌ Mezclar comandos de terminal con prompts de Claude Code en el mismo bloque
- ❌ Poner múltiples comandos en un solo bloque sin separación
- ❌ Incluir texto explicativo dentro del bloque de código

### Roles y responsabilidades

| Acción | Quién ejecuta | Herramienta |
|--------|---------------|-------------|
| Diagnóstico producción (logs, BD, endpoints) | Andy | Terminal local + gcloud |
| Cambios de código | Claude Code | VS Code con extensión |
| Arquitectura y decisiones | Claude.ai | Chat en claude.ai |
| Deploy y git | Claude Code | Terminal en VS Code |

### Regla de oro

**Claude.ai NUNCA intenta ejecutar comandos de infraestructura** (gcloud, SQL, curl a producción).

Solo prepara los comandos para que Andy los ejecute y analiza los resultados.

**Ejemplos:**
- ✅ Claude.ai: "Ejecutá este comando en tu terminal: `gcloud logging read ...`"
- ❌ Claude.ai: Intentar ejecutar `gcloud logging read` directamente

---

## 📋 Formato de Comunicación Claude.ai ↔ Andy

### Separación de bloques

Cuando Claude.ai prepara comandos o prompts, SIEMPRE separar en secciones independientes para fácil copy-paste:

**Estructura correcta:**
```
Para tu terminal

Comando 1 - [descripción]:
```bash
[comando]
```

Comando 2 - [descripción]:
```bash
[comando]
```

---

Prompt para Claude Code
```
[prompt completo]
```
```

**Estructura incorrecta:**
- Mezclar comandos de terminal con prompts de Claude Code en el mismo bloque
- Poner múltiples comandos en un solo bloque sin separación
- Incluir texto explicativo dentro del bloque de código

### Roles y herramientas

| Acción | Quién ejecuta | Herramienta |
|--------|---------------|-------------|
| Diagnóstico producción (logs, BD, endpoints) | Andy vía terminal o Claude Code | gcloud, SQL |
| Arquitectura y decisiones de producto | Claude.ai (Opus 4.5) | Chat en claude.ai |
| Cambios de código y deploy | Claude Code (Sonnet 4) | VS Code con extensión |

### Regla de oro

Claude.ai **nunca** intenta ejecutar comandos de infraestructura (gcloud, SQL, curl a producción). Solo:
1. Prepara los comandos para que Andy los ejecute en su terminal, o
2. Prepara prompt completo para Claude Code que SÍ tiene acceso

---

## 🔄 Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 8 Dic 2025 | Documento inicial creado |
| 8 Dic 2025 | MVP7 completado (viajes por pasajero) |
| 8 Dic 2025 | Recuperar contraseña implementado |
| 9 Dic 2025 | Agregada sección Gestión de Sesiones |
| 9 Dic 2025 | MVP9: Calendar feed privado por usuario |
| 9 Dic 2025 | Refactor arquitectónico: blueprints/ + utils/ |
| 9 Dic 2025 | app.py reducido de 1400 a 75 líneas |
| 9 Dic 2025 | Agregada sección Arquitectura del Proyecto |
| 10 Dic 2025 | MVP10: Calendario all-day |
| 10 Dic 2025 | MVP11: Deduplicación de vuelos compartidos |
| 10 Dic 2025 | Agregado troubleshooting: archivo corrupto/deploy roto |
| 11 Dic 2025 | Agregada estrategia para archivos largos (prompt a Claude Code) |
| 11 Dic 2025 | Formalizado workflow: commit → sync → verificar → deploy |
| 11 Dic 2025 | Obligatorio revisar docs clave en nuevas conversaciones |
| 12 Dic 2025 | MVP14h: Microsoft OAuth completado |
| 14 Dic 2025 | MVP15: Onboarding post-registro + base.html |
| 15 Dic 2025 | MVP15: Multi-Tipo de Reservas (9 tipos) |
| 15 Dic 2025 | Creado APRENDIZAJES.md (living document) |
| 15 Dic 2025 | Agregada sección "Primera Acción Obligatoria" |
| 15 Dic 2025 | Agregada sección "Formato de Comunicación Claude.ai ↔ Andy" |
| 15 Dic 2025 | Sesión 22: Fix multi-tipo gmail_to_db.py, decisión edición > extracción |
| 15 Dic 2025 | Expandida sección Formato de Comunicación con roles y regla de oro |
