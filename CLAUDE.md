# CLAUDE.md - Manifiesto Operativo

## 🎯 Identidad del Proyecto

**Proyecto:** Mi Agente Viajes  
**Stack:** Flask + PostgreSQL + Google Cloud Run  
**Producción:** https://mi-agente-viajes-454542398872.us-east1.run.app  
**Repo:** github.com/andygamberg/mi-agente-viajes

---

## 🏆 Prioridades Inmutables (en orden)

1. **UX > Features > Performance**
2. **Mobile-first** siempre
3. **Principios de diseño** en UX_UI_ROADMAP.md son ley
4. **No emojis en UI**, solo Heroicons SVG

---

## ✅ Antes de cada cambio

- [ ] Revisar `UX_UI_ROADMAP.md`
- [ ] Verificar consistencia con `DESIGN_SYSTEM.md`
- [ ] Considerar impacto mobile
- [ ] Buscar info en Project Knowledge antes de preguntar a Andy

---

## 🚫 No hacer sin preguntar a Andy

- Cambios de arquitectura de BD
- Eliminar features existentes
- Cambiar URLs o endpoints públicos
- Modificar flujos de autenticación

---

## 🤖 División de Roles

| Andy (Humano) | Claude Code (Agente) |
|---------------|----------------------|
| Decisiones de producto y UX | Edición de archivos |
| Validación de cambios | Implementación de features |
| Aprobación de deploys | Refactors y fixes |
| Prioridades de negocio | Proponer soluciones técnicas |
| Comandos: git, gcloud | NUNCA ejecutar git ni deploy |

---

## ⚡ Principios Operativos

### 0. Andy es la última opción
**CRÍTICO:** Antes de pedir información a Andy, agotar:
1. Project Knowledge (archivos del repo)
2. `conversation_search` (conversaciones pasadas)
3. Terminal (`cat`, `ls`, `grep`)

Solo preguntar si no se puede resolver de otra manera.

### 1. Archivos UNO a la vez
Crear/editar UN archivo, esperar confirmación, luego el siguiente.  
Múltiples archivos simultáneos causan errores de "incompatible messages".

### 2. Verificar antes de actuar
- `cat archivo` para ver contenido actual
- `tail -10 archivo` antes de commitear archivos largos
- `git status` para ver estado

### 3. No truncar archivos largos
Para archivos >150 líneas:
- Usar `str_replace` para ediciones quirúrgicas
- NUNCA regenerar archivo completo que pueda truncarse

---

## 🔄 Workflow de Deploy

```bash
# 1. Editar archivos necesarios (uno a la vez)

# 2. Commit y push
git add . && git commit -m "mensaje descriptivo" && git push

# 3. Deploy
gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated

# 4. Smoke tests
./smoke_tests.sh

# 5. Sync Project Knowledge (manual en Claude.ai)

# 6. Reportar resultado a Andy
```

---

## 🔄 Triggers de Mejora Continua

| Situación | Acción | Archivo a actualizar |
|-----------|--------|----------------------|
| Algo salió mal | Documentar error + solución | `docs/APRENDIZAJES.md` |
| Pattern exitoso | Documentar qué y por qué funciona | `docs/APRENDIZAJES.md` |
| Cambio en proceso | Actualizar pasos | `METODOLOGIA_TRABAJO.md` |
| Nuevo principio UX | Agregar a principios | `UX_UI_ROADMAP.md` |
| Feature completada | Mover a completados | `ROADMAP.md` |

---

## 📁 Estructura del Proyecto

```
mi-agente-viajes/
├── app.py                 # Config + Factory (75 líneas)
├── auth.py                # Flask-Login
├── models.py              # SQLAlchemy
├── blueprints/            # Rutas organizadas
│   ├── viajes.py          # CRUD principal
│   ├── calendario.py      # iCal feeds
│   ├── api.py             # Endpoints + cron
│   ├── gmail_oauth.py     # OAuth multi-cuenta
│   └── gmail_webhook.py   # Push notifications
├── utils/                 # Helpers
│   ├── iata.py            # Códigos aeropuertos
│   ├── claude.py          # Extracción IA
│   └── gmail_scanner.py   # Escaneo emails
├── templates/             # Jinja2
└── docs/                  # Documentación
    ├── APRENDIZAJES.md
    └── WORKFLOW_AGENTICO.md
```

---

## 📚 Documentación Clave

| Archivo | Cuándo consultar |
|---------|------------------|
| `METODOLOGIA_TRABAJO.md` | Workflow, troubleshooting, convenciones |
| `ROADMAP.md` | Estado del proyecto, próximos MVPs |
| `DESIGN_SYSTEM.md` | Colores, iconos (Heroicons), tipografía |
| `UX_UI_ROADMAP.md` | Decisiones de UX, progressive disclosure |
| `docs/APRENDIZAJES.md` | Lecciones aprendidas, antipatrones |

---

*Última actualización: 12 Diciembre 2025*
