"""Pruebas unitarias del Motor de Riesgo Crediticio y Pruebas de Estrés (EL, NPL, PD, LGD)."""

from decimal import Decimal

from app.domain.models import CurrencyCode, RiskLevel, StressTestRequest, UserRole
from app.domain.stress_engine import (
    build_portfolio_summary,
    calculate_expected_loss,
    classify_client_risk,
    run_stress_simulation,
)
from app.repositories.seed_data import (
    build_initial_alerts,
    build_initial_clients,
    build_initial_fx_snapshot,
    build_monthly_history_usd,
)
from app.security.auth import DEMO_PROFILES


def test_expected_loss_exact_decimal_formula() -> None:
    # EL = 14,800,000.00 * 0.0560 * 0.4800 = 397,824.00
    el = calculate_expected_loss(
        ead=Decimal("14800000.00"),
        pd=Decimal("0.0560"),
        lgd=Decimal("0.4800"),
    )
    assert el == Decimal("397824.00")
    assert isinstance(el, Decimal)


def test_risk_classification_traffic_light_bands() -> None:
    assert classify_client_risk(Decimal("0.0150"), 0) == RiskLevel.BAJO
    assert classify_client_risk(Decimal("0.0450"), 10) == RiskLevel.MEDIO
    assert classify_client_risk(Decimal("0.0200"), 45) == RiskLevel.MEDIO
    assert classify_client_risk(Decimal("0.0900"), 0) == RiskLevel.ALTO
    assert classify_client_risk(Decimal("0.0200"), 95) == RiskLevel.ALTO


def test_portfolio_summary_consistency_across_currencies() -> None:
    clients = build_initial_clients()
    alerts = build_initial_alerts()
    history = build_monthly_history_usd()
    fx = build_initial_fx_snapshot()

    usd = build_portfolio_summary(clients, alerts, history, CurrencyCode.USD, fx)
    mxn = build_portfolio_summary(clients, alerts, history, CurrencyCode.MXN, fx)

    assert usd.total_clients == 12
    assert mxn.total_clients == 12
    # El ratio NPL y la tasa EL sobre EAD son invariantes a la moneda de reporte
    assert usd.npl_ratio_pct == mxn.npl_ratio_pct
    assert usd.el_rate_pct == mxn.el_rate_pct
    assert mxn.total_ead > usd.total_ead * Decimal("19.80")


def test_stress_simulation_increases_el_and_npl_under_adverse_shock() -> None:
    clients = build_initial_clients()
    fx = build_initial_fx_snapshot()
    analyst = DEMO_PROFILES[UserRole.RISK_ANALYST]

    req = StressTestRequest(
        name="Choque Severo Test",
        pd_shock_pct=Decimal("150.00"),
        lgd_shock_pp=Decimal("10.00"),
        fx_depreciation_latam_pct=Decimal("20.00"),
        reporting_currency=CurrencyCode.USD,
    )
    res = run_stress_simulation(req, clients, fx, analyst)

    assert res.stressed_el > res.base_el
    assert res.delta_el == res.stressed_el - res.base_el
    assert res.stressed_npl_pct >= res.base_npl_pct
    assert res.delta_npl_bps >= 0
    assert res.capital_buffer_impact_pct > Decimal("0.00")
    assert len(res.sector_impacts) > 0
