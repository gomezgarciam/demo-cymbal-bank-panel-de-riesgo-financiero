variable "project_id" {
  description = "ID del proyecto de Google Cloud para Cymbal Bank — Panel de Riesgo Financiero."
  type        = string
}

variable "region" {
  description = "Región principal de despliegue en Google Cloud."
  type        = string
  default     = "us-central1"
}

variable "firestore_database_name" {
  description = "Nombre de la base de datos Firestore dedicada a esta demo (evita colisiones con '(default)' en proyectos compartidos)."
  type        = string
  default     = "cymbal-riesgo-db"
}

variable "api_image" {
  description = "URL completa en Artifact Registry de la imagen de cymbal-riesgo-api."
  type        = string
}

variable "web_image" {
  description = "URL completa en Artifact Registry de la imagen de cymbal-riesgo-web."
  type        = string
}

variable "demo_public_mode" {
  description = "Si es true, expone cymbal-riesgo-web públicamente en Cloud Run para demo; en producción usar false con Cloud Load Balancing + Cloud Armor."
  type        = bool
  default     = false
}

variable "fx_provider_mode" {
  description = "Modo del proveedor FX: 'deterministic' o 'live'."
  type        = string
  default     = "live"
}
