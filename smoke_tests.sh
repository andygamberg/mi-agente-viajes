#!/bin/bash
echo "🧪 Running smoke tests..."
echo ""

BASE_URL="https://mi-agente-viajes-454542398872.us-east1.run.app"

# 1. Login page carga
echo "1. Login page..."
RESULT=$(curl -s $BASE_URL/login | grep -o "Iniciar")
if [ -n "$RESULT" ]; then
    echo "   ✅ Login page OK"
else
    echo "   ❌ FALLO"
fi

# 2. Register page carga
echo "2. Register page..."
RESULT=$(curl -s $BASE_URL/register | grep -o "Crear Cuenta")
if [ -n "$RESULT" ]; then
    echo "   ✅ Register page OK"
else
    echo "   ❌ FALLO"
fi

# 3. Home redirige a login
echo "3. Home requiere auth..."
CODE=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/)
if [ "$CODE" = "302" ]; then
    echo "   ✅ Redirige a login (302)"
else
    echo "   ❌ FALLO: HTTP $CODE"
fi

# 4. API count
echo "4. API viajes/count..."
RESULT=$(curl -s $BASE_URL/api/viajes/count)
if echo "$RESULT" | grep -q "count"; then
    echo "   ✅ $RESULT"
else
    echo "   ❌ FALLO: $RESULT"
fi

# 5. Cron emails
echo "5. Cron process-emails..."
RESULT=$(curl -s -X POST $BASE_URL/cron/process-emails)
if echo "$RESULT" | grep -q "success"; then
    echo "   ✅ OK"
else
    echo "   ❌ FALLO: $RESULT"
fi

# 6. Cron flights
echo "6. Cron check-flights..."
RESULT=$(curl -s -X POST $BASE_URL/cron/check-flights)
if echo "$RESULT" | grep -q "success"; then
    echo "   ✅ OK"
else
    echo "   ❌ FALLO: $RESULT"
fi

# 7. Calendario
echo "7. Calendar feed..."
RESULT=$(curl -s $BASE_URL/calendar-feed | head -1)
if echo "$RESULT" | grep -q "BEGIN:VCALENDAR"; then
    echo "   ✅ OK"
else
    echo "   ❌ FALLO"
fi

# 8. Migrate DB
echo "8. Migrate DB..."
RESULT=$(curl -s $BASE_URL/migrate-db)
if echo "$RESULT" | grep -q "success"; then
    echo "   ✅ OK"
else
    echo "   ❌ FALLO: $RESULT"
fi

echo ""
echo "🏁 Smoke tests completados (8 tests)"
