# 🚀 GCP Deploy Automático desde GitHub Codespaces

> Guía para configurar deploy sin intervención humana.  
> **Portable a cualquier proyecto Flask/Python en Cloud Run.**

---

## 📋 Resumen

Esta guía configura:
- Service Account con permisos mínimos necesarios
- Secret en Codespaces con credenciales
- Script de setup que instala y autentica gcloud
- Deploy automático sin password

**Tiempo estimado:** 15-20 minutos  
**Prerequisitos:** Proyecto GCP existente con Cloud Run habilitado

---

## Paso 1: Crear Service Account

### En Google Cloud Console

```
https://console.cloud.google.com/iam-admin/serviceaccounts?project=TU_PROYECTO
```

1. Click **"+ Crear cuenta de servicio"** / **"+ Create Service Account"**
2. Nombre: `codespaces-deploy`
3. Click **"Crear y continuar"** / **"Create and Continue"**
4. **Saltar** asignación de roles aquí (los agregamos en IAM después)
5. Click **"Listo"** / **"Done"**

### Crear clave JSON

1. En la lista, click en `codespaces-deploy@TU_PROYECTO.iam.gserviceaccount.com`
2. Tab **"Claves"** / **"Keys"**
3. **"Agregar clave"** / **"Add Key"** → **"Crear clave nueva"** / **"Create new key"**
4. Seleccionar **JSON** → **"Crear"** / **"Create"**
5. Se descarga el archivo - **guardarlo seguro**

---

## Paso 2: Asignar Roles en IAM

### En Google Cloud Console

```
https://console.cloud.google.com/iam-admin/iam?project=TU_PROYECTO
```

1. Click **"+ Otorgar acceso"** / **"+ Grant Access"**
2. Principal: `codespaces-deploy@TU_PROYECTO.iam.gserviceaccount.com`
3. Agregar estos 6 roles (uno por uno con "+ Agregar otro rol"):

| # | Rol (Español) | Rol (English) | ID |
|---|---------------|---------------|-----|
| 1 | Administrador de Cloud Run | Cloud Run Admin | `roles/run.admin` |
| 2 | Administrador de Artifact Registry | Artifact Registry Admin | `roles/artifactregistry.admin` |
| 3 | Administrador de almacenamiento | Storage Admin | `roles/storage.admin` |
| 4 | Editor de Cloud Build | Cloud Build Editor | `roles/cloudbuild.builds.editor` |
| 5 | Usuario de cuenta de servicio | Service Account User | `roles/iam.serviceAccountUser` |
| 6 | Consumidor de Service Usage | Service Usage Consumer | `roles/serviceusage.serviceUsageConsumer` |

4. Click **"Guardar"** / **"Save"**

### APIs necesarias

Habilitar si no están activas:
- Cloud Resource Manager API
- Cloud Build API
- Artifact Registry API
- Cloud Run API

---

## Paso 3: Agregar Secret a GitHub Codespaces

### En GitHub

```
https://github.com/TU_USUARIO/TU_REPO/settings/secrets/codespaces
```

1. Click **"New repository secret"**
2. Name: `GCLOUD_SERVICE_KEY`
3. Value: Pegar **todo** el contenido del archivo JSON descargado
4. Click **"Add secret"**

---

## Paso 4: Crear Script de Setup

Crear `scripts/setup-gcloud.sh` en el repo:

```bash
#!/bin/bash
# scripts/setup-gcloud.sh
# Configura gcloud en Codespaces para deploy automático

set -e

PROJECT_ID="TU_PROYECTO"
REGION="us-east1"

echo "🔧 Configurando gcloud..."

# Verificar que el secret existe
if [ -z "$GCLOUD_SERVICE_KEY" ]; then
    echo "❌ Error: GCLOUD_SERVICE_KEY no está configurado"
    exit 1
fi

# Instalar gcloud si no existe
if ! command -v gcloud &> /dev/null; then
    curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=$HOME
fi

# Agregar al PATH
echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Activar service account
echo "$GCLOUD_SERVICE_KEY" > /tmp/gcloud-key.json
gcloud auth activate-service-account --key-file=/tmp/gcloud-key.json --quiet
gcloud config set project $PROJECT_ID --quiet
rm /tmp/gcloud-key.json

echo "✅ gcloud configurado"
```

---

## Paso 5: Usar en Codespaces

### Primera vez (o después de rebuild)

```bash
./scripts/setup-gcloud.sh
gcloud run services list --region us-east1
```

### Deploy

```bash
gcloud run deploy NOMBRE_SERVICIO --source . --region us-east1 --allow-unauthenticated
```

---

## Troubleshooting

### "gcloud: command not found"

```bash
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
```

### "Permission denied"

Verificar que el Service Account tiene todos los 6 roles.  
Esperar 1-2 minutos para propagación.

### "GCLOUD_SERVICE_KEY no está configurado"

Hacer Rebuild del Codespace para cargar nuevos secrets.

---

## Roles explicados

| Rol | Para qué se necesita |
|-----|---------------------|
| Cloud Run Admin | Crear/actualizar servicios en Cloud Run |
| Artifact Registry Admin | Guardar imágenes Docker del build |
| Storage Admin | Subir código fuente al bucket temporal |
| Cloud Build Editor | Ejecutar el proceso de build |
| Service Account User | Actuar como la cuenta de servicio |
| Service Usage Consumer | Usar las APIs del proyecto |

---

## Seguridad

- ✅ Service Account con permisos mínimos (no Owner/Editor)
- ✅ Clave JSON solo en GitHub Secrets (nunca en código)
- ✅ Clave se elimina después de autenticar
- ⚠️ Rotar clave periódicamente (cada 90 días recomendado)

---

*Documentado: 12 Diciembre 2025*  
*Probado en: GitHub Codespaces + Google Cloud Run*
