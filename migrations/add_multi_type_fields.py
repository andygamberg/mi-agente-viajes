"""Agregar campos para soporte multi-tipo de reservas"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def migrate():
    with app.app_context():
        # Agregar columnas si no existen
        from sqlalchemy import text

        columns_to_add = [
            ("ubicacion", "VARCHAR(500)"),
            ("proveedor", "VARCHAR(200)"),
            ("precio", "VARCHAR(100)"),
            ("raw_data", "TEXT"),
        ]

        for col_name, col_type in columns_to_add:
            try:
                db.session.execute(text(f"ALTER TABLE viaje ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Columna {col_name} agregada")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print(f"ℹ️ Columna {col_name} ya existe")
                else:
                    print(f"❌ Error agregando {col_name}: {e}")

        db.session.commit()
        print("✅ Migración completada")

if __name__ == "__main__":
    migrate()
