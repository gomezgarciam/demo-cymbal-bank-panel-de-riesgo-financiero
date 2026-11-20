#!/usr/bin/env bash
# Despliegue seguro e idempotente en Google Cloud Run + Firestore + Secret Manager + Cloud Scheduler.
# Uso en Google Cloud Shell:
#   ./infra/scripts/deploy_gcp.sh <TU_PROJECT_ID> [us-central1] [demo|enterprise]
#
# Seguridad: este script NO contiene ni escribe API keys ni credenciales en disco o Git.

set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${2:-us-central1}"
MODE="${3:-demo}"
REPO_NAME="cymbal-riesgo-containers"
TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: Debes indicar el PROJECT_ID de GCP."
  echo "Uso: ./infra/scripts/deploy_gcp.sh <TU_PROJECT_ID> [us-central1] [demo|enterprise]"
  exit 1
fi

if [[ "${MODE}" != "demo" && "${MODE}" != "enterprise" ]]; then
  echo "ERROR: Modo inválido '${MODE}'. Usa 'demo' o 'enterprise'."
  exit 1
fi

echo "==> Proyecto GCP: ${PROJECT_ID} | Región: ${REGION} | Modo: ${MODE} | Tag: ${TAG}"
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
    --description="Contenedores verificados de Cymbal Bank — Panel de Riesgo Financiero"
fi

echo "==> 3/7 Verificando base de datos Cloud Firestore (Native)..."
if ! gcloud firestore databases describe --database="(default)" >/dev/null 2>&1; then
  gcloud firestore databases create --location="${REGION}" --type=firestore-native
fi

echo "==> 4/7 Creando cuentas de servicio de mínimo privilegio..."
API_SA="cymbal-riesgo-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_SA="cymbal-fx-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts describe "${API_SA}" >/dev/null 2>&1 || \
  gcloud iam service-accounts create cymbal-riesgo-api-sa \
    --display-name="Cymbal Bank — API Riesgo Financiero"

gcloud iam service-accounts describe "${SCHED_SA}" >/dev/null 2>&1 || \
  gcloud iam service-accounts create cymbal-fx-scheduler-sa \
    --display-name="Cymbal Bank — Cloud Scheduler FX"

for ROLE in roles/datastore.user roles/logging.logWriter roles/monitoring.metricWriter roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${API_SA}" \
    --role="${ROLE}" --quiet >/dev/null
done

API_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cymbal-riesgo-api:${TAG}"
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cymbal-riesgo-web:${TAG}"

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

gcloud run deploy cymbal-riesgo-api \
  --image "${API_IMAGE}" \
  --region "${REGION}" \
  --service-account "${API_SA}" \
  --ingress "${INGRESS}" \
  ${API_AUTH_FLAG} \
  --set-env-vars "CYMBAL_APP_ENV=${APP_ENV},CYMBAL_STORAGE_BACKEND=firestore,CYMBAL_GCP_PROJECT_ID=${PROJECT_ID},CYMBAL_ALLOW_DEMO_HEADERS=${ALLOW_DEMO},CYMBAL_FX_PROVIDER_MODE=live,CYMBAL_SCHEDULER_SERVICE_ACCOUNT=${SCHED_SA},CYMBAL_OIDC_ISSUER=https://securetoken.google.com/${PROJECT_ID}"

API_URL="$(gcloud run services describe cymbal-riesgo-api --region "${REGION}" --format='value(status.url)')"

gcloud run deploy cymbal-riesgo-web \
  --image "${WEB_IMAGE}" \
  --region "${REGION}" \
  --ingress "${INGRESS}" \
  ${WEB_AUTH_FLAG} \
  --set-env-vars "API_INTERNAL_URL=${API_URL}"

WEB_URL="$(gcloud run services describe cymbal-riesgo-web --region "${REGION}" --format='value(status.url)')"

echo "==> 7/7 Configurando Cloud Scheduler + FX (actualización horaria)..."
gcloud run services add-iam-policy-binding cymbal-riesgo-api \
  --region "${REGION}" \
  --member="serviceAccount:${SCHED_SA}" \
  --role="roles/run.invoker" --quiet >/dev/null

if gcloud scheduler jobs describe cymbal-fx-hourly-refresh --location="${REGION}" >/dev/null 2>&1; then
  gcloud scheduler jobs update http cymbal-fx-hourly-refresh \
    --location="${REGION}" \
    --schedule="0 * * * *" \
    --time-zone="UTC" \
    --uri="${API_URL}/api/v1/fx/refresh" \
    --http-method=POST \
    --oidc-service-account-email="${SCHED_SA}" \
    --oidc-token-audience="${PROJECT_ID}"
else
  gcloud scheduler jobs create http cymbal-fx-hourly-refresh \
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
echo "Despliegue completado en Google Cloud Run (${MODE})"
echo "  API URL: ${API_URL}"
echo "  WEB URL: ${WEB_URL}"
echo "=================================================================="
if [[ "${MODE}" == "demo" ]]; then
  echo "Verificando /api/v1/health..."
  curl -fsS "${API_URL}/api/v1/health" && echo ""
fi
