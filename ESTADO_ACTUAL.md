# Estado del Proyecto - 4 Diciembre 2025

## ✅ PRODUCCIÓN FUNCIONANDO
- **Versión activa:** mi-agente-viajes-00009-zdh (2 dic 20:42 UTC)
- **URL:** https://mi-agente-viajes-454542398872.us-east1.run.app
- **Funcionalidades:** PDFs, Calendar, vuelos funcionan OK

## ❌ PROBLEMA IDENTIFICADO
- Todos los deploys del 3-4 diciembre están rotos
- PDFs no se procesan en producción (funciona local)
- ANTHROPIC_API_KEY está configurada pero no funciona

## 🔍 DEBUGGING REALIZADO
- Variables de entorno verificadas: OK
- Base de datos PostgreSQL: OK (todos los campos)
- Template flash messages: OK
- Código local: FUNCIONA PERFECTO
- Problema: deploy de Cloud Run no aplica cambios correctamente

## 📝 LECCIONES APRENDIDAS
1. `gcloud run deploy` sin --set-env-vars BORRA las variables
2. Siempre hacer rollback test antes de modificar más
3. Necesitamos mejor estrategia de deploy

## 🚀 PRÓXIMOS PASOS (PRÓXIMA SESIÓN)
1. Partir desde versión 00009-zdh que funciona
2. Hacer UN cambio a la vez y verificar
3. NO modificar app.py con scripts Python (hizo desastre)
4. Considerar usar GitHub Actions o Cloud Build para deploy
5. Continuar con MVP 5 (Email monitoring) una vez estable

## 💾 BACKUPS
- app.py.backup
- app.py.backup2
- Versión funcionando: 00009-zdh

## ⚠️ NO REPETIR
- No usar `cat >>` para agregar código
- No usar scripts Python para modificar app.py
- Siempre especificar env vars en deploy
- Verificar cambios ANTES de pushear a producción
