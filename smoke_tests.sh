#!/bin/bash
echo "🧪 Running smoke tests..."
echo ""

BASE_URL="https://mi-agente-viajes-454542398872.us-east1.run.app"

# 1. Home carga
echo "1. Home carga..."
RESULT=$(curl -s $BASE_URL | grep -o "Próximos Viajes ([0-9]*)")
if [ -n "$RESULT" ]; then
    echo "   ✅ $RESULT"
else
    echo "   ❌ FALLO"
fi

# 2. API count
echo "2. API viajes/count..."
RESULT=$(curl -s $BASE_URL/api/viajes/count)
if echo "$RESULT" | grep -q "count"; then
    echo "   ✅ $RESULT"
else
    echo "   ❌ FALLO: $RESULT"
fi

# 3. Cron emails
echo "3. Cron process-emails..."
RESULT=$(curl -s -X POST $BASE_URL/cron/process-emails)
if echo "$RESULT" | grep -q "success"; then
    echo "   ✅ OK"
else
    echo "   ❌ FALLO: $RESULT"
fi

# 4. Cron flights
echo "4. Cron check-flights..."
RESULT=$(curl -s -X POST $BASE_URL/cron/check-flights)
if echo "$RESULT" | grep -q "success"; then
    echo "   ✅ OK"
else
    echo "   ❌ FALLO: $RESULT"
fi

# 5. Calendario
echo "5. Calendar feed..."
RESULT=$(curl -s $BASE_URL/calendar-feed | head -1)
if echo "$RESULT" | grep -q "BEGIN:VCALENDAR"; then
    echo "   ✅ OK"
else
    echo "   ❌ FALLO"
fi

echo ""
echo "🏁 Smoke tests completados"
