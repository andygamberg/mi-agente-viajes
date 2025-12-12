#!/bin/bash
# scripts/setup-gcloud.sh
# Configura gcloud en Codespaces para deploy automático

set -e

echo "🔧 Configurando gcloud..."

# Verificar que el secret existe
if [ -z "$GCLOUD_SERVICE_KEY" ]; then
    echo "❌ Error: GCLOUD_SERVICE_KEY no está configurado"
    echo "   Agregalo en: GitHub → Repo → Settings → Secrets → Codespaces"
    exit 1
fi

# Instalar gcloud si no existe
if ! command -v gcloud &> /dev/null; then
    echo "📦 Instalando gcloud CLI..."
    curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=$HOME
    echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi

# Activar service account
echo "$GCLOUD_SERVICE_KEY" > /tmp/gcloud-key.json
gcloud auth activate-service-account --key-file=/tmp/gcloud-key.json --quiet
gcloud config set project mi-agente-viajes --quiet
rm /tmp/gcloud-key.json

echo "✅ gcloud configurado correctamente"
echo "   Proyecto: mi-agente-viajes"
echo "   Listo para deploy"
