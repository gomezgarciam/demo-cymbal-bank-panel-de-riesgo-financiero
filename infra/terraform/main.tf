# Infraestructura como Código (Terraform) — Cymbal Bank Panel de Riesgo Financiero (MVP v1.0)
# Aislamiento Multi-Demo: base Firestore nombrada ('cymbal-riesgo-db'), prefijo 'cymbal-riesgo-*'
# y etiquetas de facturación 'demo=cymbal-riesgo' sin almacenar ningún secreto en Git.

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  demo_labels = {
    demo       = "cymbal-riesgo"
    app        = "panel-riesgo-financiero"
    managed_by = "terraform"
  }

  required_apis = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudscheduler.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "identitytoolkit.googleapis.com",
  ])
}

# 0. Habilitación declarativa de APIs de Google Cloud
resource "google_project_service" "enabled_apis" {
  for_each           = local.required_apis
  service            = each.value
  disable_on_destroy = false
}

# 1. Artifact Registry (Contenedores Verificados)
resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "cymbal-riesgo-containers"
  description   = "Imágenes verificadas de cymbal-riesgo-web y cymbal-riesgo-api"
  format        = "DOCKER"
  labels        = local.demo_labels
  depends_on    = [google_project_service.enabled_apis]
}

# 2. Cloud KMS (Cifrado AES-256 / CMEK con rotación automática cada 90 días)
resource "google_kms_key_ring" "riesgo_ring" {
  name       = "cymbal-riesgo-keyring"
  location   = var.region
  depends_on = [google_project_service.enabled_apis]
}

resource "google_kms_crypto_key" "cmek_key" {
  name            = "cymbal-riesgo-cmek"
  key_ring        = google_kms_key_ring.riesgo_ring.id
  rotation_period = "7776000s" # 90 días
  labels          = local.demo_labels
}

# 3. Secret Manager (Contenedor del secreto; el valor se carga fuera de banda con gcloud)
resource "google_secret_manager_secret" "fx_provider_key" {
  secret_id = "cymbal-riesgo-fx-api-key"
  labels    = local.demo_labels
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled_apis]
}

# 4. Cloud Firestore (Base documental nombrada aislada por demo)
resource "google_firestore_database" "cymbal_db" {
  name        = var.firestore_database_name
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.enabled_apis]
}

# 5. Cloud Armor (WAF OWASP SQLi/XSS + Rate Limiting)
resource "google_compute_security_policy" "waf_policy" {
  name        = "cymbal-riesgo-waf-policy"
  description = "Política WAF OWASP y Rate Limiting para el Panel de Riesgo Financiero"
  depends_on  = [google_project_service.enabled_apis]

  rule {
    action   = "deny(403)"
    priority = 900
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('sqli-v33-stable') || evaluatePreconfiguredWaf('xss-v33-stable')"
      }
    }
    description = "Bloquear ataques OWASP SQLi y XSS"
  }

  rule {
    action   = "throttle"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 120
        interval_sec = 60
      }
    }
    description = "Rate Limiting: máximo 120 peticiones por minuto por IP"
  }

  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Regla por defecto"
  }
}

# 6. Cuentas de servicio de mínimo privilegio (IAM)
resource "google_service_account" "api_sa" {
  account_id   = "cymbal-riesgo-api-sa"
  display_name = "Cymbal Bank — Servicio API de Riesgo Financiero"
}

resource "google_service_account" "web_sa" {
  account_id   = "cymbal-riesgo-web-sa"
  display_name = "Cymbal Bank — Servicio Web Ejecutivo"
}

resource "google_service_account" "scheduler_sa" {
  account_id   = "cymbal-riesgo-scheduler-sa"
  display_name = "Cymbal Bank — Cloud Scheduler FX OIDC"
}

resource "google_project_iam_member" "api_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "api_secret_accessor" {
  secret_id = google_secret_manager_secret.fx_provider_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
}

# 7. Google Cloud Run — cymbal-riesgo-api (FastAPI + Python Decimal)
resource "google_cloud_run_v2_service" "api" {
  name       = "cymbal-riesgo-api"
  location   = var.region
  ingress    = var.demo_public_mode ? "INGRESS_TRAFFIC_ALL" : "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  labels     = local.demo_labels
  depends_on = [google_project_service.enabled_apis, google_firestore_database.cymbal_db]

  template {
    service_account = google_service_account.api_sa.email
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = var.api_image
      env {
        name  = "CYMBAL_APP_ENV"
        value = var.demo_public_mode ? "staging" : "production"
      }
      env {
        name  = "CYMBAL_STORAGE_BACKEND"
        value = "firestore"
      }
      env {
        name  = "CYMBAL_GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "CYMBAL_FIRESTORE_DATABASE"
        value = google_firestore_database.cymbal_db.name
      }
      env {
        name  = "CYMBAL_FX_SECRET_NAME"
        value = google_secret_manager_secret.fx_provider_key.secret_id
      }
      env {
        name  = "CYMBAL_ALLOW_DEMO_HEADERS"
        value = var.demo_public_mode ? "true" : "false"
      }
      env {
        name  = "CYMBAL_FX_PROVIDER_MODE"
        value = var.fx_provider_mode
      }
      env {
        name  = "CYMBAL_SCHEDULER_SERVICE_ACCOUNT"
        value = google_service_account.scheduler_sa.email
      }
      env {
        name  = "CYMBAL_OIDC_ISSUER"
        value = "https://securetoken.google.com/${var.project_id}"
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_invokes_api" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_cloud_run_v2_service_iam_member" "web_invokes_api" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.web_sa.email}"
}

# 8. Google Cloud Run — cymbal-riesgo-web (Next.js + TypeScript + Recharts)
resource "google_cloud_run_v2_service" "web" {
  name       = "cymbal-riesgo-web"
  location   = var.region
  ingress    = var.demo_public_mode ? "INGRESS_TRAFFIC_ALL" : "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  labels     = local.demo_labels
  depends_on = [google_cloud_run_v2_service.api]

  template {
    service_account = google_service_account.web_sa.email
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = var.web_image
      env {
        name  = "API_INTERNAL_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "web_public_demo" {
  count    = var.demo_public_mode ? 1 : 0
  name     = google_cloud_run_v2_service.web.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 9. Cloud Scheduler + FX (Actualización horaria de tasas USD/EUR/MXN/COP con OIDC)
resource "google_cloud_scheduler_job" "fx_refresh" {
  name        = "cymbal-riesgo-fx-hourly"
  description = "Actualiza tasas oficiales USD / EUR / MXN / COP en Cloud Firestore (cymbal-riesgo-db)"
  schedule    = "0 * * * *"
  time_zone   = "UTC"
  depends_on  = [google_cloud_run_v2_service.api]

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.api.uri}/api/v1/fx/refresh"
    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
      audience              = var.project_id
    }
  }
}

# 10. Cloud Monitoring — Alerta de cumplimiento SLO Latencia p95 < 500 ms
resource "google_monitoring_alert_policy" "slo_latency_alert" {
  display_name = "Cymbal Bank — Alerta SLO Latencia p95 > 500 ms (cymbal-riesgo-api)"
  combiner     = "OR"
  depends_on   = [google_project_service.enabled_apis]

  conditions {
    display_name = "Latencia p95 Cloud Run > 500 ms"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"cymbal-riesgo-api\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "120s"
      comparison      = "COMPARISON_GT"
      threshold_value = 500
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }
}
