#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de OAuth y procesamiento de emails.
Ejecutar localmente con acceso a la base de datos de producción.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app import app
from models import db, User, EmailConnection, UserEmail, Viaje, ProcessedEmail

def diagnose():
    with app.app_context():
        print("=" * 60)
        print("🔍 DIAGNÓSTICO DE OAUTH Y PROCESAMIENTO DE EMAILS")
        print("=" * 60)
        print(f"Fecha/Hora: {datetime.now()}")
        print()

        # 1. Listar todos los usuarios
        print("\n📋 USUARIOS REGISTRADOS")
        print("-" * 40)
        users = User.query.all()
        for user in users:
            print(f"  ID {user.id}: {user.nombre} <{user.email}>")
            print(f"    - nombre_pax: {user.nombre_pax}, apellido_pax: {user.apellido_pax}")
            print(f"    - Notif email: {user.notif_email_master}, push: {user.notif_push_master}")

        # 2. Listar emails adicionales (UserEmail)
        print("\n📧 EMAILS ADICIONALES (UserEmail)")
        print("-" * 40)
        try:
            user_emails = UserEmail.query.all()
            if user_emails:
                for ue in user_emails:
                    user = User.query.get(ue.user_id)
                    print(f"  {ue.email} -> Usuario {ue.user_id} ({user.nombre if user else 'N/A'})")
            else:
                print("  (No hay emails adicionales registrados)")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        # 3. Conexiones OAuth
        print("\n🔐 CONEXIONES OAUTH")
        print("-" * 40)
        now = datetime.utcnow()
        connections = EmailConnection.query.order_by(EmailConnection.user_id).all()

        for conn in connections:
            user = User.query.get(conn.user_id)
            print(f"\n  [{conn.provider.upper()}] {conn.email}")
            print(f"    Usuario: {user.nombre if user else 'N/A'} (ID: {conn.user_id})")
            print(f"    Estado: {'✅ Activo' if conn.is_active else '❌ Inactivo'}")

            # Watch expiration (Gmail)
            if conn.provider == 'gmail':
                if conn.watch_expiration:
                    if conn.watch_expiration < now:
                        print(f"    Watch: ⚠️ EXPIRADO desde {conn.watch_expiration}")
                    elif conn.watch_expiration < now + timedelta(hours=24):
                        print(f"    Watch: ⏰ Expira pronto ({conn.watch_expiration})")
                    else:
                        print(f"    Watch: ✅ Válido hasta {conn.watch_expiration}")
                else:
                    print(f"    Watch: ❌ Sin watch configurado")
                print(f"    History ID: {conn.history_id or '(ninguno)'}")

            # Token expiry (Microsoft principalmente)
            if conn.token_expiry:
                if conn.token_expiry < now:
                    print(f"    Token: ⚠️ EXPIRADO desde {conn.token_expiry}")
                else:
                    print(f"    Token: ✅ Válido hasta {conn.token_expiry}")

            print(f"    Último scan: {conn.last_scan or 'Nunca'}")
            print(f"    Emails procesados: {conn.emails_processed}")
            if conn.last_error:
                print(f"    Último error: {conn.last_error[:100]}...")

        # 4. Buscar emails específicos
        print("\n🔎 VERIFICACIÓN DE EMAILS ESPECÍFICOS")
        print("-" * 40)
        emails_to_check = [
            'agamberg@familiabercomat.com',
            'veronica@ggya.com.ar',
            'sol@gamberg.com.ar'
        ]

        for email in emails_to_check:
            print(f"\n  📧 {email}")

            # ¿Es usuario principal?
            user = User.query.filter_by(email=email).first()
            if user:
                print(f"    ✅ Usuario principal: {user.nombre} (ID: {user.id})")
            else:
                print(f"    ❌ No es usuario principal")

            # ¿Es email adicional?
            try:
                ue = UserEmail.query.filter_by(email=email).first()
                if ue:
                    owner = User.query.get(ue.user_id)
                    print(f"    ✅ Email adicional de: {owner.nombre if owner else 'N/A'}")
                else:
                    print(f"    ❌ No está en emails adicionales")
            except:
                pass

            # ¿Tiene conexión OAuth?
            conn = EmailConnection.query.filter_by(email=email).first()
            if conn:
                print(f"    ✅ Conexión OAuth: {conn.provider}, activo: {conn.is_active}")
                if conn.provider == 'gmail' and conn.watch_expiration:
                    status = "EXPIRADO" if conn.watch_expiration < now else "OK"
                    print(f"       Watch: {status} ({conn.watch_expiration})")
            else:
                print(f"    ❌ Sin conexión OAuth")

        # 5. Viajes recientes
        print("\n✈️ VIAJES RECIENTES (últimos 30 días)")
        print("-" * 40)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_viajes = Viaje.query.filter(
            Viaje.creado >= thirty_days_ago
        ).order_by(Viaje.creado.desc()).limit(20).all()

        for v in recent_viajes:
            user = User.query.get(v.user_id) if v.user_id else None
            print(f"  {v.creado.strftime('%Y-%m-%d %H:%M')} | {v.tipo} | {v.origen}->{v.destino}")
            print(f"    Usuario: {user.email if user else '(sin asignar)'} | Source: {v.source}")
            print(f"    Código: {v.codigo_reserva or 'N/A'}")

        # 6. Estadísticas de ProcessedEmail
        print("\n📊 EMAILS PROCESADOS (últimos 7 días)")
        print("-" * 40)
        week_ago = datetime.now() - timedelta(days=7)
        try:
            processed = ProcessedEmail.query.filter(
                ProcessedEmail.processed_at >= week_ago
            ).all()
            print(f"  Total procesados: {len(processed)}")
            with_reservation = sum(1 for p in processed if p.had_reservation)
            print(f"  Con reservas: {with_reservation}")
            print(f"  Sin reservas: {len(processed) - with_reservation}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        print("\n" + "=" * 60)
        print("✅ Diagnóstico completado")
        print("=" * 60)


if __name__ == '__main__':
    diagnose()
