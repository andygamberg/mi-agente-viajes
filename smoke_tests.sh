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

# 6. Cron emails
echo "6. Cron process-emails..."
curl -s -X POST $BASE_URL/cron/process-emails | grep -q "success" && echo "   ✅ OK" || echo "   ❌ FAIL"

# 7. Cron flights
echo "7. Cron check-flights..."
curl -s -X POST $BASE_URL/cron/check-flights | grep -q "success" && echo "   ✅ OK" || echo "   ❌ FAIL"

# 8. Calendario
echo "8. Calendar feed..."
curl -s $BASE_URL/calendar-feed | grep -q "BEGIN:VCALENDAR" && echo "   ✅ OK" || echo "   ❌ FAIL"

# 9. Migrate DB
echo "9. Migrate DB..."
curl -s $BASE_URL/migrate-db | grep -q "success" && echo "   ✅ OK" || echo "   ❌ FAIL"

echo ""
echo "🏁 Smoke tests completados (9 tests)"
