#!/usr/bin/env python3
"""
Migración: Poblar columna 'datos' JSONB desde raw_data existente.
Ejecutar una sola vez después de agregar la columna.
"""
import json
import os
import sys

# Setup Flask app context
from app import create_app
from models import db, Viaje

def migrate_viajes():
    """Migra todos los viajes existentes a estructura JSONB"""

    viajes = Viaje.query.all()
    total = len(viajes)
    migrados = 0
    errores = 0

    print(f"Migrando {total} viajes...")

    for viaje in viajes:
        try:
            if viaje.raw_data:
                # Tiene raw_data de Claude - usar directamente
                datos = json.loads(viaje.raw_data)
            else:
                # Carga manual sin raw_data - construir desde columnas
                datos = {
                    'tipo': viaje.tipo or 'vuelo',
                    'descripcion': viaje.descripcion,
                    'origen': viaje.origen,
                    'destino': viaje.destino,
                    'codigo_reserva': viaje.codigo_reserva,
                }

                # Campos específicos de vuelo
                if viaje.tipo == 'vuelo' or not viaje.tipo:
                    datos.update({
                        'aerolinea': viaje.aerolinea,
                        'numero_vuelo': viaje.numero_vuelo,
                        'terminal': viaje.terminal,
                        'puerta': viaje.puerta,
                        'asiento': viaje.asiento,
                    })

                # Fechas
                if viaje.fecha_salida:
                    datos['fecha_salida'] = viaje.fecha_salida.strftime('%Y-%m-%d')
                if viaje.hora_salida:
                    datos['hora_salida'] = viaje.hora_salida
                if viaje.fecha_llegada:
                    datos['fecha_llegada'] = viaje.fecha_llegada.strftime('%Y-%m-%d')
                if viaje.hora_llegada:
                    datos['hora_llegada'] = viaje.hora_llegada

                # Pasajeros (ya es JSON string)
                if viaje.pasajeros:
                    try:
                        datos['pasajeros'] = json.loads(viaje.pasajeros)
                    except:
                        datos['pasajeros'] = []

                # Campos multi-tipo
                if viaje.proveedor:
                    datos['proveedor'] = viaje.proveedor
                if viaje.ubicacion:
                    datos['ubicacion'] = viaje.ubicacion
                if viaje.precio:
                    datos['precio'] = viaje.precio

            # Asegurar que tipo esté presente
            if 'tipo' not in datos:
                datos['tipo'] = viaje.tipo or 'vuelo'

            viaje.datos = datos
            migrados += 1

            if migrados % 50 == 0:
                print(f"  Progreso: {migrados}/{total}")
                db.session.commit()

        except Exception as e:
            print(f"  ❌ Error en viaje {viaje.id}: {e}")
            errores += 1

    db.session.commit()

    print(f"\n✅ Migración completada:")
    print(f"   - Migrados: {migrados}")
    print(f"   - Errores: {errores}")
    print(f"   - Total: {total}")

def verify_migration():
    """Verifica que la migración fue exitosa"""

    total = Viaje.query.count()
    con_datos = Viaje.query.filter(Viaje.datos.isnot(None)).count()
    sin_datos = total - con_datos

    print(f"\n📊 Verificación:")
    print(f"   - Total viajes: {total}")
    print(f"   - Con datos JSONB: {con_datos}")
    print(f"   - Sin datos JSONB: {sin_datos}")

    # Mostrar ejemplos
    print(f"\n📋 Ejemplos de migración:")
    ejemplos = Viaje.query.filter(Viaje.datos.isnot(None)).limit(3).all()
    for v in ejemplos:
        print(f"\n   Viaje {v.id} ({v.tipo}):")
        print(f"   datos = {json.dumps(v.datos, indent=2, ensure_ascii=False)[:300]}...")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        if len(sys.argv) > 1 and sys.argv[1] == '--verify':
            verify_migration()
        else:
            migrate_viajes()
            verify_migration()
