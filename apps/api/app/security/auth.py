"""Capa de Seguridad e Identidad (Identity Platform OIDC JWT + Cloud Scheduler + RBAC)."""

from __future__ import annotations

import base64
import json
from typing import Any, Callable

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import settings
from app.domain.models import ActorIdentity, UserRole
from app.observability.audit import record_audit_event

DEMO_PROFILES: dict[UserRole, ActorIdentity] = {
    UserRole.CFO: ActorIdentity(
        email="cfo.corporativo@cymbalbank.com",
        full_name="Elena Mendoza — CFO Corporativo",
        role=UserRole.CFO,
        auth_provider="identity-platform-oidc",
        mfa_verified=True,
    ),
    UserRole.RISK_ANALYST: ActorIdentity(
        email="analista.riesgo@cymbalbank.com",
        full_name="Carlos Navarro — Analista Senior de Riesgo",
        role=UserRole.RISK_ANALYST,
        auth_provider="identity-platform-oidc",
        mfa_verified=True,
    ),
}


def _decode_unverified_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decodifica claims JWT solo en entornos de desarrollo local."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def verify_oidc_jwt(token: str) -> dict[str, Any]:
    """Verifica criptográficamente un JWT emitido por Identity Platform / Google OIDC.

    En producción valida firma RS256, expiración, audiencia (aud == gcp_project_id)
    y emisor (iss). Lanza ValueError si el token es inválido o caducado.
    """
    try:
        from google.auth.transport import requests as google_requests  # type: ignore
        from google.oauth2 import id_token  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "El paquete google-auth es obligatorio para verificación OIDC en producción."
        ) from exc

    request_adapter = google_requests.Request()
    # Intenta primero token de Identity Platform / Firebase y luego OIDC estándar de Google (Cloud Scheduler)
    try:
        claims = id_token.verify_firebase_token(
            token, request_adapter, audience=settings.gcp_project_id
        )
    except Exception:
        claims = id_token.verify_oauth2_token(
            token, request_adapter, audience=settings.gcp_project_id
        )

    if settings.oidc_issuer and claims.get("iss") != settings.oidc_issuer:
        # Permitir emisor accounts.google.com solo para Cloud Scheduler SA autorizado
        if claims.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
            raise ValueError("Emisor OIDC (iss) no autorizado.")
    return claims


def _actor_from_claims(claims: dict[str, Any], provider: str) -> ActorIdentity:
    email = str(claims.get("email", "")).strip()
    # Soporte para Service Account de Cloud Scheduler autorizado
    if (
        settings.scheduler_service_account
        and email
        and email.lower() == settings.scheduler_service_account.lower()
    ):
        return ActorIdentity(
            email=email,
            full_name="Cloud Scheduler + FX (Service Account)",
            role=UserRole.RISK_ANALYST,
            auth_provider="gcp-cloud-scheduler-oidc",
            mfa_verified=True,
        )

    raw_role = str(claims.get("role", "")).strip().lower()
    if raw_role not in (UserRole.CFO.value, UserRole.RISK_ANALYST.value):
        raise ValueError("El token OIDC no contiene un claim RBAC válido ('cfo' o 'risk_analyst').")

    role = UserRole(raw_role)
    return ActorIdentity(
        email=email or DEMO_PROFILES[role].email,
        full_name=str(claims.get("name", DEMO_PROFILES[role].full_name)),
        role=role,
        auth_provider=provider,
        mfa_verified=bool(claims.get("mfa", True)),
    )


def get_current_actor(
    request: Request,
    authorization: str | None = Header(default=None),
    x_cymbal_role: str | None = Header(default=None),
    x_cymbal_user: str | None = Header(default=None),
) -> ActorIdentity:
    """Resuelve y valida la identidad autenticada y su rol RBAC."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if settings.effective_demo_headers_allowed:
            claims = _decode_unverified_jwt_payload(token)
            if claims:
                try:
                    actor = _actor_from_claims(claims, "identity-platform-jwt-dev")
                    request.state.actor = actor
                    return actor
                except ValueError:
                    pass
        else:
            try:
                claims = verify_oidc_jwt(token)
                actor = _actor_from_claims(claims, "identity-platform-oidc-verified")
                request.state.actor = actor
                return actor
            except Exception as exc:
                record_audit_event(
                    action="AUTH_TOKEN_REJECTED",
                    actor=None,
                    http_method=request.method,
                    path=request.url.path,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    latency_ms=0.0,
                    severity="WARNING",
                    outcome="DENIED",
                    details={"reason": str(exc)},
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token OIDC/JWT inválido o no autorizado por Identity Platform.",
                ) from exc

    if settings.effective_demo_headers_allowed and x_cymbal_role:
        normalized = x_cymbal_role.strip().lower()
        if normalized not in (UserRole.CFO.value, UserRole.RISK_ANALYST.value):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Rol RBAC no reconocido. Roles válidos: cfo, risk_analyst.",
            )
        role = UserRole(normalized)
        base_profile = DEMO_PROFILES[role]
        actor = ActorIdentity(
            email=x_cymbal_user.strip() if x_cymbal_user else base_profile.email,
            full_name=base_profile.full_name,
            role=role,
            auth_provider="identity-platform-oidc",
            mfa_verified=True,
        )
        request.state.actor = actor
        return actor

    if settings.effective_demo_headers_allowed:
        actor = DEMO_PROFILES[UserRole.CFO]
        request.state.actor = actor
        return actor

    record_audit_event(
        action="AUTH_TOKEN_REJECTED",
        actor=None,
        http_method=request.method,
        path=request.url.path,
        status_code=status.HTTP_401_UNAUTHORIZED,
        latency_ms=0.0,
        severity="WARNING",
        outcome="DENIED",
        details={"reason": "Cabecera Authorization Bearer requerida en producción."},
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token OIDC/JWT requerido por Identity Platform.",
    )


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Dependencia FastAPI que impone control de acceso RBAC y audita denegaciones."""

    def _checker(
        request: Request,
        actor: ActorIdentity = Depends(get_current_actor),
    ) -> ActorIdentity:
        if actor.role not in allowed_roles:
            record_audit_event(
                action="RBAC_ACCESS_DENIED",
                actor=actor,
                http_method=request.method,
                path=request.url.path,
                status_code=status.HTTP_403_FORBIDDEN,
                latency_ms=0.0,
                severity="WARNING",
                outcome="DENIED",
                details={
                    "required_roles": [r.value for r in allowed_roles],
                    "provided_role": actor.role.value,
                    "reason": "Permisos insuficientes para operación restringida a Analista de Riesgo.",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso denegado por política RBAC: el perfil '{actor.role.value}' "
                    f"no tiene autorización para esta operación. Roles permitidos: "
                    f"{', '.join(r.value for r in allowed_roles)}."
                ),
            )
        return actor

    return _checker
