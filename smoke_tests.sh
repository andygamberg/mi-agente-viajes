#!/bin/bash
echo "🧪 Running smoke tests..."
echo ""

BASE_URL="https://mi-agente-viajes-454542398872.us-east1.run.app"

# 1. Login page carga
echo "1. Login page..."
curl -s $BASE_URL/login | grep -q "Iniciar" && echo "   ✅ Login OK" || echo "   ❌ FAIL"

# 2. Register page carga
echo "2. Register page..."
curl -s $BASE_URL/register | grep -q "Crear Cuenta" && echo "   ✅ Register OK" || echo "   ❌ FAIL"

# 3. Home redirige a login
echo "3. Home requiere auth..."
[ "$(curl -s -o /dev/null -w '%{http_code}' $BASE_URL/)" = "302" ] && echo "   ✅ Redirige a login (302)" || echo "   ❌ FAIL"

# 4. Perfil redirige a login
echo "4. Perfil requiere auth..."
[ "$(curl -s -o /dev/null -w '%{http_code}' $BASE_URL/perfil)" = "302" ] && echo "   ✅ Redirige a login (302)" || echo "   ❌ FAIL"

# 5. API count
echo "5. API viajes/count..."
curl -s $BASE_URL/api/viajes/count | grep -q "count" && echo "   ✅ OK" || echo "   ❌ FAIL"

# 6. Cron emails (sin auth debe dar 403)
echo "6. Cron process-emails sin auth (debe dar 403)..."
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE_URL/cron/process-emails)" = "403" ] && echo "   ✅ OK (403 Forbidden)" || echo "   ❌ FAIL"

# 7. Cron flights (sin auth debe dar 403)
echo "7. Cron check-flights sin auth (debe dar 403)..."
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE_URL/cron/check-flights)" = "403" ] && echo "   ✅ OK (403 Forbidden)" || echo "   ❌ FAIL"

# 8. MVP9: Calendar feed SIN token → 403
echo "8. Calendar feed sin token (debe dar 403)..."
[ "$(curl -s -o /dev/null -w '%{http_code}' $BASE_URL/calendar-feed)" = "403" ] && echo "   ✅ OK (403 Forbidden)" || echo "   ❌ FAIL"

# 9. MVP9: Calendar feed con token INVÁLIDO → 404
echo "9. Calendar feed token inválido (debe dar 404)..."
[ "$(curl -s -o /dev/null -w '%{http_code}' $BASE_URL/calendar-feed/token-invalido-12345)" = "404" ] && echo "   ✅ OK (404 Not Found)" || echo "   ❌ FAIL"

# 10. Migrate DB (sin auth debe dar 403)
echo "10. Migrate DB sin auth (debe dar 403)..."
[ "$(curl -s -o /dev/null -w '%{http_code}' $BASE_URL/migrate-db)" = "403" ] && echo "   ✅ OK (403 Forbidden)" || echo "   ❌ FAIL"

# 10b. Migrate DB (con auth debe funcionar)
echo "10b. Migrate DB con auth..."
curl -s -H "X-Admin-Key: ${ADMIN_SECRET_KEY:-dev-secret-123}" $BASE_URL/migrate-db | grep -q "success" && echo "   ✅ OK" || echo "   ❌ FAIL"

# 11. Cron checkin-reminders (sin auth debe dar 403)
echo "11. Cron checkin-reminders sin auth (debe dar 403)..."
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE_URL/cron/checkin-reminders)" = "403" ] && echo "   ✅ OK (403 Forbidden)" || echo "   ❌ FAIL"

echo ""
echo "🏁 Smoke tests completados (12 tests)"
echo ""
echo "📝 NOTAS:"
echo "   - Para probar migrate-db: export ADMIN_SECRET_KEY=tu-secret"
echo "   - Crons ahora requieren header X-Appengine-Cron (Cloud Scheduler lo envía automáticamente)"
echo "   - Calendar feed: ir a Preferencias → Calendario para obtener link personal"
