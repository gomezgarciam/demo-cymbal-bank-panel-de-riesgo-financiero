"""Repositorio en memoria thread-safe para ejecución local, pruebas y demo MVP."""

from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock

from app.domain.models import (
    AlertRecord,
    AlertStatus,
    ClientPortfolioRecord,
    CurrencyCode,
    FxRatesSnapshot,
    StressTestRecord,
    StressTestRequest,
    UserRole,
)
from app.domain.stress_engine import run_stress_simulation
from app.repositories.base import RiskRepository
from app.repositories.seed_data import (
    build_initial_alerts,
    build_initial_clients,
    build_initial_fx_snapshot,
    build_monthly_history_usd,
)
from app.security.auth import DEMO_PROFILES


class InMemoryRiskRepository(RiskRepository):
    """Implementación en memoria precargada con cartera institucional de Cymbal Bank."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._clients: list[ClientPortfolioRecord] = build_initial_clients()
        self._fx_snapshot: FxRatesSnapshot = build_initial_fx_snapshot()
        self._alerts: dict[str, AlertRecord] = {
            a.alert_id: a for a in build_initial_alerts()
        }
        self._monthly_history: list[dict[str, str]] = build_monthly_history_usd()
        self._stress_tests: list[StressTestRecord] = []
        self._seed_initial_simulations()

    def _seed_initial_simulations(self) -> None:
        analyst = DEMO_PROFILES[UserRole.RISK_ANALYST]
        presets = [
            StressTestRequest(
                name="Escenario Moderado — Alza de Tasas +150 pbs",
                pd_shock_pct=Decimal("25.00"),
                lgd_shock_pp=Decimal("3.00"),
                fx_depreciation_latam_pct=Decimal("8.00"),
                reporting_currency=CurrencyCode.USD,
                notes="Escenario de comité trimestral con endurecimiento monetario gradual.",
            ),
            StressTestRequest(
                name="Estrés Severo — Recesión Regional y Choque FX LATAM",
                pd_shock_pct=Decimal("65.00"),
                lgd_shock_pp=Decimal("8.50"),
                fx_depreciation_latam_pct=Decimal("18.00"),
                reporting_currency=CurrencyCode.USD,
                notes="Prueba de resistencia regulatoria ante depreciación de MXN/COP y deterioro crediticio.",
            ),
        ]
        for req in presets:
            sim = run_stress_simulation(req, self._clients, self._fx_snapshot, analyst)
            self._stress_tests.insert(0, sim)

    def list_clients(self) -> list[ClientPortfolioRecord]:
        with self._lock:
            return list(self._clients)

    def get_fx_snapshot(self) -> FxRatesSnapshot:
        with self._lock:
            return self._fx_snapshot

    def save_fx_snapshot(self, snapshot: FxRatesSnapshot) -> FxRatesSnapshot:
        with self._lock:
            self._fx_snapshot = snapshot
            return self._fx_snapshot

    def list_alerts(self) -> list[AlertRecord]:
        with self._lock:
            return sorted(
                self._alerts.values(),
                key=lambda a: (a.status.value == AlertStatus.MITIGADA.value, -a.days_past_due),
            )

    def update_alert_status(
        self,
        alert_id: str,
        status: AlertStatus,
        updated_by: str,
        analyst_note: str | None = None,
    ) -> AlertRecord | None:
        with self._lock:
            existing = self._alerts.get(alert_id)
            if not existing:
                return None
            updated_desc = existing.description
            if analyst_note:
                updated_desc = f"{existing.description} [Nota analista: {analyst_note.strip()}]"
            updated = existing.model_copy(
                update={
                    "status": status,
                    "description": updated_desc,
                    "updated_at_utc": datetime.now(timezone.utc),
                    "updated_by": updated_by,
                }
            )
            self._alerts[alert_id] = updated
            return updated

    def list_stress_tests(self) -> list[StressTestRecord]:
        with self._lock:
            return list(self._stress_tests)

    def save_stress_test(self, record: StressTestRecord) -> StressTestRecord:
        with self._lock:
            self._stress_tests.insert(0, record)
            return record

    def get_monthly_history_usd(self) -> list[dict[str, str]]:
        with self._lock:
            return list(self._monthly_history)
