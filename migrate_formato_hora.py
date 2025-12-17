#!/usr/bin/env python3
"""
Script para agregar columna formato_hora a tabla user
Ejecutar: python3 migrate_formato_hora.py
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
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS formato_hora VARCHAR(4);
"""

try:
    with engine.connect() as conn:
        print("🔄 Ejecutando migración formato_hora...")
        conn.execute(text(migration_sql))
        conn.commit()
        print("✅ Migración completada: columna formato_hora agregada")
except Exception as e:
    print(f"❌ Error en migración: {e}")
    exit(1)
