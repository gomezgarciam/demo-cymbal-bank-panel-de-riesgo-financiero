output "artifact_registry_repository" {
  description = "Ruta del repositorio Docker en Artifact Registry."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}"
}

output "firestore_database_name" {
  description = "Base de datos Cloud Firestore aislada para esta demo."
  value       = google_firestore_database.cymbal_db.name
}

output "api_service_url" {
  description = "URL del servicio Cloud Run cymbal-riesgo-api."
  value       = google_cloud_run_v2_service.api.uri
}

output "web_service_url" {
  description = "URL del servicio Cloud Run cymbal-riesgo-web."
  value       = google_cloud_run_v2_service.web.uri
}

output "kms_cmek_key_id" {
  description = "Identificador de la clave CMEK AES-256 en Cloud KMS."
  value       = google_kms_crypto_key.cmek_key.id
}

output "fx_scheduler_job" {
  description = "Nombre del job programado de tasas FX en Cloud Scheduler."
  value       = google_cloud_scheduler_job.fx_refresh.name
}
