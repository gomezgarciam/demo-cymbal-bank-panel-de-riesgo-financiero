#!/usr/bin/env bash
# Despliegue seguro, idempotente y aislado (Multi-Demo) en Google Cloud Platform.
# Uso en Google Cloud Shell:
#   ./infra/scripts/deploy_gcp.sh <TU_PROJECT_ID> [us-central1] [demo|enterprise]
#
# Aislamiento en proyectos compartidos:
#   - Base de datos Firestore nombrada dedicada: cymbal-riesgo-db (no toca '(default)')
#   - Prefijo único en todos los recursos: cymbal-riesgo-*
#   - Etiquetas de facturación y filtrado: demo=cymbal-riesgo, app=panel-riesgo-financiero
# Seguridad: NO contiene ni escribe API keys, Project IDs ni credenciales en Git.

set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${2:-us-central1}"
MODE="${3:-demo}"

DEMO_PREFIX="cymbal-riesgo"
REPO_NAME="${DEMO_PREFIX}-containers"
FIRESTORE_DB="${DEMO_PREFIX}-db"
API_SERVICE="${DEMO_PREFIX}-api"
WEB_SERVICE="${DEMO_PREFIX}-web"
SCHEDULER_JOB="${DEMO_PREFIX}-fx-hourly"
SECRET_NAME="${DEMO_PREFIX}-fx-api-key"
API_SA_ID="${DEMO_PREFIX}-api-sa"
SCHED_SA_ID="${DEMO_PREFIX}-scheduler-sa"
LABELS="demo=${DEMO_PREFIX},app=panel-riesgo-financiero,managed-by=deploy-script"
TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: Debes indicar el PROJECT_ID de GCP (o tener GOOGLE_CLOUD_PROJECT activo en Cloud Shell)."
  echo "Uso: ./infra/scripts/deploy_gcp.sh <TU_PROJECT_ID> [us-central1] [demo|enterprise]"
  exit 1
fi

if [[ "${MODE}" != "demo" && "${MODE}" != "enterprise" ]]; then
  echo "ERROR: Modo inválido '${MODE}'. Usa 'demo' o 'enterprise'."
  exit 1
fi

echo "==> Proyecto GCP: ${PROJECT_ID} | Región: ${REGION} | Modo: ${MODE} | Tag: ${TAG}"
echo "==> Aislamiento Multi-Demo: prefijo '${DEMO_PREFIX}-*' | Firestore DB '${FIRESTORE_DB}'"
gcloud config set project "${PROJECT_ID}" >/dev/null

echo "==> 1/7 Habilitando APIs de Google Cloud..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  cloudkms.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com

echo "==> 2/7 Verificando Artifact Registry (${REPO_NAME})..."
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --labels="${LABELS}" \
    --description="Contenedores verificados de Cymbal Bank — Panel de Riesgo Financiero"
fi

echo "==> 3/7 Verificando base de datos Cloud Firestore aislada (${FIRESTORE_DB})..."
if ! gcloud firestore databases describe --database="${FIRESTORE_DB}" >/dev/null 2>&1; then
  gcloud firestore databases create \
    --database="${FIRESTORE_DB}" \
    --location="${REGION}" \
    --type=firestore-native
fi

echo "==> 4/7 Creando cuentas de servicio de mínimo privilegio..."
API_SA="${API_SA_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_SA="${SCHED_SA_ID}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts describe "${API_SA}" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "${API_SA_ID}" \
    --display-name="Cymbal Bank — API Riesgo Financiero"

gcloud iam service-accounts describe "${SCHED_SA}" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "${SCHED_SA_ID}" \
    --display-name="Cymbal Bank — Cloud Scheduler FX"

for ROLE in roles/datastore.user roles/logging.logWriter roles/monitoring.metricWriter roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${API_SA}" \
    --role="${ROLE}" --quiet >/dev/null
done

API_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${API_SERVICE}:${TAG}"
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${WEB_SERVICE}:${TAG}"

echo "==> 5/7 Construyendo imágenes verificadas en Cloud Build..."
gcloud builds submit ./apps/api --tag "${API_IMAGE}"
gcloud builds submit ./apps/web --tag "${WEB_IMAGE}"

echo "==> 6/7 Desplegando servicios serverless en Google Cloud Run..."
if [[ "${MODE}" == "demo" ]]; then
  APP_ENV="staging"
  ALLOW_DEMO="true"
  API_AUTH_FLAG="--allow-unauthenticated"
  WEB_AUTH_FLAG="--allow-unauthenticated"
  INGRESS="all"
else
  APP_ENV="production"
  ALLOW_DEMO="false"
  API_AUTH_FLAG="--no-allow-unauthenticated"
  WEB_AUTH_FLAG="--no-allow-unauthenticated"
  INGRESS="internal-and-cloud-load-balancing"
fi

gcloud run deploy "${API_SERVICE}" \
  --image "${API_IMAGE}" \
  --region "${REGION}" \
  --service-account "${API_SA}" \
  --ingress "${INGRESS}" \
  --labels "${LABELS}" \
  ${API_AUTH_FLAG} \
  --set-env-vars "CYMBAL_APP_ENV=${APP_ENV},CYMBAL_STORAGE_BACKEND=firestore,CYMBAL_GCP_PROJECT_ID=${PROJECT_ID},CYMBAL_FIRESTORE_DATABASE=${FIRESTORE_DB},CYMBAL_FX_SECRET_NAME=${SECRET_NAME},CYMBAL_ALLOW_DEMO_HEADERS=${ALLOW_DEMO},CYMBAL_FX_PROVIDER_MODE=live,CYMBAL_SCHEDULER_SERVICE_ACCOUNT=${SCHED_SA},CYMBAL_OIDC_ISSUER=https://securetoken.google.com/${PROJECT_ID}"

API_URL="$(gcloud run services describe "${API_SERVICE}" --region "${REGION}" --format='value(status.url)')"

gcloud run deploy "${WEB_SERVICE}" \
  --image "${WEB_IMAGE}" \
  --region "${REGION}" \
  --ingress "${INGRESS}" \
  --labels "${LABELS}" \
  ${WEB_AUTH_FLAG} \
  --set-env-vars "API_INTERNAL_URL=${API_URL}"

WEB_URL="$(gcloud run services describe "${WEB_SERVICE}" --region "${REGION}" --format='value(status.url)')"

echo "==> 7/7 Configurando Cloud Scheduler + FX (${SCHEDULER_JOB})..."
gcloud run services add-iam-policy-binding "${API_SERVICE}" \
  --region "${REGION}" \
  --member="serviceAccount:${SCHED_SA}" \
  --role="roles/run.invoker" --quiet >/dev/null

if gcloud scheduler jobs describe "${SCHEDULER_JOB}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "${SCHEDULER_JOB}" \
    --location="${REGION}" \
    --schedule="0 * * * *" \
    --time-zone="UTC" \
    --uri="${API_URL}/api/v1/fx/refresh" \
    --http-method=POST \
    --oidc-service-account-email="${SCHED_SA}" \
    --oidc-token-audience="${PROJECT_ID}"
else
  gcloud scheduler jobs create http "${SCHEDULER_JOB}" \
    --location="${REGION}" \
    --schedule="0 * * * *" \
    --time-zone="UTC" \
    --uri="${API_URL}/api/v1/fx/refresh" \
    --http-method=POST \
    --oidc-service-account-email="${SCHED_SA}" \
    --oidc-token-audience="${PROJECT_ID}"
fi

echo ""
echo "=================================================================="
echo "Despliegue Multi-Demo completado en Google Cloud Run (${MODE})"
echo "  Firestore DB : ${FIRESTORE_DB} (aislada)"
echo "  Labels       : ${LABELS}"
echo "  API URL      : ${API_URL}"
echo "  WEB URL      : ${WEB_URL}"
echo "=================================================================="
if [[ "${MODE}" == "demo" ]]; then
  echo "Verificando /api/v1/health..."
  curl -fsS "${API_URL}/api/v1/health" && echo ""
fi
