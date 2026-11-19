"""Pruebas unitarias de precisión Decimal para conversión multimoneda FX."""

from decimal import Decimal

import pytest

from app.domain.fx import apply_latam_fx_shock, convert_amount, get_cross_rate
from app.domain.models import CurrencyCode
from app.repositories.seed_data import build_initial_fx_snapshot


def test_identity_conversion_keeps_exact_decimal() -> None:
    fx = build_initial_fx_snapshot()
    converted, rate = convert_amount(
        Decimal("14250000.55"), CurrencyCode.USD, CurrencyCode.USD, fx
    )
    assert converted == Decimal("14250000.55")
    assert rate == Decimal("1.000000")
    assert isinstance(converted, Decimal)


def test_cross_currency_conversion_cop_to_eur_and_mxn() -> None:
    fx = build_initial_fx_snapshot()
    # 4,285,000.00 COP = 1,000.00 USD = 921.50 EUR = 19,850.00 MXN
    eur_val, _ = convert_amount(
        Decimal("4285000.00"), CurrencyCode.COP, CurrencyCode.EUR, fx
    )
    mxn_val, _ = convert_amount(
        Decimal("4285000.00"), CurrencyCode.COP, CurrencyCode.MXN, fx
    )
    assert eur_val == Decimal("921.50")
    assert mxn_val == Decimal("19850.00")


def test_bankers_rounding_half_even() -> None:
    fx = build_initial_fx_snapshot()
    # 0.005 -> 0.00 (par), 0.015 -> 0.02 (par)
    val1, _ = convert_amount(Decimal("10.005"), CurrencyCode.USD, CurrencyCode.USD, fx)
    val2, _ = convert_amount(Decimal("10.015"), CurrencyCode.USD, CurrencyCode.USD, fx)
    assert val1 == Decimal("10.00")
    assert val2 == Decimal("10.02")


def test_latam_fx_shock_affects_only_mxn_and_cop() -> None:
    fx = build_initial_fx_snapshot()
    stressed = apply_latam_fx_shock(fx, Decimal("20.00"))
    assert stressed.rates[CurrencyCode.USD] == Decimal("1.000000")
    assert stressed.rates[CurrencyCode.EUR] == fx.rates[CurrencyCode.EUR]
    assert stressed.rates[CurrencyCode.MXN] == Decimal("23.820000")
    assert stressed.rates[CurrencyCode.COP] == Decimal("5142.000000")


def test_get_cross_rate_rejects_invalid_fx_shock() -> None:
    fx = build_initial_fx_snapshot()
    with pytest.raises(ValueError):
        apply_latam_fx_shock(fx, Decimal("-100.00"))
    assert get_cross_rate(CurrencyCode.USD, CurrencyCode.MXN, fx) == Decimal("19.850000")
