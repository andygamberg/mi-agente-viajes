# Estado de Deploy - Mi Agente Viajes

## Versión actual en producción
- **Tag:** v1.0-stable
- **Fecha:** 2024-12-06
- **Cloud Run revision:** (completar con `gcloud run revisions list`)

## Funcionalidades activas
- ✅ PDF processing (Claude API)
- ✅ FR24 flight monitoring
- ✅ Calendar feed (.ics)
- ✅ Scheduler inteligente por proximidad
- 🔄 Gmail automation (en desarrollo)

## Cómo hacer rollback
```bash
# Opción 1: Volver al tag estable
git checkout v1.0-stable

# Opción 2: En Cloud Run (si ya deployeaste algo roto)
gcloud run services update-traffic mi-agente-viajes --to-revisions=REVISION_ESTABLE=100
```

## Última actualización
- **Qué:** Setup inicial de metodología
- **Por qué:** Organizar desarrollo con Kanban y docs
- **Quién:** Andy + Claude
