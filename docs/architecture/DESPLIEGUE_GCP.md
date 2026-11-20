# Guía de Despliegue y Seguridad Bancaria en Google Cloud (Fase 4)

Este documento describe el procedimiento oficial para desplegar el **Panel de Riesgo Financiero de Cymbal Bank (MVP v1.0)** en Google Cloud Platform garantizando **cero secretos en Git**, cifrado **CMEK (AES-256)**, autenticación **Identity Platform (OIDC + MFA + RBAC)** y cumplimiento de **SLO `< 500 ms`**.

---

## 1. Política Estricta de Secretos (Cero Credenciales en GitHub)

El repositorio incluye controles automáticos para impedir filtraciones accidentales:

1. **`.gitignore` endurecido:** Bloquea `.env`, `.env.*` (excepto `.env.example`), `*.tfvars` (excepto `*.tfvars.example`), `*service-account*.json`, `*credentials*.json`, `*.pem` y `*.key`.
2. **Escáner automático en CI (`.github/workflows/ci-security.yml`):** Cada `push` y Pull Request ejecuta [`scripts/scan_secrets.py`](../../scripts/scan_secrets.py) antes de permitir pruebas o builds.
3. **Google Cloud Secret Manager:** Cualquier API key externa (por ejemplo, proveedor FX premium) se carga directamente en **Secret Manager** fuera de Git:

```bash
# Ejecutar únicamente en Google Cloud Shell (NUNCA guardar el valor en archivos del repo)
gcloud secrets create cymbal-fx-provider-api-key --replication-policy="automatic"
printf '%s' "PEGAR_CLAVE_AQUI" | gcloud secrets versions add cymbal-fx-provider-api-key --data-file=-
```

> **Guardia de producción en código:** Cuando `CYMBAL_APP_ENV=production`, [`apps/api/app/config.py`](../../apps/api/app/config.py) deshabilita automáticamente las cabeceras demo (`effective_demo_headers_allowed == False`) sin importar el valor de `CYMBAL_ALLOW_DEMO_HEADERS`, exigiendo obligatoriamente tokens JWT OIDC firmados por **Identity Platform**.

---

## 2. Opción A — Despliegue Rápido desde Google Cloud Shell (1 Comando)

Ideal para levantar el MVP en minutos con **Cloud Run + Cloud Firestore + Artifact Registry + Cloud Scheduler + FX**:

```bash
git clone https://github.com/gomezgarciam/demo-cymbal-bank-panel-de-riesgo-financiero.git
cd demo-cymbal-bank-panel-de-riesgo-financiero
chmod +x infra/scripts/deploy_gcp.sh

# Modo Demo (URL pública HTTPS en Cloud Run + Firestore + FX horario)
./infra/scripts/deploy_gcp.sh <TU_PROJECT_ID> us-central1 demo

# Modo Enterprise (ingress interno para Load Balancer + Cloud Armor + Identity Platform OIDC estricto)
./infra/scripts/deploy_gcp.sh <TU_PROJECT_ID> us-central1 enterprise
```

---

## 3. Opción B — Aprovisionamiento Declarativo con Terraform

Para entornos corporativos auditables que incluyen **Cloud KMS (CMEK)**, **Cloud Armor (WAF OWASP + Rate Limiting 120 rpm)**, **Cloud Monitoring (alerta SLO p95 > 500 ms)** y cuentas IAM de mínimo privilegio:

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edite terraform.tfvars localmente (ignorado por .gitignore) con su project_id e imágenes

terraform init
terraform plan
terraform apply
```

---

## 4. Configuración de Identity Platform (SSO OIDC + MFA + RBAC)

Para el modo `enterprise` (`CYMBAL_APP_ENV=production`):

1. Habilite **Identity Platform** en Google Cloud Console y configure el proveedor corporativo OIDC/SAML con **MFA obligatorio**.
2. Asigne el custom claim RBAC correspondiente a cada usuario corporativo:
   - `{"role": "cfo", "mfa": true}` — Acceso ejecutivo de lectura, KPIs, alertas y auditoría.
   - `{"role": "risk_analyst", "mfa": true}` — Permisos completos incluyendo `POST /api/v1/stress-tests`, `PATCH /api/v1/alerts/{id}` y `POST /api/v1/fx/refresh`.
3. `cymbal-riesgo-api` valida criptográficamente la firma RS256, expiración, audiencia (`aud == PROJECT_ID`) y emisor (`iss`) en [`apps/api/app/security/auth.py`](../../apps/api/app/security/auth.py).

---

## 5. Observabilidad y Auditoría Bancaria Inmutable

- **Cloud Logging (Filtro de Auditoría):**
  ```text
  jsonPayload.service="cymbal-riesgo-api" AND labels.audit_stream="banking-immutable"
  ```
  Configure un *Log Sink* hacia un bucket de Cloud Storage con política de retención bloqueada (*Bucket Lock / WORM*) para auditoría regulatoria.
- **Cloud Monitoring (SLO `< 500 ms`):**
  Terraform crea automáticamente la política `Cymbal Bank — Alerta SLO Latencia p95 > 500 ms (cymbal-riesgo-api)`.
