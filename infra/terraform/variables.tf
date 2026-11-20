variable "project_id" {
  description = "ID del proyecto de Google Cloud para Cymbal Bank — Panel de Riesgo Financiero."
  type        = string
}

variable "region" {
  description = "Región principal de despliegue en Google Cloud."
  type        = string
  default     = "us-central1"
}

variable "api_image" {
  description = "URL completa en Artifact Registry de la imagen de cymbal-riesgo-api."
  type        = string
}

variable "web_image" {
  description = "URL completa en Artifact Registry de la imagen de cymbal-riesgo-web."
  type        = string
}
