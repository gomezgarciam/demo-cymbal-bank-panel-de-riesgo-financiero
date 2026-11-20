"""Adaptador de producción para Google Cloud Firestore (colecciones bancarias CMEK)."""

from datetime import datetime, timezone

from app.config import settings
from app.domain.models import (
    AlertRecord,
    AlertStatus,
    ClientPortfolioRecord,
    FxRatesSnapshot,
    StressTestRecord,
)
from app.repositories.base import RiskRepository
from app.repositories.seed_data import (
    build_initial_alerts,
    build_initial_clients,
    build_initial_fx_snapshot,
    build_monthly_history_usd,
)


class FirestoreRiskRepository(RiskRepository):
    """Persistencia sobre Google Cloud Firestore (clientes, carteras, simulaciones, alertas, fx_rates)."""

    COL_CLIENTS = "carteras"
    COL_ALERTS = "alertas"
    COL_SIMULATIONS = "simulaciones"
    COL_FX = "fx_rates"

    def __init__(self) -> None:
        try:
            from google.cloud import firestore  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Instale el extra opcional 'gcp' (google-cloud-firestore) para usar STORAGE_BACKEND=firestore."
            ) from exc

        self._client = firestore.Client(
            project=settings.gcp_project_id,
            database=settings.firestore_database,
        )
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        existing_clients = list(self._client.collection(self.COL_CLIENTS).limit(1).stream())
        if not existing_clients:
            batch = self._client.batch()
            for item in build_initial_clients():
                ref = self._client.collection(self.COL_CLIENTS).document(item.client_id)
                batch.set(ref, item.model_dump(mode="json"))
            for alert in build_initial_alerts():
                ref = self._client.collection(self.COL_ALERTS).document(alert.alert_id)
                batch.set(ref, alert.model_dump(mode="json"))
            fx_ref = self._client.collection(self.COL_FX).document("latest")
            batch.set(fx_ref, build_initial_fx_snapshot().model_dump(mode="json"))
            batch.commit()

    def list_clients(self) -> list[ClientPortfolioRecord]:
        docs = self._client.collection(self.COL_CLIENTS).stream()
        return [ClientPortfolioRecord.model_validate(d.to_dict()) for d in docs]

    def get_fx_snapshot(self) -> FxRatesSnapshot:
        doc = self._client.collection(self.COL_FX).document("latest").get()
        if not doc.exists:
            return build_initial_fx_snapshot()
        return FxRatesSnapshot.model_validate(doc.to_dict())

    def save_fx_snapshot(self, snapshot: FxRatesSnapshot) -> FxRatesSnapshot:
        payload = snapshot.model_dump(mode="json")
        self._client.collection(self.COL_FX).document("latest").set(payload)
        ts_key = snapshot.as_of_utc.strftime("%Y%m%dT%H%M%SZ")
        self._client.collection(self.COL_FX).document(f"hist-{ts_key}").set(payload)
        return snapshot

    def list_alerts(self) -> list[AlertRecord]:
        docs = self._client.collection(self.COL_ALERTS).stream()
        alerts = [AlertRecord.model_validate(d.to_dict()) for d in docs]
        return sorted(
            alerts,
            key=lambda a: (a.status.value == AlertStatus.MITIGADA.value, -a.days_past_due),
        )

    def update_alert_status(
        self,
        alert_id: str,
        status: AlertStatus,
        updated_by: str,
        analyst_note: str | None = None,
    ) -> AlertRecord | None:
        ref = self._client.collection(self.COL_ALERTS).document(alert_id)
        snap = ref.get()
        if not snap.exists:
            return None
        existing = AlertRecord.model_validate(snap.to_dict())
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
        ref.set(updated.model_dump(mode="json"))
        return updated

    def list_stress_tests(self) -> list[StressTestRecord]:
        docs = (
            self._client.collection(self.COL_SIMULATIONS)
            .order_by("created_at_utc", direction="DESCENDING")
            .limit(50)
            .stream()
        )
        return [StressTestRecord.model_validate(d.to_dict()) for d in docs]

    def save_stress_test(self, record: StressTestRecord) -> StressTestRecord:
        self._client.collection(self.COL_SIMULATIONS).document(record.simulation_id).set(
            record.model_dump(mode="json")
        )
        return record

    def get_monthly_history_usd(self) -> list[dict[str, str]]:
        return build_monthly_history_usd()
