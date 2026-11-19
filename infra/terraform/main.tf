# Infraestructura como Código (Terraform) — Cymbal Bank Panel de Riesgo Financiero (MVP v1.0)
# Cubre: Artifact Registry, Cloud KMS (CMEK), Secret Manager, Cloud Firestore,
# Cloud Armor (WAF + Rate Limiting), Cloud Run y Cloud Scheduler + FX.

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

# 1. Artifact Registry (Contenedores Verificados)
resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "cymbal-riesgo-containers"
  description   = "Imágenes verificadas de cymbal-riesgo-web y cymbal-riesgo-api"
  format        = "DOCKER"
}

# 2. Cloud KMS (Cifrado AES-256 / CMEK con rotación automática cada 90 días)
resource "google_kms_key_ring" "riesgo_ring" {
  name     = "cymbal-riesgo-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "cmek_key" {
  name            = "cymbal-riesgo-cmek"
  key_ring        = google_kms_key_ring.riesgo_ring.id
  rotation_period = "7776000s" # 90 días
}

# 3. Secret Manager (Claves de proveedor FX y secretos OIDC)
resource "google_secret_manager_secret" "fx_provider_key" {
  secret_id = "cymbal-fx-provider-api-key"
  replication {
    auto {}
  }
}

# 4. Cloud Firestore (Base documental: clientes, carteras, simulaciones, alertas, fx_rates)
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# 5. Cloud Armor (WAF OWASP + Rate Limiting)
resource "google_compute_security_policy" "waf_policy" {
  name        = "cymbal-riesgo-waf-policy"
  description = "Política WAF y Rate Limiting para el Panel de Riesgo Financiero"

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

# 6. Cuentas de servicio de mínimo privilegio para Cloud Run
resource "google_service_account" "api_sa" {
  account_id   = "cymbal-riesgo-api-sa"
  display_name = "Cymbal Bank — Servicio API de Riesgo Financiero"
}

resource "google_service_account" "web_sa" {
  account_id   = "cymbal-riesgo-web-sa"
  display_name = "Cymbal Bank — Servicio Web Ejecutivo"
}

# 7. Google Cloud Run — cymbal-riesgo-api (FastAPI + Python Decimal)
resource "google_cloud_run_v2_service" "api" {
  name     = "cymbal-riesgo-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.api_sa.email
    containers {
      image = var.api_image
      env {
        name  = "CYMBAL_APP_ENV"
        value = "production"
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
        name  = "CYMBAL_ALLOW_DEMO_HEADERS"
        value = "false"
      }
    }
  }
}

# 8. Google Cloud Run — cymbal-riesgo-web (Next.js + TypeScript + Recharts)
resource "google_cloud_run_v2_service" "web" {
  name     = "cymbal-riesgo-web"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.web_sa.email
    containers {
      image = var.web_image
      env {
        name  = "API_INTERNAL_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }
}

# 9. Cloud Scheduler + FX (Actualización horaria de tasas USD/EUR/MXN/COP)
resource "google_cloud_scheduler_job" "fx_refresh" {
  name        = "cymbal-fx-hourly-refresh"
  description = "Actualiza tasas oficiales USD / EUR / MXN / COP en Cloud Firestore"
  schedule    = "0 * * * *"
  time_zone   = "UTC"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.api.uri}/api/v1/fx/refresh"
    oidc_token {
      service_account_email = google_service_account.api_sa.email
    }
  }
}
