"""Adaptador seguro para Google Cloud Secret Manager (cero secretos en Git)."""

from __future__ import annotations

import os
import time
from threading import Lock

from app.config import settings


class SecretManagerProvider:
    """Recupera secretos desde Google Cloud Secret Manager con caché en memoria con TTL.

    Las credenciales nunca se imprimen, serializan ni registran en logs de auditoría.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._cache: dict[str, tuple[str | None, float]] = {}

    def get_secret(self, secret_name: str, local_env_var: str | None = None) -> str | None:
        """Obtiene el valor del secreto desde Secret Manager (GCP) o variable local en dev."""
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(secret_name)
            if cached and cached[1] > now:
                return cached[0]

        value = self._fetch_value(secret_name, local_env_var)

        with self._lock:
            self._cache[secret_name] = (value, now + self._ttl_seconds)
        return value

    def _fetch_value(self, secret_name: str, local_env_var: str | None) -> str | None:
        if settings.app_env == "development":
            if local_env_var:
                return os.getenv(local_env_var)
            return None

        try:
            from google.cloud import secretmanager  # type: ignore

            client = secretmanager.SecretManagerServiceClient()
            resource = (
                f"projects/{settings.gcp_project_id}/secrets/{secret_name}/versions/latest"
            )
            response = client.access_secret_version(request={"name": resource})
            return response.payload.data.decode("utf-8").strip()
        except Exception:
            return None

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def __repr__(self) -> str:
        return f"SecretManagerProvider(cached_keys={len(self._cache)}, ttl={self._ttl_seconds}s)"


secret_provider = SecretManagerProvider()
