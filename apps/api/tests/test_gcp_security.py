"""Pruebas de Fase 4: seguridad OIDC en producción, Secret Manager, FX Decimal y Firestore."""

from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from app.api.v1.routes import reset_repository_for_tests
from app.config import settings
from app.domain.fx_provider import parse_fx_payload_decimal
from app.domain.models import CurrencyCode, UserRole
from app.main import app
from app.observability.audit import clear_audit_events
from app.security.auth import _actor_from_claims
from app.security.secrets import SecretManagerProvider

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    clear_audit_events()
    reset_repository_for_tests()
    yield
    clear_audit_events()


def test_production_blocks_demo_headers_and_requires_oidc_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "allow_demo_headers", True)  # Guardia debe ignorarlo en producción

    assert settings.effective_demo_headers_allowed is False

    res = client.get(
        "/api/v1/portfolio/summary?currency=USD",
        headers={"X-Cymbal-Role": "risk_analyst"},
    )
    assert res.status_code == 401


def test_production_accepts_verified_oidc_jwt_and_enforces_rbac(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")

    cfo_claims = {
        "email": "elena.mendoza@cymbalbank.com",
        "name": "Elena Mendoza",
        "role": "cfo",
        "mfa": True,
    }
    with patch("app.security.auth.verify_oidc_jwt", return_value=cfo_claims):
        ok_res = client.get(
            "/api/v1/portfolio/summary?currency=EUR",
            headers={"Authorization": "Bearer verified-oidc-token"},
        )
        assert ok_res.status_code == 200
        assert ok_res.json()["reporting_currency"] == "EUR"

        denied_res = client.post(
            "/api/v1/fx/refresh",
            headers={"Authorization": "Bearer verified-oidc-token"},
        )
        assert denied_res.status_code == 403


def test_cloud_scheduler_service_account_can_trigger_fx_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(
        settings,
        "scheduler_service_account",
        "cymbal-fx-scheduler-sa@demo-proj.iam.gserviceaccount.com",
    )

    scheduler_claims = {
        "email": "cymbal-fx-scheduler-sa@demo-proj.iam.gserviceaccount.com",
        "iss": "https://accounts.google.com",
    }
    actor = _actor_from_claims(scheduler_claims, "gcp-cloud-scheduler-oidc")
    assert actor.role == UserRole.RISK_ANALYST

    with patch("app.security.auth.verify_oidc_jwt", return_value=scheduler_claims):
        res = client.post(
            "/api/v1/fx/refresh",
            headers={"Authorization": "Bearer scheduler-oidc-token"},
        )
        assert res.status_code == 200
        assert "rates" in res.json()


def test_parse_fx_payload_decimal_preserves_exact_precision() -> None:
    payload = '{"rates": {"USD": 1, "EUR": 0.9184567, "MXN": 19.7425, "COP": 4312.875}}'
    rates = parse_fx_payload_decimal(payload)
    assert isinstance(rates[CurrencyCode.EUR], Decimal)
    assert rates[CurrencyCode.EUR] == Decimal("0.918457")
    assert rates[CurrencyCode.MXN] == Decimal("19.742500")
    assert rates[CurrencyCode.COP] == Decimal("4312.875000")


def test_secret_provider_does_not_leak_values_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setenv("TEST_CYMBAL_SECRET", "super-secret-value-not-for-logs")
    provider = SecretManagerProvider(ttl_seconds=60)

    val = provider.get_secret("cymbal-fx-provider-api-key", local_env_var="TEST_CYMBAL_SECRET")
    assert val == "super-secret-value-not-for-logs"
    assert "super-secret-value-not-for-logs" not in repr(provider)
