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
