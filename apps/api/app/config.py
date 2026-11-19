"""Configuración centralizada de cymbal-riesgo-api."""

from decimal import Decimal
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros de ejecución para entornos local y Google Cloud Run."""

    model_config = SettingsConfigDict(
        env_prefix="CYMBAL_",
        env_file=".env",
        extra="ignore",
    )

    service_name: str = "cymbal-riesgo-api"
    service_version: str = "1.0.0"
    app_env: Literal["development", "staging", "production"] = "development"
    storage_backend: Literal["memory", "firestore"] = "memory"
    gcp_project_id: str = "cymbal-bank-riesgo-mvp"
    firestore_database: str = "(default)"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    slo_latency_target_ms: int = 500
    npl_appetite_limit_pct: Decimal = Decimal("3.50")
    el_rate_appetite_limit_pct: Decimal = Decimal("2.25")
    allow_demo_headers: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
