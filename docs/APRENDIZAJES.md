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
