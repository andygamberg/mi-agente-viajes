# 🤖 Metodología de Trabajo AI-Assisted Development

**Proyecto:** Mi Agente Viajes
**Última actualización:** 8 Diciembre 2025
**Stack:** Flask + PostgreSQL + Google Cloud Run

---

## 📋 Índice

1. [Setup del Entorno](#setup-del-entorno)
2. [Flujo de Desarrollo](#flujo-de-desarrollo)
3. [Estructura de Archivos para Deploy](#estructura-de-archivos-para-deploy)
4. [Convenciones de Comunicación](#convenciones-de-comunicación)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

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
   - Arrastrá contenido de "templates/" → carpeta templates/
   - Reemplazar cuando pregunte
4. En terminal: git status (verificar archivos)
5. Commit: git add . && git commit -m "mensaje" && git push
6. Deploy: gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated
7. Smoke tests
8. Sync en Claude (🔄)
```

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

# O ejecutar inline (copiar bloque completo)
echo "🧪 Running smoke tests..." && \
# ... (ver smoke_tests.sh para versión completa)
```

### Tests actuales (9)

1. Login page carga
2. Register page carga
3. Home redirige a login (sin auth)
4. Perfil redirige a login (sin auth)
5. API viajes/count responde
6. Cron process-emails funciona
7. Cron check-flights funciona
8. Calendar feed genera iCal válido
9. Migrate DB responde

### Test E2E Manual (post-MVP)

1. Registrar usuario nuevo
2. Verificar 0 viajes
3. Configurar nombre_pax/apellido_pax
4. Desde otro usuario, crear viaje con el nuevo como pasajero
5. Verificar que nuevo usuario ve el viaje
6. Probar logout/login

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
# Conectar a Cloud SQL
gcloud sql connect mi-agente-viajes-db --user=postgres --database=viajes

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

### URLs Importantes

- **App:** https://mi-agente-viajes-454542398872.us-east1.run.app
- **Repo:** https://github.com/andygamberg/mi-agente-viajes
- **Calendar Feed:** https://mi-agente-viajes-454542398872.us-east1.run.app/calendar-feed

### Costos Mensuales

| Servicio | Costo |
|----------|-------|
| Cloud SQL | ~$10 |
| FR24 API | $9 |
| Cloud Run | $0 (free tier) |
| **Total** | ~$19/mes |

---

## 🔮 Backlog

### Alta Prioridad
- [ ] Recuperar contraseña (en deploy)
- [ ] Onboarding (recordatorio calendario + perfil)

### Media Prioridad
- [ ] Rediseño UI moderno
- [ ] Mobile responsive mejorado

### Baja Prioridad
- [ ] Placeholders genéricos (Juan Pérez)
- [ ] Portal para agentes de viaje
- [ ] Tab "Compartidos" para asistentes

---

## 📝 Notas para Nuevas Conversaciones

Al iniciar nueva conversación con Claude, incluir:

```
Proyecto: Mi Agente Viajes
Repo: github.com/andygamberg/mi-agente-viajes (conectado a Project Knowledge)
Stack: Flask + PostgreSQL + Google Cloud Run
Estado: MVP7 completado, trabajando en UX
Metodología: Ver METODOLOGIA_TRABAJO.md en el repo
```

---

## 🔄 Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 8 Dic 2025 | Documento inicial creado |
| 8 Dic 2025 | MVP7 completado (viajes por pasajero) |
| 8 Dic 2025 | Recuperar contraseña implementado |
