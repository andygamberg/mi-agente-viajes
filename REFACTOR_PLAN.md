# 🔧 PLAN DE REFACTORING - Mi Agente Viajes

**Fecha:** 7 Diciembre 2025
**Objetivo:** Preparar arquitectura para multi-usuario (MVP6)

---

## 📊 ESTADO ACTUAL

### Archivos Python:
| Archivo | Líneas | Propósito | Estado |
|---------|--------|-----------|--------|
| app.py | 1362 | MONOLITO - todo junto | 🔴 Refactorizar |
| email_processor.py | 200 | Gmail API helpers | ✅ OK |
| gmail_to_db.py | 250 | Orquesta email→BD | ✅ OK |
| flight_monitor.py | 200 | FR24 API | ✅ OK |
| scheduler.py | 100 | Cloud Scheduler | ⚠️ Revisar si se usa |
| process_emails_standalone.py | 50 | Script manual | ⚠️ Posible obsoleto |

### Templates:
| Template | Tamaño | Estado |
|----------|--------|--------|
| index.html | 40KB | ✅ Usado (pero grande) |
| agregar.html | 9KB | ✅ Usado |
| carga_rapida.html | 8KB | ✅ Usado |
| check_flights.html | 1KB | ✅ Usado |
| revisar_vuelos.html | 10KB | ❌ NO USADO - eliminar |
| agregar_prellenado.html | 4KB | ❌ NO USADO - eliminar |

---

## 🎯 PLAN DE REFACTORING

### Fase 1: Crear estructura de módulos (30 min)
```
mi-agente-viajes/
├── app.py              # Solo Flask app, rutas, config
├── models.py           # User, Viaje (SQLAlchemy)
├── auth.py             # Login, register, logout, decorators
├── email_processor.py  # (ya existe)
├── gmail_to_db.py      # (ya existe)
├── flight_monitor.py   # (ya existe)
├── utils/
│   ├── __init__.py
│   ├── iata.py         # IATA_TO_CITY dict + helpers
│   ├── claude.py       # extraer_info_con_claude()
│   └── calendar.py     # Lógica de calendario .ics
└── templates/
    └── (solo los usados)
```

### Fase 2: Extraer models.py (15 min)
- Mover clase Viaje
- Crear clase User
- Configurar relaciones

### Fase 3: Crear auth.py (30 min)
- Flask-Login setup
- /register, /login, /logout
- Decorator @login_required
- Hash passwords con werkzeug

### Fase 4: Extraer utilidades (20 min)
- IATA_TO_CITY → utils/iata.py
- extraer_info_con_claude → utils/claude.py
- Calendario → utils/calendar.py

### Fase 5: Limpiar (10 min)
- Eliminar templates no usados
- Eliminar archivos obsoletos
- Actualizar imports en app.py

### Fase 6: Migrar BD (15 min)
- Agregar user_id a Viaje
- Crear tabla User
- Migrar datos existentes (asignar a user default)

---

## 📋 ORDEN DE EJECUCIÓN

1. [ ] Eliminar templates no usados
2. [ ] Crear models.py (User + Viaje)
3. [ ] Crear auth.py (Flask-Login)
4. [ ] Crear utils/iata.py
5. [ ] Actualizar app.py imports
6. [ ] Test local
7. [ ] Deploy + smoke tests
8. [ ] Crear utils/claude.py (opcional, puede quedar en app.py)
9. [ ] Crear utils/calendar.py (opcional, puede quedar en app.py)

---

## ⚠️ RIESGOS

| Riesgo | Mitigación |
|--------|------------|
| Romper imports | Test local antes de deploy |
| BD incompatible | Backup antes de migrar |
| Sesiones rotas | Probar login/logout exhaustivamente |

---

## 🔙 ROLLBACK

Si algo falla:
```bash
git checkout v1.3-pre-multiuser
gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated
```

---

## ✅ DEFINICIÓN DE DONE

- [ ] models.py creado con User y Viaje
- [ ] auth.py funcionando (/register, /login, /logout)
- [ ] Rutas protegidas con @login_required
- [ ] Templates no usados eliminados
- [ ] Smoke tests pasan
- [ ] Usuario puede registrarse, loguearse, ver sus viajes

