"""
Script standalone para procesar emails
Se ejecuta desde Cloud Scheduler
"""
from email_processor import fetch_unread_emails
from app import app, db, Viaje, extraer_info_con_claude
from datetime import datetime

def main():
    with app.app_context():
        print('🔍 Buscando emails...')
        emails = fetch_unread_emails()
        
        if not emails:
            print('✅ No hay emails nuevos')
            return
        
        vuelos_creados = 0
        for email in emails:
            print(f'📧 {email["subject"][:60]}')
            vuelos = extraer_info_con_claude(email['body'])
            
            if not vuelos:
                continue
            
            for v in vuelos:
                existe = Viaje.query.filter_by(
                    numero_vuelo=v.get('numero_vuelo'),
                    fecha_salida=v.get('fecha_salida')
                ).first()
                
                if not existe:
                    viaje = Viaje(
                        tipo='vuelo',
                        descripcion=f"{v.get('origen')} → {v.get('destino')}",
                        origen=v.get('origen'),
                        destino=v.get('destino'),
                        fecha_salida=v.get('fecha_salida'),
                        hora_salida=v.get('hora_salida'),
                        aerolinea=v.get('aerolinea'),
                        numero_vuelo=v.get('numero_vuelo')
                    )
                    db.session.add(viaje)
                    vuelos_creados += 1
            
            db.session.commit()
        
        print(f'✅ Creados {vuelos_creados} vuelos')

if __name__ == '__main__':
    main()
