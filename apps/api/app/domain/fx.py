"""Motor determinístico de conversión multimoneda FX (USD, EUR, MXN, COP)."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN

from app.domain.models import CurrencyCode, FxRatesSnapshot

MONEY_QUANT = Decimal("0.01")
RATE_QUANT = Decimal("0.000001")
PCT_QUANT = Decimal("0.01")
FACTOR_QUANT = Decimal("0.000001")


def quantize_money(value: Decimal) -> Decimal:
    """Redondeo bancario estándar (ROUND_HALF_EVEN) a 2 decimales."""
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_EVEN)


def quantize_rate(value: Decimal) -> Decimal:
    """Precisión interna de 6 decimales para tasas FX y factores."""
    return value.quantize(RATE_QUANT, rounding=ROUND_HALF_EVEN)


def quantize_pct(value: Decimal) -> Decimal:
    """Redondeo de porcentajes a 2 decimales."""
    return value.quantize(PCT_QUANT, rounding=ROUND_HALF_EVEN)


def get_cross_rate(
    origin: CurrencyCode,
    target: CurrencyCode,
    snapshot: FxRatesSnapshot,
) -> Decimal:
    """Calcula la tasa cruzada exacta origin -> target vía base USD.

    Las tasas del snapshot representan unidades de cada divisa por 1 USD:
    ej. MXN = 19.850000 significa 1 USD = 19.85 MXN.
    Por lo tanto, 1 unidad de `origin` equivale a `(rate[target] / rate[origin])` en `target`.
    """
    if origin == target:
        return Decimal("1.000000")
    origin_per_usd = snapshot.rates[origin]
    target_per_usd = snapshot.rates[target]
    if origin_per_usd <= Decimal("0") or target_per_usd <= Decimal("0"):
        raise ValueError("Las tasas FX deben ser estrictamente positivas.")
    return quantize_rate(target_per_usd / origin_per_usd)


def convert_amount(
    amount: Decimal,
    origin: CurrencyCode,
    target: CurrencyCode,
    snapshot: FxRatesSnapshot,
) -> tuple[Decimal, Decimal]:
    """Convierte un monto exacto Decimal y devuelve (monto_convertido, tasa_aplicada)."""
    cross_rate = get_cross_rate(origin, target, snapshot)
    if origin == target:
        return quantize_money(amount), cross_rate
    # Se usa relación directa de tasas del snapshot para evitar doble redondeo intermedio.
    exact_converted = (amount * snapshot.rates[target]) / snapshot.rates[origin]
    return quantize_money(exact_converted), cross_rate


def apply_latam_fx_shock(
    snapshot: FxRatesSnapshot,
    depreciation_latam_pct: Decimal,
) -> FxRatesSnapshot:
    """Aplica choque cambiario (depreciación) a MXN y COP frente a USD."""
    factor = Decimal("1") + (depreciation_latam_pct / Decimal("100"))
    if factor <= Decimal("0"):
        raise ValueError("El choque FX no puede producir tasas negativas o nulas.")

    stressed_rates: dict[CurrencyCode, Decimal] = {}
    for code, rate in snapshot.rates.items():
        if code in (CurrencyCode.MXN, CurrencyCode.COP):
            stressed_rates[code] = quantize_rate(rate * factor)
        else:
            stressed_rates[code] = quantize_rate(rate)

    return FxRatesSnapshot(
        base_currency=snapshot.base_currency,
        rates=stressed_rates,
        as_of_utc=datetime.now(timezone.utc),
        source=f"Escenario FX Estresado (LATAM {depreciation_latam_pct:+.2f}%)",
    )
