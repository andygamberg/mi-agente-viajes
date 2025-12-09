# 🤖 Metodología de Trabajo AI-Assisted Development

**Proyecto:** Mi Agente Viajes
**Última actualización:** 9 Diciembre 2025
**Stack:** Flask + PostgreSQL + Google Cloud Run

---

## 📋 Índice

1. [Setup del Entorno](#setup-del-entorno)
2. [Flujo de Desarrollo](#flujo-de-desarrollo)
3. [Estructura de Archivos para Deploy](#estructura-de-archivos-para-deploy)
4. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
5. [Convenciones de Comunicación](#convenciones-de-comunicación)
6. [Testing](#testing)
7. [Gestión de Sesiones con Claude](#gestión-de-sesiones-con-claude)
8. [Troubleshooting](#troubleshooting)

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
1. Discutir requerimiento con Claude
2. Claude genera archivos
3. Usuario descarga archivos
4. Usuario arrastra a Codespace
5. git add . && git commit -m "mensaje" && git push
6. gcloud run deploy...
7. Smoke tests
8. Sync repo en Claude (🔄)
```

### Comandos frecuentes

```bash
# Ver cambios pendientes
git status

# Commit y push en un comando
git add . && git commit -m "descripción del cambio" && git push

# Deploy a Cloud Run
gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated

# Ver logs de Cloud Run
gcloud run logs read mi-agente-viajes --region us-east1 --limit 50
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
| `User` | email, password_hash, nombre, nombre_pax, apellido_pax, calendar_token | has_many: Viaje, UserEmail |
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

Para retomar contexto rápido, incluir en primer mensaje:

```
Proyecto: Mi Agente Viajes
Repo: github.com/andygamberg/mi-agente-viajes
Estado: [MVP actual, última feature completada]
Objetivo: [Qué queremos lograr en esta sesión]
Contexto: [Si hay algo específico de la sesión anterior]
```

### Ejemplo de mensaje de inicio

```
Proyecto: Mi Agente Viajes
Estado: MVP9 completado + refactor arquitectónico
Objetivo: Implementar MVP10 (calendario all-day)
Contexto: App modular con blueprints/, utils/
```

---

## 🔥 Troubleshooting

### Deploy falla

```bash
# Ver logs del build
gcloud builds list --limit 5

# Ver logs de la app
gcloud run logs read mi-agente-viajes --region us-east1 --limit 100
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
- [ ] MVP10: Calendario all-day (evento multi-día para viajes completos)
- [ ] MVP11: Deduplicación de vuelos (mismo vuelo en distintas reservas)
- [ ] Onboarding mejorado (recordatorio calendario + perfil)

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
Estado: MVP9 completado + Refactor arquitectónico (9 Dic 2025)
Metodología: Ver METODOLOGIA_TRABAJO.md en el repo
```

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
