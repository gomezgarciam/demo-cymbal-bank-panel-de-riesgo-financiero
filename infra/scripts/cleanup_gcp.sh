#!/usr/bin/env bash
# Limpieza aislada Multi-Demo en Google Cloud Platform.
# Elimina ÚNICAMENTE los recursos de la demo Cymbal Bank (prefijo 'cymbal-riesgo-*' y DB 'cymbal-riesgo-db')
# sin afectar '(default)' ni otras demos que convivan en el mismo proyecto.
#
# Uso en Google Cloud Shell:
#   ./infra/scripts/cleanup_gcp.sh <TU_PROJECT_ID> [us-central1] [--yes]

set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${2:-us-central1}"
AUTO_APPROVE="${3:-}"

DEMO_PREFIX="cymbal-riesgo"
REPO_NAME="${DEMO_PREFIX}-containers"
FIRESTORE_DB="${DEMO_PREFIX}-db"
API_SERVICE="${DEMO_PREFIX}-api"
WEB_SERVICE="${DEMO_PREFIX}-web"
SCHEDULER_JOB="${DEMO_PREFIX}-fx-hourly"
API_SA="${DEMO_PREFIX}-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_SA="${DEMO_PREFIX}-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: Debes indicar el PROJECT_ID de GCP."
  echo "Uso: ./infra/scripts/cleanup_gcp.sh <TU_PROJECT_ID> [us-central1] [--yes]"
  exit 1
fi

echo "Se eliminarán ÚNICAMENTE los recursos de la demo '${DEMO_PREFIX}' en '${PROJECT_ID}' (${REGION}):"
echo "  - Cloud Run         : ${WEB_SERVICE}, ${API_SERVICE}"
echo "  - Cloud Scheduler   : ${SCHEDULER_JOB}"
echo "  - Firestore DB      : ${FIRESTORE_DB} (NO afecta a '(default)')"
echo "  - Artifact Registry : ${REPO_NAME}"
echo "  - Service Accounts  : ${API_SA}, ${SCHED_SA}"
echo ""

if [[ "${AUTO_APPROVE}" != "--yes" ]]; then
  read -r -p "¿Confirmas la eliminación de estos recursos? Escribe 'SI' para continuar: " CONFIRM
  if [[ "${CONFIRM}" != "SI" ]]; then
    echo "Operación cancelada. No se eliminó ningún recurso."
    exit 0
  fi
fi

gcloud config set project "${PROJECT_ID}" >/dev/null

echo "==> Eliminando Cloud Scheduler (${SCHEDULER_JOB})..."
gcloud scheduler jobs delete "${SCHEDULER_JOB}" --location="${REGION}" --quiet 2>/dev/null || true

echo "==> Eliminando servicios Cloud Run (${WEB_SERVICE}, ${API_SERVICE})..."
gcloud run services delete "${WEB_SERVICE}" --region="${REGION}" --quiet 2>/dev/null || true
gcloud run services delete "${API_SERVICE}" --region="${REGION}" --quiet 2>/dev/null || true

echo "==> Eliminando base Firestore nombrada (${FIRESTORE_DB})..."
gcloud firestore databases delete --database="${FIRESTORE_DB}" --quiet 2>/dev/null || true

echo "==> Eliminando repositorio Artifact Registry (${REPO_NAME})..."
gcloud artifacts repositories delete "${REPO_NAME}" --location="${REGION}" --quiet 2>/dev/null || true

echo "==> Eliminando Service Accounts dedicadas..."
gcloud iam service-accounts delete "${API_SA}" --quiet 2>/dev/null || true
gcloud iam service-accounts delete "${SCHED_SA}" --quiet 2>/dev/null || true

echo "Limpieza completada. Las demás demos del proyecto permanecen intactas."
