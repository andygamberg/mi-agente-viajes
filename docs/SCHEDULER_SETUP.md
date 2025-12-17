# Setup Cloud Scheduler para Monitoreo de Vuelos

## Estrategia de Frecuencia Dinámica

El scheduler se ejecuta **cada 15 minutos** pero el endpoint `/cron/check-flights` 
internamente decide qué vuelos chequear según su proximidad.

### Configuración Cloud Scheduler:
```bash
# 1. Crear el cron job
gcloud scheduler jobs create http flight-monitor \
    --schedule="*/15 * * * *" \
    --uri="https://mi-agente-viajes-454542398872.us-east1.run.app/cron/check-flights" \
    --http-method=POST \
    --headers="X-Appengine-Cron=true" \
    --location=us-east1 \
    --project=mi-agente-viajes
```

### Lógica Interna (en el código):
```
┌─────────────────────────┬──────────────┬────────────────────┐
│ Tiempo hasta vuelo      │ Frecuencia   │ Acción del endpoint│
├─────────────────────────┼──────────────┼────────────────────┤
│ Más de 7 días           │ 1x por día   │ Chequea 1 vez/día  │
│ 7-2 días antes          │ 2x por día   │ Chequea 2 veces/día│
│ 48-24 horas antes       │ Cada 6h      │ Chequea c/6h       │
│ 24-12 horas antes       │ Cada 1h      │ Chequea c/1h       │
│ 12-2 horas antes        │ Cada 30min   │ Chequea c/30min    │
│ Menos de 2 horas        │ Cada 15min   │ Chequea c/15min    │
└─────────────────────────┴──────────────┴────────────────────┘
```

**Ventaja:** Un solo cron job, lógica inteligente decide qué procesar.

### Variables de Entorno en Cloud Run:
```bash
# Configurar FR24_API_TOKEN
gcloud run services update mi-agente-viajes \
    --update-env-vars FR24_API_TOKEN="019ae167-5bdd-7355-acf7-d2db1dc29740|bv9Ox4UD5JrSWbf6gR2fvCp0m1bwXcbmyIWspAdQf4d00f82" \
    --region=us-east1 \
    --project=mi-agente-viajes
```

### Aplicar Migración SQL:
```bash
./apply_migration_gcp.sh
```

### Costos Estimados:

- Cloud Scheduler: $0.10/mes (1 job)
- Cloud Run invocations: ~2,880/mes (cada 15 min) = ~$0.50/mes
- FR24 API: 6,150 créditos/mes de 60,000 disponibles

**Total: ~$0.60/mes adicionales**
