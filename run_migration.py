#!/usr/bin/env python3
"""
Script para ejecutar migración de codigo_reserva VARCHAR(50) → VARCHAR(255)
Ejecutar: python3 run_migration.py
"""
import os
from sqlalchemy import create_engine, text

# Obtener DATABASE_URL del entorno
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL no configurada en el entorno")
    print("ℹ️  Ejecutar desde Cloud Run o configurar DATABASE_URL localmente")
    exit(1)

# Crear engine
engine = create_engine(database_url)

# Ejecutar migración
migration_sql = """
ALTER TABLE viaje
ALTER COLUMN codigo_reserva TYPE VARCHAR(255);
"""

try:
    with engine.connect() as conn:
        print("🔄 Ejecutando migración...")
        conn.execute(text(migration_sql))
        conn.commit()
        print("✅ Migración completada: codigo_reserva ahora es VARCHAR(255)")
except Exception as e:
    print(f"❌ Error en migración: {e}")
    exit(1)
