#!/bin/bash
# Script de prueba de push notifications usando endpoint admin

BASE_URL="https://mi-agente-viajes-454542398872.us-east1.run.app"
ADMIN_KEY="mv-admin-2025-xK9mP2"

echo "🧪 Test de Notificaciones Push - Admin Mode"
echo "============================================="
echo ""

if [ -z "$1" ]; then
    echo "Uso:"
    echo "  ./test_push_admin.sh <user_id> [all]"
    echo ""
    echo "Ejemplos:"
    echo "  ./test_push_admin.sh 1          # Enviar 1 notificación de prueba"
    echo "  ./test_push_admin.sh 1 all      # Enviar las 3 notificaciones de prueba"
    echo ""
    exit 1
fi

USER_ID=$1
SEND_ALL=""

if [ "$2" = "all" ]; then
    SEND_ALL="?all=true"
    echo "📤 Enviando 3 notificaciones de prueba al usuario $USER_ID..."
else
    echo "📤 Enviando 1 notificación de prueba al usuario $USER_ID..."
fi

echo ""

RESPONSE=$(curl -s -X POST "$BASE_URL/api/push/admin/test/$USER_ID$SEND_ALL" \
    -H "X-Admin-Key: $ADMIN_KEY" \
    -H "Content-Type: application/json")

# Pretty print JSON si es posible
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Extraer resultado
SUCCESS=$(echo "$RESPONSE" | grep -o '"success":[^,}]*' | cut -d':' -f2 | tr -d ' ')
SENT=$(echo "$RESPONSE" | grep -o '"total_sent":[0-9]*' | cut -d':' -f2)
ATTEMPTS=$(echo "$RESPONSE" | grep -o '"total_attempts":[0-9]*' | cut -d':' -f2)

if [ "$SUCCESS" = "true" ] && [ "$SENT" -gt 0 ]; then
    echo "✅ ¡Notificaciones enviadas exitosamente! ($SENT/$ATTEMPTS)"
    echo "   Revisa tu dispositivo móvil - deberías ver las notificaciones"
elif [ "$SUCCESS" = "true" ]; then
    echo "⚠️  Las notificaciones se procesaron pero no se enviaron"
    echo "   El usuario probablemente no tiene suscripciones push activas"
else
    echo "❌ Error enviando notificaciones"
    echo "   Revisa el mensaje de error arriba"
fi

echo ""
echo "============================================="
