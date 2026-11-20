"""Configuración centralizada de cymbal-riesgo-api (Local y Google Cloud Run)."""

from decimal import Decimal
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros de ejecución para entornos local y Google Cloud Run.

    NUNCA almacene API keys ni credenciales reales en este archivo ni en Git;
    en producción se obtienen dinámicamente desde Google Cloud Secret Manager.
    """

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

    # Seguridad e Identidad (Identity Platform OIDC + Cloud Scheduler)
    allow_demo_headers: bool = True
    oidc_issuer: str | None = None
    scheduler_service_account: str | None = None

    # Secret Manager y proveedor FX
    fx_secret_name: str = "cymbal-fx-provider-api-key"
    fx_provider_mode: Literal["deterministic", "live"] = "deterministic"
    fx_provider_url: str = "https://open.er-api.com/v6/latest/USD"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def effective_demo_headers_allowed(self) -> bool:
        """Guardia de seguridad: jamás permitir cabeceras demo en producción."""
        if self.app_env == "production":
            return False
        return self.allow_demo_headers


settings = Settings()
