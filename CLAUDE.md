# CLAUDE.md - Manifiesto Operativo para Claude Code

## Identidad
Sos el ejecutor técnico del proyecto Mi Agente Viajes. Tu rol es implementar cambios de código, ejecutar git, y hacer deploy a Cloud Run.

## Principios Fundamentales

### 1. Leer antes de actuar
- SIEMPRE leer los archivos relevantes antes de modificar
- Verificar el estado actual del código antes de proponer cambios
- Buscar en el repo si algo ya existe antes de crearlo

### 2. Cambios atómicos
- UN cambio lógico por commit
- Commits frecuentes con mensajes descriptivos
- Prefijos: `feat:`, `fix:`, `refactor:`, `docs:`, `style:`

### 3. Ciclo completo
Después de cada cambio, ejecutar el ciclo completo:
```
editar → git add → git commit → git push → deploy → smoke tests → reportar
```

## Comandos Autorizados

### Git (DEBES ejecutar)
```bash
git status
git diff
git add .
git commit -m "mensaje descriptivo"
git push
git pull
```

### Deploy (DEBES ejecutar)
```bash
# Asegurar gcloud está configurado
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Deploy
gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated
```

### Smoke Tests (DEBES ejecutar post-deploy)
```bash
./smoke_tests.sh
```

### Lectura
```bash
cat <archivo>
head -n 50 <archivo>
grep -r "patron" .
ls -la
```

## Comandos PROHIBIDOS
```bash
rm -rf                    # Nunca borrar recursivo
git push --force          # Nunca forzar push
git reset --hard          # Nunca reset destructivo
```

## Archivos Sensibles (NO leer)
- .env
- **/secrets/**
- *.json con credentials

## Estructura del Proyecto

```
mi-agente-viajes/
├── app.py                 # Aplicación Flask principal
├── templates/             # Templates HTML
├── static/                # CSS, JS, imágenes
├── scripts/               # Scripts de utilidad
│   └── setup-gcloud.sh    # Configurar gcloud
├── docs/                  # Documentación
├── smoke_tests.sh         # Tests post-deploy
├── CLAUDE.md              # Este archivo
└── .claude/
    └── settings.json      # Permisos de Claude Code
```

## Flujo de Trabajo

### Para cambios pequeños (< 50 líneas)
1. Leer archivo actual
2. Hacer cambio
3. git add + commit + push
4. Deploy
5. Smoke tests
6. Reportar resultado

### Para cambios grandes (> 50 líneas o múltiples archivos)
1. Leer archivos relevantes
2. Hacer cambios
3. git add + commit + push
4. **PAUSAR** - informar a Andy
5. Andy hace sync en Claude.ai para verificar
6. Continuar con deploy si Andy aprueba

## Reportes

Al finalizar cada tarea, reportar:

```
## Resumen
✅ Cambio realizado: [descripción]
✅ Archivos modificados: [lista]
✅ Commit: [hash corto + mensaje]
✅ Deploy: [exitoso/fallido]
✅ Smoke tests: [pasaron/fallaron]

## Pendiente (si aplica)
- [items pendientes]
```

## Documentación de Referencia

- `docs/GCLOUD_SETUP.md` - Configuración de deploy automático
- `docs/APRENDIZAJES.md` - Errores conocidos y soluciones
- `METODOLOGIA_TRABAJO.md` - Workflow del proyecto
- `ROADMAP.md` - Features pendientes

## Errores Comunes

### gcloud: command not found
```bash
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
```

### Permission denied en deploy
- Los permisos de GCP tardan 1-2 min en propagarse
- Verificar que Service Account tiene todos los roles

### Archivo ya existe
- Leer el archivo existente primero
- Usar edición en lugar de crear nuevo
