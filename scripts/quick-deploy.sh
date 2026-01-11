#!/bin/bash
# scripts/quick-deploy.sh
# Reautentica gcloud y hace deploy

set -e

echo "🔐 Iniciando autenticación de gcloud..."
echo ""
/opt/homebrew/bin/gcloud auth login

echo ""
echo "🚀 Haciendo deploy a Cloud Run..."
/opt/homebrew/bin/gcloud run deploy mi-agente-viajes \
    --source . \
    --region us-east1 \
    --allow-unauthenticated \
    --project mi-agente-viajes

echo ""
echo "✅ Deploy completado!"
echo ""
echo "🔍 Ejecutando diagnóstico de OAuth..."
curl -s "https://mi-agente-viajes-454542398872.us-east1.run.app/api/debug/oauth-status" \
    -H "X-Admin-Key: mv-admin-2025-xK9mP2" | python3 -m json.tool
