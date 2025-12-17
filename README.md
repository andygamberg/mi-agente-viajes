# Mi Agente Viajes

Sistema inteligente de gestión de viajes con extracción automática de reservas desde emails y PDFs.

## Estado: MVP 26 (17 Dic 2025)

### Features Principales
- 11 tipos de reservas: vuelos, hoteles, cruceros, autos, restaurantes, espectáculos, actividades, trenes, buses, transfers
- Extracción automática: Gmail OAuth + Microsoft OAuth + reenvío de emails
- Monitoreo de vuelos: Flightradar24 API con alertas de cambios
- Calendario sincronizado: Apple Calendar, Google Calendar, Outlook
- Multi-usuario: Cada usuario ve sus propias reservas + donde es pasajero
- Deduplicación inteligente: Combina reservas idénticas de diferentes pasajeros

### Stack Técnico
- Backend: Flask + PostgreSQL + SQLAlchemy
- Hosting: Google Cloud Run
- AI: Claude API para extracción de información
- APIs: Gmail, Microsoft Graph, Flightradar24

## URLs

- App: https://mi-agente-viajes-454542398872.us-east1.run.app
- Repo: https://github.com/andygamberg/mi-agente-viajes

## Documentación

- ROADMAP.md - Estado del proyecto y próximos pasos
- METODOLOGIA_TRABAJO.md - Workflow de desarrollo
- DESIGN_SYSTEM.md - Sistema de diseño
- UX_UI_ROADMAP.md - Principios de UX
- docs/APRENDIZAJES.md - Lecciones aprendidas
- docs/CASOS_DE_USO.md - Matriz de casos de uso

## Costos Mensuales

- Cloud SQL: ~$10
- FR24 API: $9
- Cloud Run: $0 (free tier)
- Total: ~$19/mes

## Licencia

Proyecto privado - 2025 Andy Gamberg
