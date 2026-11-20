"""Pruebas de integración de /api/v1, RBAC (CFO vs Analista), auditoría JSON y SLO."""

from fastapi.testclient import TestClient
import pytest

from app.api.v1.routes import reset_repository_for_tests
from app.main import app
from app.observability.audit import clear_audit_events


@pytest.fixture(autouse=True)
def clean_state() -> None:
    clear_audit_events()
    reset_repository_for_tests()


client = TestClient(app)


def test_health_and_slo_headers() -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["slo_latency_target_ms"] == 500
    assert "X-Response-Time-Ms" in res.headers
    assert float(res.headers["X-Response-Time-Ms"]) < 500.0


def test_portfolio_summary_multicurrency() -> None:
    for cur in ("USD", "EUR", "MXN", "COP"):
        res = client.get(
            f"/api/v1/portfolio/summary?currency={cur}",
            headers={"X-Cymbal-Role": "cfo"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["reporting_currency"] == cur
        assert data["total_clients"] == 12
        assert len(data["sector_exposures"]) >= 5
        assert len(data["monthly_trend"]) == 6


def test_rbac_denies_cfo_write_operations_and_logs_audit() -> None:
    cfo_headers = {"X-Cymbal-Role": "cfo", "X-Cymbal-User": "cfo@cymbalbank.com"}

    res_sim = client.post(
        "/api/v1/stress-tests",
        headers=cfo_headers,
        json={
            "name": "Intento no autorizado CFO",
            "pd_shock_pct": "40.00",
            "lgd_shock_pp": "5.00",
            "fx_depreciation_latam_pct": "10.00",
            "reporting_currency": "USD",
        },
    )
    assert res_sim.status_code == 403

    res_alert = client.patch(
        "/api/v1/alerts/ALT-2026-001",
        headers=cfo_headers,
        json={"status": "MITIGADA"},
    )
    assert res_alert.status_code == 403

    audit_res = client.get("/api/v1/audit/events", headers=cfo_headers)
    assert audit_res.status_code == 200
    actions = [ev["action"] for ev in audit_res.json()]
    assert "RBAC_ACCESS_DENIED" in actions


def test_risk_analyst_can_run_stress_test_and_update_alert() -> None:
    analyst_headers = {
        "X-Cymbal-Role": "risk_analyst",
        "X-Cymbal-User": "carlos.navarro@cymbalbank.com",
    }

    sim_res = client.post(
        "/api/v1/stress-tests",
        headers=analyst_headers,
        json={
            "name": "Prueba Comité Riesgo 4T",
            "pd_shock_pct": "50.00",
            "lgd_shock_pp": "6.00",
            "fx_depreciation_latam_pct": "15.00",
            "reporting_currency": "COP",
        },
    )
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    assert sim_data["reporting_currency"] == "COP"
    assert sim_data["executed_by"] == "carlos.navarro@cymbalbank.com"

    # Verificar persistencia en listado histórico
    list_res = client.get("/api/v1/stress-tests", headers=analyst_headers)
    assert list_res.status_code == 200
    ids = [s["simulation_id"] for s in list_res.json()]
    assert sim_data["simulation_id"] in ids

    # Actualizar alerta de morosidad
    patch_res = client.patch(
        "/api/v1/alerts/ALT-2026-001?currency=COP",
        headers=analyst_headers,
        json={"status": "EN_REVISION", "analyst_note": "Comité programado lunes 09:00."},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "EN_REVISION"
    assert patch_res.json()["reporting_currency"] == "COP"
