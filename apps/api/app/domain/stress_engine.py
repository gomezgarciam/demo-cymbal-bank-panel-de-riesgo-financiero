"""Motor de Riesgo Crediticio y Pruebas de Estrés (EL, NPL, PD, LGD) con Python Decimal."""

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from uuid import uuid4

from app.config import settings
from app.domain.fx import (
    apply_latam_fx_shock,
    convert_amount,
    quantize_money,
    quantize_pct,
)
from app.domain.models import (
    ActorIdentity,
    AlertRecord,
    AlertStatus,
    ClientPortfolioRecord,
    ClientPortfolioView,
    CurrencyBreakdown,
    CurrencyCode,
    ExecutiveInsight,
    FxRatesSnapshot,
    MonthlyRiskPoint,
    PortfolioSummaryResponse,
    RiskLevel,
    SectorExposure,
    SectorStressImpact,
    StressTestRecord,
    StressTestRequest,
)

HUNDRED = Decimal("100")
MAX_PD = Decimal("0.990000")
MIN_PD = Decimal("0.000500")
MAX_LGD = Decimal("0.950000")
MIN_LGD = Decimal("0.050000")
NPL_DAYS_THRESHOLD = 90
STRESS_NPL_PD_THRESHOLD = Decimal("0.120000")
LATAM_COUNTRIES = {"México", "Colombia", "Chile", "Perú", "Brasil"}


def calculate_expected_loss(ead: Decimal, pd: Decimal, lgd: Decimal) -> Decimal:
    """Calcula la Pérdida Esperada exacta: EL = PD * LGD * EAD."""
    return quantize_money(ead * pd * lgd)


def classify_client_risk(pd: Decimal, days_past_due: int) -> RiskLevel:
    """Clasifica severidad de riesgo crediticio según semáforo de Cymbal Bank."""
    if days_past_due > NPL_DAYS_THRESHOLD or pd >= Decimal("0.0800"):
        return RiskLevel.ALTO
    if days_past_due >= 30 or pd >= Decimal("0.0350"):
        return RiskLevel.MEDIO
    return RiskLevel.BAJO


def classify_portfolio_risk(
    npl_ratio_pct: Decimal,
    el_rate_pct: Decimal,
) -> RiskLevel:
    """Evalúa severidad agregada frente a límites de apetito de riesgo institucional."""
    if (
        npl_ratio_pct > settings.npl_appetite_limit_pct
        or el_rate_pct > settings.el_rate_appetite_limit_pct
    ):
        return RiskLevel.ALTO
    if (
        npl_ratio_pct >= settings.npl_appetite_limit_pct * Decimal("0.75")
        or el_rate_pct >= settings.el_rate_appetite_limit_pct * Decimal("0.75")
    ):
        return RiskLevel.MEDIO
    return RiskLevel.BAJO


def project_client(
    record: ClientPortfolioRecord,
    reporting_currency: CurrencyCode,
    fx_snapshot: FxRatesSnapshot,
) -> ClientPortfolioView:
    """Proyecta un registro de cartera a la divisa de reporte con precisión Decimal."""
    ead_rep, fx_rate = convert_amount(
        record.ead_origin,
        record.origin_currency,
        reporting_currency,
        fx_snapshot,
    )
    el_rep = calculate_expected_loss(ead_rep, record.pd, record.lgd)
    el_rate_pct = (
        quantize_pct((el_rep / ead_rep) * HUNDRED)
        if ead_rep > Decimal("0")
        else Decimal("0.00")
    )
    is_npl = record.days_past_due > NPL_DAYS_THRESHOLD
    risk_level = classify_client_risk(record.pd, record.days_past_due)

    return ClientPortfolioView(
        client_id=record.client_id,
        name=record.name,
        country=record.country,
        sector=record.sector,
        credit_rating=record.credit_rating,
        facility_type=record.facility_type,
        origin_currency=record.origin_currency,
        reporting_currency=reporting_currency,
        fx_rate_applied=fx_rate,
        ead_origin=quantize_money(record.ead_origin),
        ead=ead_rep,
        pd_pct=quantize_pct(record.pd * HUNDRED),
        lgd_pct=quantize_pct(record.lgd * HUNDRED),
        expected_loss=el_rep,
        el_rate_pct=el_rate_pct,
        days_past_due=record.days_past_due,
        is_npl=is_npl,
        risk_level=risk_level,
        maturity_date=record.maturity_date,
        last_review_date=record.last_review_date,
    )


def _format_compact_money(amount: Decimal, currency: CurrencyCode) -> str:
    """Formatea cifras ejecutivas (M o K) en tono sobrio para CFO."""
    millions = amount / Decimal("1000000")
    if abs(millions) >= Decimal("1"):
        return f"{currency.value} {millions.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN):,.2f}M"
    return f"{currency.value} {quantize_money(amount):,.2f}"


def build_portfolio_summary(
    records: list[ClientPortfolioRecord],
    alerts: list[AlertRecord],
    monthly_history_usd: list[dict[str, str]],
    reporting_currency: CurrencyCode,
    fx_snapshot: FxRatesSnapshot,
) -> PortfolioSummaryResponse:
    """Consolida KPIs ejecutivos, desglose sectorial, histórico y conclusión para CFO."""
    views = [project_client(r, reporting_currency, fx_snapshot) for r in records]

    total_ead = quantize_money(sum((v.ead for v in views), Decimal("0.00")))
    total_el = quantize_money(sum((v.expected_loss for v in views), Decimal("0.00")))
    npl_ead = quantize_money(
        sum((v.ead for v in views if v.is_npl), Decimal("0.00"))
    )

    if total_ead > Decimal("0"):
        el_rate_pct = quantize_pct((total_el / total_ead) * HUNDRED)
        npl_ratio_pct = quantize_pct((npl_ead / total_ead) * HUNDRED)
        weighted_pd_pct = quantize_pct(
            sum((v.ead * v.pd_pct for v in views), Decimal("0.00")) / total_ead
        )
        weighted_lgd_pct = quantize_pct(
            sum((v.ead * v.lgd_pct for v in views), Decimal("0.00")) / total_ead
        )
    else:
        el_rate_pct = Decimal("0.00")
        npl_ratio_pct = Decimal("0.00")
        weighted_pd_pct = Decimal("0.00")
        weighted_lgd_pct = Decimal("0.00")

    risk_distribution = {
        RiskLevel.BAJO: sum(1 for v in views if v.risk_level == RiskLevel.BAJO),
        RiskLevel.MEDIO: sum(1 for v in views if v.risk_level == RiskLevel.MEDIO),
        RiskLevel.ALTO: sum(1 for v in views if v.risk_level == RiskLevel.ALTO),
    }

    active_alerts = [a for a in alerts if a.status != AlertStatus.MITIGADA]
    alerts_summary = {
        RiskLevel.ALTO: sum(1 for a in active_alerts if a.severity == RiskLevel.ALTO),
        RiskLevel.MEDIO: sum(1 for a in active_alerts if a.severity == RiskLevel.MEDIO),
        RiskLevel.BAJO: sum(1 for a in active_alerts if a.severity == RiskLevel.BAJO),
    }

    # Agrupación sectorial
    by_sector: dict[str, list[ClientPortfolioView]] = defaultdict(list)
    for v in views:
        by_sector[v.sector].append(v)

    sector_exposures: list[SectorExposure] = []
    for sector, items in by_sector.items():
        s_ead = quantize_money(sum((i.ead for i in items), Decimal("0.00")))
        s_el = quantize_money(sum((i.expected_loss for i in items), Decimal("0.00")))
        s_npl = quantize_money(
            sum((i.ead for i in items if i.is_npl), Decimal("0.00"))
        )
        s_el_rate = (
            quantize_pct((s_el / s_ead) * HUNDRED) if s_ead > Decimal("0") else Decimal("0.00")
        )
        s_npl_rate = (
            quantize_pct((s_npl / s_ead) * HUNDRED) if s_ead > Decimal("0") else Decimal("0.00")
        )
        share_pct = (
            quantize_pct((s_ead / total_ead) * HUNDRED)
            if total_ead > Decimal("0")
            else Decimal("0.00")
        )
        s_risk = classify_portfolio_risk(s_npl_rate, s_el_rate)
        sector_exposures.append(
            SectorExposure(
                sector=sector,
                client_count=len(items),
                ead=s_ead,
                expected_loss=s_el,
                el_rate_pct=s_el_rate,
                npl_ratio_pct=s_npl_rate,
                share_of_portfolio_pct=share_pct,
                risk_level=s_risk,
            )
        )
    sector_exposures.sort(key=lambda s: s.ead, reverse=True)

    # Desglose por moneda de origen
    by_currency: dict[CurrencyCode, list[ClientPortfolioView]] = defaultdict(list)
    for v in views:
        by_currency[v.origin_currency].append(v)

    currency_breakdown: list[CurrencyBreakdown] = []
    for code in CurrencyCode:
        c_items = by_currency.get(code, [])
        c_ead = quantize_money(sum((i.ead for i in c_items), Decimal("0.00")))
        c_share = (
            quantize_pct((c_ead / total_ead) * HUNDRED)
            if total_ead > Decimal("0")
            else Decimal("0.00")
        )
        currency_breakdown.append(
            CurrencyBreakdown(
                origin_currency=code,
                ead_in_reporting=c_ead,
                share_pct=c_share,
                client_count=len(c_items),
            )
        )

    # Serie histórica mensual convertida desde USD base a divisa de reporte
    monthly_trend: list[MonthlyRiskPoint] = []
    for pt in monthly_history_usd:
        m_ead, _ = convert_amount(
            Decimal(pt["ead_usd"]), CurrencyCode.USD, reporting_currency, fx_snapshot
        )
        m_el, _ = convert_amount(
            Decimal(pt["el_usd"]), CurrencyCode.USD, reporting_currency, fx_snapshot
        )
        m_el_rate = (
            quantize_pct((m_el / m_ead) * HUNDRED) if m_ead > Decimal("0") else Decimal("0.00")
        )
        monthly_trend.append(
            MonthlyRiskPoint(
                period=pt["period"],
                ead=m_ead,
                expected_loss=m_el,
                npl_ratio_pct=quantize_pct(Decimal(pt["npl_ratio_pct"])),
                el_rate_pct=m_el_rate,
            )
        )
    # Último punto sincronizado exactamente con el corte actual de cartera
    if monthly_trend:
        monthly_trend[-1] = MonthlyRiskPoint(
            period=monthly_trend[-1].period,
            ead=total_ead,
            expected_loss=total_el,
            npl_ratio_pct=npl_ratio_pct,
            el_rate_pct=el_rate_pct,
        )

    # Síntesis ejecutiva orientada a CFO (conclusión primero)
    npl_variance_bps = int(
        ((npl_ratio_pct - settings.npl_appetite_limit_pct) * HUNDRED).to_integral_value(
            rounding=ROUND_HALF_EVEN
        )
    )
    el_variance_bps = int(
        ((el_rate_pct - settings.el_rate_appetite_limit_pct) * HUNDRED).to_integral_value(
            rounding=ROUND_HALF_EVEN
        )
    )
    overall_status = classify_portfolio_risk(npl_ratio_pct, el_rate_pct)

    top_risk_sector = max(sector_exposures, key=lambda s: s.expected_loss) if sector_exposures else None
    npl_delta_txt = (
        f"superando en {npl_variance_bps} pbs"
        if npl_variance_bps > 0
        else f"{abs(npl_variance_bps)} pbs por debajo de"
    )
    headline = (
        f"Exposición corporativa de {_format_compact_money(total_ead, reporting_currency)} "
        f"con NPL en {npl_ratio_pct:.2f}% ({npl_delta_txt} el umbral interno de {settings.npl_appetite_limit_pct:.2f}%)."
    )
    sector_clause = (
        f" La mayor concentración de pérdida esperada se registra en {top_risk_sector.sector} "
        f"({_format_compact_money(top_risk_sector.expected_loss, reporting_currency)}, "
        f"{top_risk_sector.el_rate_pct:.2f}% sobre exposición sectorial)."
        if top_risk_sector
        else ""
    )
    summary = (
        f"La pérdida esperada consolidada (EL) asciende a {_format_compact_money(total_el, reporting_currency)} "
        f"({el_rate_pct:.2f}% del EAD total), con {alerts_summary[RiskLevel.ALTO]} alertas de Riesgo Alto y "
        f"{alerts_summary[RiskLevel.MEDIO]} en vigilancia activa.{sector_clause}"
    )
    if overall_status == RiskLevel.ALTO:
        recommendation = (
            "Recomendación al CFO: activar plan de reestructuración y cobertura de garantías sobre las exposiciones "
            "con mora superior a 90 días y ejecutar prueba de estrés cambiario LATAM antes del comité semanal de crédito."
        )
    elif overall_status == RiskLevel.MEDIO:
        recommendation = (
            "Recomendación al CFO: mantener vigilancia preventiva sobre clientes en rango 30–89 días de mora "
            "y validar límites sectoriales mediante simulación de choque +150 pbs en PD."
        )
    else:
        recommendation = (
            "Recomendación al CFO: cartera dentro del apetito institucional de riesgo; preservar provisiones actuales "
            "y monitorear sensibilidad FX en líneas originadas en MXN y COP."
        )

    return PortfolioSummaryResponse(
        reporting_currency=reporting_currency,
        as_of_utc=datetime.now(timezone.utc),
        fx_snapshot=fx_snapshot,
        total_clients=len(views),
        total_ead=total_ead,
        total_expected_loss=total_el,
        el_rate_pct=el_rate_pct,
        el_appetite_limit_pct=settings.el_rate_appetite_limit_pct,
        npl_ead=npl_ead,
        npl_ratio_pct=npl_ratio_pct,
        npl_appetite_limit_pct=settings.npl_appetite_limit_pct,
        weighted_pd_pct=weighted_pd_pct,
        weighted_lgd_pct=weighted_lgd_pct,
        risk_distribution=risk_distribution,
        alerts_summary=alerts_summary,
        open_alerts_total=len(active_alerts),
        sector_exposures=sector_exposures,
        currency_breakdown=currency_breakdown,
        monthly_trend=monthly_trend,
        executive_insight=ExecutiveInsight(
            headline=headline,
            summary=summary,
            recommendation=recommendation,
            overall_status=overall_status,
            npl_variance_bps=npl_variance_bps,
            el_variance_bps=el_variance_bps,
        ),
    )


def run_stress_simulation(
    request: StressTestRequest,
    records: list[ClientPortfolioRecord],
    fx_snapshot: FxRatesSnapshot,
    actor: ActorIdentity,
) -> StressTestRecord:
    """Ejecuta prueba de estrés determinística sobre EL, NPL, PD, LGD y tipo de cambio FX."""
    reporting = request.reporting_currency
    stressed_fx = apply_latam_fx_shock(fx_snapshot, request.fx_depreciation_latam_pct)

    pd_multiplier = Decimal("1") + (request.pd_shock_pct / HUNDRED)
    lgd_additive = request.lgd_shock_pp / HUNDRED
    fx_mismatch_pd_addon = (
        max(Decimal("0"), request.fx_depreciation_latam_pct) / HUNDRED
    ) * Decimal("0.18")

    base_ead_total = Decimal("0.00")
    stressed_ead_total = Decimal("0.00")
    base_el_total = Decimal("0.00")
    stressed_el_total = Decimal("0.00")
    base_npl_ead = Decimal("0.00")
    stressed_npl_ead = Decimal("0.00")

    sector_acc: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "base_ead": Decimal("0.00"),
            "stressed_ead": Decimal("0.00"),
            "base_el": Decimal("0.00"),
            "stressed_el": Decimal("0.00"),
            "stressed_npl_ead": Decimal("0.00"),
        }
    )

    for rec in records:
        base_ead, _ = convert_amount(rec.ead_origin, rec.origin_currency, reporting, fx_snapshot)
        base_el = calculate_expected_loss(base_ead, rec.pd, rec.lgd)
        base_is_npl = rec.days_past_due > NPL_DAYS_THRESHOLD

        in_scope = request.sector_filter is None or rec.sector == request.sector_filter

        # Conversión bajo tasas FX estresadas
        stressed_ead, _ = convert_amount(
            rec.ead_origin, rec.origin_currency, reporting, stressed_fx
        )

        if in_scope:
            stressed_pd = rec.pd * pd_multiplier
            # Descalce cambiario: clientes LATAM con deuda en USD/EUR sufren presión adicional en PD
            if (
                rec.country in LATAM_COUNTRIES
                and rec.origin_currency in (CurrencyCode.USD, CurrencyCode.EUR)
                and fx_mismatch_pd_addon > Decimal("0")
            ):
                stressed_pd = stressed_pd + fx_mismatch_pd_addon
            stressed_pd = max(MIN_PD, min(MAX_PD, stressed_pd))
            stressed_lgd = max(MIN_LGD, min(MAX_LGD, rec.lgd + lgd_additive))
        else:
            stressed_pd = rec.pd
            stressed_lgd = rec.lgd

        stressed_el = calculate_expected_loss(stressed_ead, stressed_pd, stressed_lgd)
        stressed_is_npl = base_is_npl or (
            in_scope and (rec.days_past_due >= 30 and stressed_pd >= STRESS_NPL_PD_THRESHOLD)
        )

        base_ead_total += base_ead
        stressed_ead_total += stressed_ead
        base_el_total += base_el
        stressed_el_total += stressed_el
        if base_is_npl:
            base_npl_ead += base_ead
        if stressed_is_npl:
            stressed_npl_ead += stressed_ead

        s = sector_acc[rec.sector]
        s["base_ead"] += base_ead
        s["stressed_ead"] += stressed_ead
        s["base_el"] += base_el
        s["stressed_el"] += stressed_el
        if stressed_is_npl:
            s["stressed_npl_ead"] += stressed_ead

    base_ead_total = quantize_money(base_ead_total)
    stressed_ead_total = quantize_money(stressed_ead_total)
    base_el_total = quantize_money(base_el_total)
    stressed_el_total = quantize_money(stressed_el_total)
    delta_el = quantize_money(stressed_el_total - base_el_total)

    delta_el_pct = (
        quantize_pct((delta_el / base_el_total) * HUNDRED)
        if base_el_total > Decimal("0")
        else Decimal("0.00")
    )
    base_el_rate_pct = (
        quantize_pct((base_el_total / base_ead_total) * HUNDRED)
        if base_ead_total > Decimal("0")
        else Decimal("0.00")
    )
    stressed_el_rate_pct = (
        quantize_pct((stressed_el_total / stressed_ead_total) * HUNDRED)
        if stressed_ead_total > Decimal("0")
        else Decimal("0.00")
    )
    base_npl_pct = (
        quantize_pct((base_npl_ead / base_ead_total) * HUNDRED)
        if base_ead_total > Decimal("0")
        else Decimal("0.00")
    )
    stressed_npl_pct = (
        quantize_pct((stressed_npl_ead / stressed_ead_total) * HUNDRED)
        if stressed_ead_total > Decimal("0")
        else Decimal("0.00")
    )
    delta_npl_bps = int(
        ((stressed_npl_pct - base_npl_pct) * HUNDRED).to_integral_value(
            rounding=ROUND_HALF_EVEN
        )
    )
    # Impacto estimado sobre colchón CET1 asumiendo capital regulatorio base de 12% sobre EAD
    cet1_base = base_ead_total * Decimal("0.12")
    capital_buffer_impact_pct = (
        quantize_pct((delta_el / cet1_base) * HUNDRED)
        if cet1_base > Decimal("0")
        else Decimal("0.00")
    )
    stressed_risk_level = classify_portfolio_risk(stressed_npl_pct, stressed_el_rate_pct)

    sector_impacts: list[SectorStressImpact] = []
    for sector, data in sector_acc.items():
        b_el = quantize_money(data["base_el"])
        st_el = quantize_money(data["stressed_el"])
        d_el = quantize_money(st_el - b_el)
        d_el_pct = quantize_pct((d_el / b_el) * HUNDRED) if b_el > Decimal("0") else Decimal("0.00")
        st_npl_pct = (
            quantize_pct((data["stressed_npl_ead"] / data["stressed_ead"]) * HUNDRED)
            if data["stressed_ead"] > Decimal("0")
            else Decimal("0.00")
        )
        st_el_rate = (
            quantize_pct((st_el / data["stressed_ead"]) * HUNDRED)
            if data["stressed_ead"] > Decimal("0")
            else Decimal("0.00")
        )
        sector_impacts.append(
            SectorStressImpact(
                sector=sector,
                base_el=b_el,
                stressed_el=st_el,
                delta_el=d_el,
                delta_el_pct=d_el_pct,
                stressed_npl_pct=st_npl_pct,
                risk_level=classify_portfolio_risk(st_npl_pct, st_el_rate),
            )
        )
    sector_impacts.sort(key=lambda x: x.delta_el, reverse=True)

    scope_txt = f"sector {request.sector_filter}" if request.sector_filter else "toda la cartera corporativa"
    executive_conclusion = (
        f"Bajo el escenario '{request.name}' sobre {scope_txt} "
        f"(PD {request.pd_shock_pct:+.2f}%, LGD {request.lgd_shock_pp:+.2f} pp, FX LATAM {request.fx_depreciation_latam_pct:+.2f}%), "
        f"la pérdida esperada aumenta en {_format_compact_money(delta_el, reporting)} ({delta_el_pct:+.2f}%) "
        f"hasta {_format_compact_money(stressed_el_total, reporting)}, elevando el NPL en {delta_npl_bps:+d} pbs "
        f"(hasta {stressed_npl_pct:.2f}%) con un consumo estimado de {capital_buffer_impact_pct:.2f}% del colchón CET1."
    )

    return StressTestRecord(
        simulation_id=f"SIM-{uuid4().hex[:8].upper()}",
        name=request.name,
        created_at_utc=datetime.now(timezone.utc),
        executed_by=actor.email,
        executed_role=actor.role,
        reporting_currency=reporting,
        sector_filter=request.sector_filter,
        notes=request.notes,
        pd_shock_pct=quantize_pct(request.pd_shock_pct),
        lgd_shock_pp=quantize_pct(request.lgd_shock_pp),
        fx_depreciation_latam_pct=quantize_pct(request.fx_depreciation_latam_pct),
        fx_snapshot_base=fx_snapshot,
        fx_snapshot_stressed=stressed_fx,
        base_ead=base_ead_total,
        stressed_ead=stressed_ead_total,
        base_el=base_el_total,
        stressed_el=stressed_el_total,
        delta_el=delta_el,
        delta_el_pct=delta_el_pct,
        base_el_rate_pct=base_el_rate_pct,
        stressed_el_rate_pct=stressed_el_rate_pct,
        base_npl_pct=base_npl_pct,
        stressed_npl_pct=stressed_npl_pct,
        delta_npl_bps=delta_npl_bps,
        capital_buffer_impact_pct=capital_buffer_impact_pct,
        stressed_risk_level=stressed_risk_level,
        sector_impacts=sector_impacts,
        executive_conclusion=executive_conclusion,
    )
