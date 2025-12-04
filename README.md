# 🌍 Mi Agente Viajes

Sistema inteligente de gestión de viajes con monitoreo automático de vuelos y sincronización de calendario.

## 🎯 Descripción

Alternativa moderna a TripCase que permite:
- ✈️ Cargar vuelos automáticamente desde PDFs o emails
- 📅 Sincronización automática con Apple Calendar (webcal)
- 🔍 Monitoreo en tiempo real de cambios en vuelos
- 👥 Gestión multi-usuario (futuro)
- 📱 Acceso web responsive

## 🚀 Estado Actual: MVP 4.5 ✅

### Completado
- ✅ Core app con carga de vuelos
- ✅ Extracción con Claude API de PDFs
- ✅ Calendar sync (webcal)
- ✅ Flight monitoring con FR24
- ✅ Auto-update de BD cuando hay cambios

### En Desarrollo
- 🔄 MVP 5: Email monitoring automático (Gmail API)

## 🌐 URLs Producción

- **App:** https://mi-agente-viajes-454542398872.us-east1.run.app
- **Calendar:** https://mi-agente-viajes-454542398872.us-east1.run.app/calendar-feed

## 📚 Documentación

- Ver [ROADMAP.md](ROADMAP.md) para plan completo de features
- Ver [MVP4_RESEARCH.md](MVP4_RESEARCH.md) para detalles técnicos FR24

## 💰 Costos: ~$19/mes
- Cloud SQL: $10/mes
- FR24 API: $9/mes
- Cloud Run: $0 (free tier)
