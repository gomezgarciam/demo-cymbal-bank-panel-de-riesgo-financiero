"""Modelos de dominio financiero con aritmética exacta basada en Decimal."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    MXN = "MXN"
    COP = "COP"


class UserRole(str, Enum):
    CFO = "cfo"
    RISK_ANALYST = "risk_analyst"


class RiskLevel(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


class AlertStatus(str, Enum):
    ABIERTA = "ABIERTA"
    EN_REVISION = "EN_REVISION"
    MITIGADA = "MITIGADA"


class StrictDecimalModel(BaseModel):
    """Base Pydantic que garantiza serialización exacta de valores Decimal como cadenas."""

    model_config = ConfigDict(
        ser_json_inf_nan="null",
        populate_by_name=True,
    )


class ActorIdentity(StrictDecimalModel):
    email: str
    full_name: str
    role: UserRole
    auth_provider: str = "identity-platform-oidc"
    mfa_verified: bool = True


class FxRatesSnapshot(StrictDecimalModel):
    base_currency: CurrencyCode = CurrencyCode.USD
    rates: dict[CurrencyCode, Decimal]
    as_of_utc: datetime
    source: str = "Cloud Scheduler + FX (Referencia Bancaria Cymbal)"


class ClientPortfolioRecord(StrictDecimalModel):
    """Registro canónico en Firestore (colecciones clientes + carteras)."""

    client_id: str
    name: str
    country: str
    sector: str
    credit_rating: str
    facility_type: str
    origin_currency: CurrencyCode
    ead_origin: Decimal
    pd: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    lgd: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    days_past_due: int = Field(ge=0)
    maturity_date: date
    last_review_date: date


class ClientPortfolioView(StrictDecimalModel):
    """Proyección del cliente en la moneda de reporte seleccionada."""

    client_id: str
    name: str
    country: str
    sector: str
    credit_rating: str
    facility_type: str
    origin_currency: CurrencyCode
    reporting_currency: CurrencyCode
    fx_rate_applied: Decimal
    ead_origin: Decimal
    ead: Decimal
    pd_pct: Decimal
    lgd_pct: Decimal
    expected_loss: Decimal
    el_rate_pct: Decimal
    days_past_due: int
    is_npl: bool
    risk_level: RiskLevel
    maturity_date: date
    last_review_date: date


class SectorExposure(StrictDecimalModel):
    sector: str
    client_count: int
    ead: Decimal
    expected_loss: Decimal
    el_rate_pct: Decimal
    npl_ratio_pct: Decimal
    share_of_portfolio_pct: Decimal
    risk_level: RiskLevel


class CurrencyBreakdown(StrictDecimalModel):
    origin_currency: CurrencyCode
    ead_in_reporting: Decimal
    share_pct: Decimal
    client_count: int


class MonthlyRiskPoint(StrictDecimalModel):
    period: str
    ead: Decimal
    expected_loss: Decimal
    npl_ratio_pct: Decimal
    el_rate_pct: Decimal


class ExecutiveInsight(StrictDecimalModel):
    headline: str
    summary: str
    recommendation: str
    overall_status: RiskLevel
    npl_variance_bps: int
    el_variance_bps: int


class PortfolioSummaryResponse(StrictDecimalModel):
    reporting_currency: CurrencyCode
    as_of_utc: datetime
    fx_snapshot: FxRatesSnapshot
    total_clients: int
    total_ead: Decimal
    total_expected_loss: Decimal
    el_rate_pct: Decimal
    el_appetite_limit_pct: Decimal
    npl_ead: Decimal
    npl_ratio_pct: Decimal
    npl_appetite_limit_pct: Decimal
    weighted_pd_pct: Decimal
    weighted_lgd_pct: Decimal
    risk_distribution: dict[RiskLevel, int]
    alerts_summary: dict[RiskLevel, int]
    open_alerts_total: int
    sector_exposures: list[SectorExposure]
    currency_breakdown: list[CurrencyBreakdown]
    monthly_trend: list[MonthlyRiskPoint]
    executive_insight: ExecutiveInsight


class StressTestRequest(StrictDecimalModel):
    name: str = Field(min_length=3, max_length=120)
    pd_shock_pct: Decimal = Field(
        default=Decimal("35.00"),
        ge=Decimal("-50.00"),
        le=Decimal("300.00"),
        description="Variación porcentual multiplicativa sobre PD (ej. 35 = +35%).",
    )
    lgd_shock_pp: Decimal = Field(
        default=Decimal("5.00"),
        ge=Decimal("-20.00"),
        le=Decimal("45.00"),
        description="Incremento aditivo en puntos porcentuales sobre LGD (ej. 5 = +5 pp).",
    )
    fx_depreciation_latam_pct: Decimal = Field(
        default=Decimal("12.00"),
        ge=Decimal("-25.00"),
        le=Decimal("60.00"),
        description="Depreciación de monedas LATAM (MXN, COP) frente a USD (%).",
    )
    sector_filter: str | None = Field(
        default=None,
        description="Si se especifica, concentra el choque exclusivamente en ese sector.",
    )
    reporting_currency: CurrencyCode = CurrencyCode.USD
    notes: str | None = Field(default=None, max_length=400)


class SectorStressImpact(StrictDecimalModel):
    sector: str
    base_el: Decimal
    stressed_el: Decimal
    delta_el: Decimal
    delta_el_pct: Decimal
    stressed_npl_pct: Decimal
    risk_level: RiskLevel


class StressTestRecord(StrictDecimalModel):
    """Simulación persistida en Firestore (colección simulaciones)."""

    simulation_id: str
    name: str
    created_at_utc: datetime
    executed_by: str
    executed_role: UserRole
    reporting_currency: CurrencyCode
    sector_filter: str | None
    notes: str | None
    pd_shock_pct: Decimal
    lgd_shock_pp: Decimal
    fx_depreciation_latam_pct: Decimal
    fx_snapshot_base: FxRatesSnapshot
    fx_snapshot_stressed: FxRatesSnapshot
    base_ead: Decimal
    stressed_ead: Decimal
    base_el: Decimal
    stressed_el: Decimal
    delta_el: Decimal
    delta_el_pct: Decimal
    base_el_rate_pct: Decimal
    stressed_el_rate_pct: Decimal
    base_npl_pct: Decimal
    stressed_npl_pct: Decimal
    delta_npl_bps: int
    capital_buffer_impact_pct: Decimal
    stressed_risk_level: RiskLevel
    sector_impacts: list[SectorStressImpact]
    executive_conclusion: str


class AlertRecord(StrictDecimalModel):
    """Alerta persistida en Firestore (colección alertas)."""

    alert_id: str
    client_id: str
    client_name: str
    sector: str
    category: str
    title: str
    description: str
    recommendation: str
    severity: RiskLevel
    status: AlertStatus
    origin_currency: CurrencyCode
    exposure_origin: Decimal
    threshold_breach_bps: int
    days_past_due: int
    created_at_utc: datetime
    updated_at_utc: datetime
    updated_by: str


class AlertView(AlertRecord):
    reporting_currency: CurrencyCode
    exposure_reporting: Decimal
    fx_rate_applied: Decimal


class AlertUpdateRequest(StrictDecimalModel):
    status: AlertStatus
    analyst_note: str | None = Field(default=None, max_length=300)


class AuditEvent(StrictDecimalModel):
    event_id: str
    timestamp_utc: datetime
    severity: str
    service: str
    action: str
    actor_email: str
    actor_role: str
    http_method: str
    path: str
    status_code: int
    latency_ms: Decimal
    currency: str | None = None
    resource_id: str | None = None
    outcome: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(StrictDecimalModel):
    status: str
    service: str
    version: str
    storage_backend: str
    slo_latency_target_ms: int
    supported_currencies: list[CurrencyCode]
    timestamp_utc: datetime
