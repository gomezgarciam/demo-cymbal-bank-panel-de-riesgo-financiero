"""Punto de entrada principal de cymbal-riesgo-api (Google Cloud Run / FastAPI)."""

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router as v1_router
from app.config import settings

app = FastAPI(
    title="Cymbal Bank — Panel de Riesgo Financiero API",
    description=(
        "Backend financiero MVP v1.0 en FastAPI con aritmética exacta Python Decimal, "
        "motor de estrés (EL, NPL, PD, LGD), conversión multimoneda FX (USD/EUR/MXN/COP), "
        "RBAC y auditoría bancaria inmutable en JSON."
    ),
    version=settings.service_version,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https?://.*" if settings.app_env == "development" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time-Ms", "X-SLO-Target-Ms"],
)


@app.middleware("http")
async def slo_telemetry_middleware(request: Request, call_next):
    """Mide latencia por petición para telemetría de cumplimiento SLO (< 500 ms)."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
    response.headers["X-SLO-Target-Ms"] = str(settings.slo_latency_target_ms)
    return response


app.include_router(v1_router)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "api_base": "/api/v1",
        "docs": "/api/v1/docs",
    }
