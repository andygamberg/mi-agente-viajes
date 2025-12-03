-- Migración: Agregar campos de monitoreo FR24 a tabla viaje
-- Fecha: 2025-12-03

ALTER TABLE viaje ADD COLUMN ultima_actualizacion_fr24 TIMESTAMP;
ALTER TABLE viaje ADD COLUMN status_fr24 VARCHAR(50);
ALTER TABLE viaje ADD COLUMN delay_minutos INTEGER;
ALTER TABLE viaje ADD COLUMN datetime_takeoff_actual TIMESTAMP;
ALTER TABLE viaje ADD COLUMN datetime_landed_actual TIMESTAMP;
