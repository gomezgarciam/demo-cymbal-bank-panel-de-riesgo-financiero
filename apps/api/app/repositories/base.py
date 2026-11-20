"""Interfaz abstracta de repositorio (Cloud Firestore / Memoria local)."""

from abc import ABC, abstractmethod

from app.domain.models import (
    AlertRecord,
    AlertStatus,
    ClientPortfolioRecord,
    FxRatesSnapshot,
    StressTestRecord,
)


class RiskRepository(ABC):
    """Contrato único para desacoplar la lógica financiera del motor de persistencia."""

    @abstractmethod
    def list_clients(self) -> list[ClientPortfolioRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_fx_snapshot(self) -> FxRatesSnapshot:
        raise NotImplementedError

    @abstractmethod
    def save_fx_snapshot(self, snapshot: FxRatesSnapshot) -> FxRatesSnapshot:
        raise NotImplementedError

    @abstractmethod
    def list_alerts(self) -> list[AlertRecord]:
        raise NotImplementedError

    @abstractmethod
    def update_alert_status(
        self,
        alert_id: str,
        status: AlertStatus,
        updated_by: str,
        analyst_note: str | None = None,
    ) -> AlertRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_stress_tests(self) -> list[StressTestRecord]:
        raise NotImplementedError

    @abstractmethod
    def save_stress_test(self, record: StressTestRecord) -> StressTestRecord:
        raise NotImplementedError

    @abstractmethod
    def get_monthly_history_usd(self) -> list[dict[str, str]]:
        raise NotImplementedError
