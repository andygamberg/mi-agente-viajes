#!/bin/bash
# scripts/setup-gcloud.sh
# Configura gcloud en Codespaces para deploy automático
# 
# PREREQUISITOS:
# 1. Service Account creada en GCP con roles correctos
# 2. Secret GCLOUD_SERVICE_KEY configurado en GitHub Codespaces
#
# USO:
# ./scripts/setup-gcloud.sh
#
# Después de ejecutar, gcloud estará listo para deploy sin intervención.

set -e

echo "🔧 Configurando gcloud para deploy automático..."

# Verificar que el secret existe
if [ -z "$GCLOUD_SERVICE_KEY" ]; then
    echo "❌ Error: GCLOUD_SERVICE_KEY no está configurado"
    echo ""
    echo "Para configurar:"
    echo "1. Crear Service Account en GCP (ver docs/GCLOUD_SETUP.md)"
    echo "2. Agregar secret en: GitHub → Repo → Settings → Secrets → Codespaces"
    echo "   Name: GCLOUD_SERVICE_KEY"
    echo "   Value: contenido del archivo JSON de la Service Account"
    exit 1
fi

# Instalar gcloud si no existe
if ! command -v gcloud &> /dev/null; then
    echo "📦 Instalando gcloud CLI..."
    curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=$HOME
    
    # Agregar al PATH permanentemente
    echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    
    echo "✅ gcloud CLI instalado"
else
    echo "✅ gcloud CLI ya instalado"
fi

# Asegurar que gcloud está en el PATH de esta sesión
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Activar service account
echo "🔐 Activando Service Account..."
echo "$GCLOUD_SERVICE_KEY" > /tmp/gcloud-key.json
gcloud auth activate-service-account --key-file=/tmp/gcloud-key.json --quiet
gcloud config set project mi-agente-viajes --quiet
rm /tmp/gcloud-key.json

# Verificar configuración
echo ""
echo "✅ gcloud configurado correctamente"
echo "   Cuenta: $(gcloud config get-value account)"
echo "   Proyecto: $(gcloud config get-value project)"
echo ""
echo "🚀 Listo para deploy:"
echo "   gcloud run deploy mi-agente-viajes --source . --region us-east1 --allow-unauthenticated"
