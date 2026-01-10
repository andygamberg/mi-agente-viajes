#!/bin/bash
# Script para probar notificaciones push - Mi Agente Viajes

BASE_URL="https://mi-agente-viajes-454542398872.us-east1.run.app"

echo "🧪 Test de Notificaciones Push - Mi Agente Viajes"
echo "=================================================="
echo ""

# Verificar que se proporcionó el cookie
if [ -z "$SESSION_COOKIE" ]; then
    echo "❌ Error: Falta la variable SESSION_COOKIE"
    echo ""
    echo "Uso:"
    echo "  1. Abre la app en tu navegador e inicia sesión"
    echo "  2. Abre las DevTools (F12) y ve a Application > Cookies"
    echo "  3. Copia el valor de la cookie 'session'"
    echo "  4. Ejecuta:"
    echo "     export SESSION_COOKIE='tu-cookie-aqui'"
    echo "     ./test_push.sh"
    echo ""
    exit 1
fi

echo "📡 Verificando estado de suscripción push..."
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/push/status" \
    -H "Cookie: session=$SESSION_COOKIE" \
    -H "Content-Type: application/json")

echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
echo ""

# Verificar si está suscrito
IS_SUBSCRIBED=$(echo "$STATUS_RESPONSE" | grep -o '"subscribed":[^,}]*' | cut -d':' -f2 | tr -d ' ')

if [ "$IS_SUBSCRIBED" = "false" ]; then
    echo "⚠️  No estás suscrito a notificaciones push"
    echo "   Por favor abre la app en tu dispositivo móvil y acepta las notificaciones"
    echo ""
    exit 1
fi

echo "✅ Suscripción activa encontrada"
echo ""

echo "📤 Enviando notificación de prueba..."
TEST_RESPONSE=$(curl -s -X POST "$BASE_URL/api/push/test" \
    -H "Cookie: session=$SESSION_COOKIE" \
    -H "Content-Type: application/json")

echo "$TEST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TEST_RESPONSE"
echo ""

# Verificar resultado
SENT=$(echo "$TEST_RESPONSE" | grep -o '"sent":[0-9]*' | cut -d':' -f2)

if [ "$SENT" -gt 0 ]; then
    echo "✅ ¡Notificación enviada exitosamente!"
    echo "   Revisa tu dispositivo móvil - deberías ver la notificación"
else
    echo "❌ No se pudo enviar la notificación"
    echo "   Detalles del error arriba"
fi

echo ""
echo "=================================================="
