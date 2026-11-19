"""Capa de Seguridad e Identidad (JWT / OIDC + RBAC) para cymbal-riesgo-api."""

import base64
import json
from typing import Callable

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


def _decode_unverified_jwt_payload(token: str) -> dict | None:
    """Extrae claims JWT en entornos de demo/desarrollo cuando se envía Bearer token.

    En producción sobre Google Cloud Run + Identity Platform, la verificación de firma
    RS256 y audiencia (aud/iss) se delega al SDK oficial de Firebase/Identity Platform
    o a Cloud Endpoints / IAP antes de aceptar claims.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def get_current_actor(
    request: Request,
    authorization: str | None = Header(default=None),
    x_cymbal_role: str | None = Header(default=None),
    x_cymbal_user: str | None = Header(default=None),
) -> ActorIdentity:
    """Resuelve la identidad autenticada y su rol RBAC para la petición actual."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        claims = _decode_unverified_jwt_payload(token)
        if claims and claims.get("role") in (UserRole.CFO.value, UserRole.RISK_ANALYST.value):
            role = UserRole(claims["role"])
            actor = ActorIdentity(
                email=str(claims.get("email", DEMO_PROFILES[role].email)),
                full_name=str(claims.get("name", DEMO_PROFILES[role].full_name)),
                role=role,
                auth_provider="identity-platform-jwt",
                mfa_verified=bool(claims.get("mfa", True)),
            )
            request.state.actor = actor
            return actor

    if settings.allow_demo_headers and x_cymbal_role:
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

    if settings.allow_demo_headers:
        actor = DEMO_PROFILES[UserRole.CFO]
        request.state.actor = actor
        return actor

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
