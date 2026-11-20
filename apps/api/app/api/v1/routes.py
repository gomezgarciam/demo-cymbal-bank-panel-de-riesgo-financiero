"""Rutas REST versionadas /api/v1 de cymbal-riesgo-api."""

from datetime import datetime, timezone
from decimal import Decimal
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.config import settings
from app.domain.fx import convert_amount
from app.domain.fx_provider import fetch_latest_fx_snapshot
from app.domain.models import (
    ActorIdentity,
    AlertStatus,
    AlertUpdateRequest,
    AlertView,
    AuditEvent,
    ClientPortfolioView,
    CurrencyCode,
    FxRatesSnapshot,
    HealthResponse,
    PortfolioSummaryResponse,
    RiskLevel,
    StressTestRecord,
    StressTestRequest,
    UserRole,
)
from app.domain.stress_engine import (
    build_portfolio_summary,
    project_client,
    run_stress_simulation,
)
from app.observability.audit import list_recent_audit_events, record_audit_event
from app.repositories.base import RiskRepository
from app.repositories.firestore_repo import FirestoreRiskRepository
from app.repositories.memory_repo import InMemoryRiskRepository
from app.security.auth import get_current_actor, require_roles

router = APIRouter(prefix="/api/v1", tags=["Cymbal Bank Risk API v1"])

_repository_singleton: RiskRepository | None = None


def get_repository() -> RiskRepository:
    global _repository_singleton
    if _repository_singleton is None:
        if settings.storage_backend == "firestore":
            _repository_singleton = FirestoreRiskRepository()
        else:
            _repository_singleton = InMemoryRiskRepository()
    return _repository_singleton


def reset_repository_for_tests() -> None:
    """Reinicia el singleton de repositorio para aislamiento en pytest."""
    global _repository_singleton
    _repository_singleton = InMemoryRiskRepository()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        storage_backend=settings.storage_backend,
        slo_latency_target_ms=settings.slo_latency_target_ms,
        supported_currencies=list(CurrencyCode),
        timestamp_utc=datetime.now(timezone.utc),
    )


@router.get("/portfolio/summary", response_model=PortfolioSummaryResponse)
def get_portfolio_summary(
    request: Request,
    currency: CurrencyCode = Query(default=CurrencyCode.USD),
    actor: ActorIdentity = Depends(get_current_actor),
    repo: RiskRepository = Depends(get_repository),
) -> PortfolioSummaryResponse:
    start = time.perf_counter()
    summary = build_portfolio_summary(
        records=repo.list_clients(),
        alerts=repo.list_alerts(),
        monthly_history_usd=repo.get_monthly_history_usd(),
        reporting_currency=currency,
        fx_snapshot=repo.get_fx_snapshot(),
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_audit_event(
        action="PORTFOLIO_SUMMARY_READ",
        actor=actor,
        http_method=request.method,
        path=request.url.path,
        status_code=status.HTTP_200_OK,
        latency_ms=elapsed_ms,
        currency=currency.value,
        details={
            "total_ead": str(summary.total_ead),
            "total_expected_loss": str(summary.total_expected_loss),
            "npl_ratio_pct": str(summary.npl_ratio_pct),
        },
    )
    return summary


@router.get("/clients", response_model=list[ClientPortfolioView])
def list_clients(
    request: Request,
    currency: CurrencyCode = Query(default=CurrencyCode.USD),
    sector: str | None = Query(default=None),
    risk_level: RiskLevel | None = Query(default=None),
    origin_currency: CurrencyCode | None = Query(default=None),
    search: str | None = Query(default=None),
    actor: ActorIdentity = Depends(get_current_actor),
    repo: RiskRepository = Depends(get_repository),
) -> list[ClientPortfolioView]:
    start = time.perf_counter()
    fx = repo.get_fx_snapshot()
    views = [project_client(r, currency, fx) for r in repo.list_clients()]

    if sector:
        views = [v for v in views if v.sector.lower() == sector.strip().lower()]
    if risk_level:
        views = [v for v in views if v.risk_level == risk_level]
    if origin_currency:
        views = [v for v in views if v.origin_currency == origin_currency]
    if search:
        needle = search.strip().lower()
        views = [
            v
            for v in views
            if needle in v.name.lower()
            or needle in v.client_id.lower()
            or needle in v.country.lower()
            or needle in v.sector.lower()
        ]

    views.sort(key=lambda v: v.expected_loss, reverse=True)
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_audit_event(
        action="CLIENTS_PORTFOLIO_READ",
        actor=actor,
        http_method=request.method,
        path=request.url.path,
        status_code=status.HTTP_200_OK,
        latency_ms=elapsed_ms,
        currency=currency.value,
        details={"returned_count": len(views), "sector": sector, "risk_level": risk_level.value if risk_level else None},
    )
    return views


@router.get("/fx/rates", response_model=FxRatesSnapshot)
def get_fx_rates(
    repo: RiskRepository = Depends(get_repository),
) -> FxRatesSnapshot:
    return repo.get_fx_snapshot()


@router.post("/fx/refresh", response_model=FxRatesSnapshot)
def refresh_fx_rates(
    request: Request,
    actor: ActorIdentity = Depends(require_roles(UserRole.RISK_ANALYST)),
    repo: RiskRepository = Depends(get_repository),
) -> FxRatesSnapshot:
    """Ejecuta el job Cloud Scheduler + FX (modo live con Secret Manager o determinístico local)."""
    start = time.perf_counter()
    current = repo.get_fx_snapshot()
    updated = fetch_latest_fx_snapshot(current)
    saved = repo.save_fx_snapshot(updated)
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_audit_event(
        action="FX_RATES_REFRESHED",
        actor=actor,
        http_method=request.method,
        path=request.url.path,
        status_code=status.HTTP_200_OK,
        latency_ms=elapsed_ms,
        details={"rates": {k.value: str(v) for k, v in saved.rates.items()}},
    )
    return saved


@router.get("/stress-tests", response_model=list[StressTestRecord])
def list_stress_tests(
    repo: RiskRepository = Depends(get_repository),
) -> list[StressTestRecord]:
    return repo.list_stress_tests()


@router.post(
    "/stress-tests",
    response_model=StressTestRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_stress_test(
    payload: StressTestRequest,
    request: Request,
    actor: ActorIdentity = Depends(require_roles(UserRole.RISK_ANALYST)),
    repo: RiskRepository = Depends(get_repository),
) -> StressTestRecord:
    start = time.perf_counter()
    result = run_stress_simulation(
        request=payload,
        records=repo.list_clients(),
        fx_snapshot=repo.get_fx_snapshot(),
        actor=actor,
    )
    saved = repo.save_stress_test(result)
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_audit_event(
        action="STRESS_TEST_EXECUTED",
        actor=actor,
        http_method=request.method,
        path=request.url.path,
        status_code=status.HTTP_201_CREATED,
        latency_ms=elapsed_ms,
        currency=payload.reporting_currency.value,
        resource_id=saved.simulation_id,
        details={
            "scenario_name": saved.name,
            "pd_shock_pct": str(saved.pd_shock_pct),
            "lgd_shock_pp": str(saved.lgd_shock_pp),
            "fx_depreciation_latam_pct": str(saved.fx_depreciation_latam_pct),
            "delta_el": str(saved.delta_el),
            "stressed_npl_pct": str(saved.stressed_npl_pct),
        },
    )
    return saved


@router.get("/alerts", response_model=list[AlertView])
def list_alerts(
    currency: CurrencyCode = Query(default=CurrencyCode.USD),
    severity: RiskLevel | None = Query(default=None),
    alert_status: AlertStatus | None = Query(default=None, alias="status"),
    repo: RiskRepository = Depends(get_repository),
) -> list[AlertView]:
    fx = repo.get_fx_snapshot()
    raw_alerts = repo.list_alerts()
    if severity:
        raw_alerts = [a for a in raw_alerts if a.severity == severity]
    if alert_status:
        raw_alerts = [a for a in raw_alerts if a.status == alert_status]

    views: list[AlertView] = []
    for alert in raw_alerts:
        exp_rep, fx_rate = convert_amount(
            alert.exposure_origin, alert.origin_currency, currency, fx
        )
        views.append(
            AlertView(
                **alert.model_dump(),
                reporting_currency=currency,
                exposure_reporting=exp_rep,
                fx_rate_applied=fx_rate,
            )
        )
    return views


@router.patch("/alerts/{alert_id}", response_model=AlertView)
def patch_alert_status(
    alert_id: str,
    payload: AlertUpdateRequest,
    request: Request,
    currency: CurrencyCode = Query(default=CurrencyCode.USD),
    actor: ActorIdentity = Depends(require_roles(UserRole.RISK_ANALYST)),
    repo: RiskRepository = Depends(get_repository),
) -> AlertView:
    start = time.perf_counter()
    updated = repo.update_alert_status(
        alert_id=alert_id,
        status=payload.status,
        updated_by=actor.email,
        analyst_note=payload.analyst_note,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alerta '{alert_id}' no encontrada.",
        )
    fx = repo.get_fx_snapshot()
    exp_rep, fx_rate = convert_amount(
        updated.exposure_origin, updated.origin_currency, currency, fx
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_audit_event(
        action="ALERT_STATUS_UPDATED",
        actor=actor,
        http_method=request.method,
        path=request.url.path,
        status_code=status.HTTP_200_OK,
        latency_ms=elapsed_ms,
        currency=currency.value,
        resource_id=alert_id,
        details={
            "new_status": updated.status.value,
            "client_id": updated.client_id,
            "analyst_note": payload.analyst_note,
        },
    )
    return AlertView(
        **updated.model_dump(),
        reporting_currency=currency,
        exposure_reporting=exp_rep,
        fx_rate_applied=fx_rate,
    )


@router.get("/audit/events", response_model=list[AuditEvent])
def get_audit_events(
    limit: int = Query(default=30, ge=1, le=100),
    actor: ActorIdentity = Depends(get_current_actor),
) -> list[AuditEvent]:
    _ = actor
    return list_recent_audit_events(limit=limit)
