-- Migración: Aumentar límite de codigo_reserva de VARCHAR(50) a VARCHAR(255)
-- Razón: Algunos códigos de expediciones/charters son más largos (ej: Antarctica_Photo_Expedition_with_AntonioS.Chamorro_2026)
-- Fecha: 15 Dic 2025

ALTER TABLE viaje
ALTER COLUMN codigo_reserva TYPE VARCHAR(255);
