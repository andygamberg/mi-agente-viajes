#!/bin/bash
# Script para aplicar migración en GCP Cloud SQL

echo "🔧 Aplicando migración FR24 a Cloud SQL..."

gcloud sql connect mi-agente-viajes-db \
  --user=postgres \
  --database=viajes \
  --project=mi-agente-viajes << SQL
ALTER TABLE viaje ADD COLUMN IF NOT EXISTS ultima_actualizacion_fr24 TIMESTAMP;
ALTER TABLE viaje ADD COLUMN IF NOT EXISTS status_fr24 VARCHAR(50);
ALTER TABLE viaje ADD COLUMN IF NOT EXISTS delay_minutos INTEGER;
ALTER TABLE viaje ADD COLUMN IF NOT EXISTS datetime_takeoff_actual TIMESTAMP;
ALTER TABLE viaje ADD COLUMN IF NOT EXISTS datetime_landed_actual TIMESTAMP;
SQL

echo "✅ Migración aplicada exitosamente"
