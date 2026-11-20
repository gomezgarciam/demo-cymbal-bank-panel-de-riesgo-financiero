"""Auditoría Bancaria Inmutable en formato JSON estructurado (Cloud Logging)."""

import json
import logging
import sys
from collections import deque
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from threading import Lock
from typing import Any
from uuid import uuid4

from app.config import settings
from app.domain.models import ActorIdentity, AuditEvent

_audit_logger = logging.getLogger("cymbal.audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False
if not _audit_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _audit_logger.addHandler(_handler)

_events_lock = Lock()
_recent_events: deque[AuditEvent] = deque(maxlen=250)


def record_audit_event(
    *,
    action: str,
    actor: ActorIdentity | None,
    http_method: str,
    path: str,
    status_code: int,
    latency_ms: float | Decimal,
    severity: str = "INFO",
    outcome: str = "SUCCESS",
    currency: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    """Emite una línea JSON compatible con Cloud Logging y conserva trazabilidad reciente."""
    latency_dec = Decimal(str(latency_ms)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN
    )
    event = AuditEvent(
        event_id=f"AUD-{uuid4().hex[:10].upper()}",
        timestamp_utc=datetime.now(timezone.utc),
        severity=severity,
        service=settings.service_name,
        action=action,
        actor_email=actor.email if actor else "system@cymbalbank.com",
        actor_role=actor.role.value if actor else "system",
        http_method=http_method,
        path=path,
        status_code=status_code,
        latency_ms=latency_dec,
        currency=currency,
        resource_id=resource_id,
        outcome=outcome,
        details=details or {},
    )

    payload = event.model_dump(mode="json")
    payload["logging.googleapis.com/labels"] = {
        "service": settings.service_name,
        "audit_stream": "banking-immutable",
        "actor_role": event.actor_role,
    }
    _audit_logger.info(json.dumps(payload, ensure_ascii=False))

    with _events_lock:
        _recent_events.appendleft(event)

    return event


def list_recent_audit_events(limit: int = 50) -> list[AuditEvent]:
    with _events_lock:
        return list(_recent_events)[:limit]


def clear_audit_events() -> None:
    """Utilidad exclusiva para aislamiento de pruebas unitarias."""
    with _events_lock:
        _recent_events.clear()
