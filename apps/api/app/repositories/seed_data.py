"""Datos institucionales iniciales para el MVP de Cymbal Bank (Banca Corporativa)."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.domain.models import (
    AlertRecord,
    AlertStatus,
    ClientPortfolioRecord,
    CurrencyCode,
    FxRatesSnapshot,
    RiskLevel,
)


def build_initial_fx_snapshot() -> FxRatesSnapshot:
    return FxRatesSnapshot(
        base_currency=CurrencyCode.USD,
        rates={
            CurrencyCode.USD: Decimal("1.000000"),
            CurrencyCode.EUR: Decimal("0.921500"),
            CurrencyCode.MXN: Decimal("19.850000"),
            CurrencyCode.COP: Decimal("4285.000000"),
        },
        as_of_utc=datetime.now(timezone.utc).replace(second=0, microsecond=0),
        source="Cloud Scheduler + FX (Corte Oficial Cymbal Bank)",
    )


def build_initial_clients() -> list[ClientPortfolioRecord]:
    """Cartera corporativa multimoneda realista (12 acreditados en USD, EUR, MXN, COP)."""
    return [
        ClientPortfolioRecord(
            client_id="CB-CORP-001",
            name="Andina Energía y Renovables S.A.",
            country="Colombia",
            sector="Energía y Renovables",
            credit_rating="BBB+",
            facility_type="Crédito Sindicado Proyecto Solar",
            origin_currency=CurrencyCode.COP,
            ead_origin=Decimal("98500000000.00"),  # ~22.99M USD
            pd=Decimal("0.0185"),
            lgd=Decimal("0.3500"),
            days_past_due=0,
            maturity_date=date(2029, 6, 30),
            last_review_date=date(2026, 10, 28),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-002",
            name="Grupo Industrial Regiomontano S.A.B.",
            country="México",
            sector="Manufactura Industrial",
            credit_rating="BBB",
            facility_type="Línea Revolvente Capital de Trabajo",
            origin_currency=CurrencyCode.MXN,
            ead_origin=Decimal("640000000.00"),  # ~32.24M USD
            pd=Decimal("0.0240"),
            lgd=Decimal("0.4200"),
            days_past_due=12,
            maturity_date=date(2028, 3, 15),
            last_review_date=date(2026, 11, 4),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-003",
            name="Iberia Logística y Puertos S.L.",
            country="España",
            sector="Logística y Puertos",
            credit_rating="A-",
            facility_type="Financiamiento Flota e Infraestructura",
            origin_currency=CurrencyCode.EUR,
            ead_origin=Decimal("26400000.00"),  # ~28.65M USD
            pd=Decimal("0.0110"),
            lgd=Decimal("0.3000"),
            days_past_due=0,
            maturity_date=date(2030, 9, 30),
            last_review_date=date(2026, 10, 19),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-004",
            name="Pacífico Agroexportadora Corp.",
            country="México",
            sector="Agroindustria",
            credit_rating="BB-",
            facility_type="Préstamo Estructurado Exportación",
            origin_currency=CurrencyCode.USD,
            ead_origin=Decimal("14800000.00"),
            pd=Decimal("0.0560"),
            lgd=Decimal("0.4800"),
            days_past_due=58,
            maturity_date=date(2027, 8, 20),
            last_review_date=date(2026, 11, 12),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-005",
            name="Constructora Vial del Caribe S.A.S.",
            country="Colombia",
            sector="Infraestructura",
            credit_rating="B+",
            facility_type="Crédito Puente Concesión Vial",
            origin_currency=CurrencyCode.COP,
            ead_origin=Decimal("41200000000.00"),  # ~9.61M USD (NPL > 90d)
            pd=Decimal("0.1450"),
            lgd=Decimal("0.5500"),
            days_past_due=118,
            maturity_date=date(2027, 4, 15),
            last_review_date=date(2026, 11, 15),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-006",
            name="Meridian Cloud & Telecom Inc.",
            country="Estados Unidos",
            sector="Telecomunicaciones",
            credit_rating="A",
            facility_type="Préstamo a Plazo Senior Garantizado",
            origin_currency=CurrencyCode.USD,
            ead_origin=Decimal("42500000.00"),
            pd=Decimal("0.0095"),
            lgd=Decimal("0.3200"),
            days_past_due=0,
            maturity_date=date(2031, 1, 31),
            last_review_date=date(2026, 11, 1),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-007",
            name="Almacenes Centrales del Sur S.A.",
            country="México",
            sector="Retail Corporativo",
            credit_rating="BB",
            facility_type="Línea de Liquidez Corporativa",
            origin_currency=CurrencyCode.MXN,
            ead_origin=Decimal("315000000.00"),  # ~15.87M USD
            pd=Decimal("0.0440"),
            lgd=Decimal("0.4500"),
            days_past_due=41,
            maturity_date=date(2027, 12, 10),
            last_review_date=date(2026, 11, 10),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-008",
            name="Nordic MedTech Solutions GmbH",
            country="Alemania",
            sector="Tecnología Empresarial",
            credit_rating="A-",
            facility_type="Facilidad Expansión Capex",
            origin_currency=CurrencyCode.EUR,
            ead_origin=Decimal("18900000.00"),  # ~20.51M USD
            pd=Decimal("0.0130"),
            lgd=Decimal("0.3500"),
            days_past_due=0,
            maturity_date=date(2029, 11, 30),
            last_review_date=date(2026, 10, 22),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-009",
            name="Naviera Transcontinental S.A.",
            country="Estados Unidos",
            sector="Logística y Puertos",
            credit_rating="B",
            facility_type="Crédito Arrendamiento Marítimo",
            origin_currency=CurrencyCode.USD,
            ead_origin=Decimal("6400000.00"),  # NPL > 90d
            pd=Decimal("0.1680"),
            lgd=Decimal("0.5200"),
            days_past_due=104,
            maturity_date=date(2027, 2, 28),
            last_review_date=date(2026, 11, 16),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-010",
            name="Ecoparque Industrial Bogotá S.A.S.",
            country="Colombia",
            sector="Infraestructura",
            credit_rating="BBB-",
            facility_type="Financiamiento Parques Logísticos",
            origin_currency=CurrencyCode.COP,
            ead_origin=Decimal("76000000000.00"),  # ~17.74M USD
            pd=Decimal("0.0310"),
            lgd=Decimal("0.4000"),
            days_past_due=18,
            maturity_date=date(2028, 10, 15),
            last_review_date=date(2026, 11, 5),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-011",
            name="Solstice Petroquímica & Materiales S.A.",
            country="México",
            sector="Manufactura Industrial",
            credit_rating="BB+",
            facility_type="Crédito Sindicado Planta Bajío",
            origin_currency=CurrencyCode.USD,
            ead_origin=Decimal("24600000.00"),
            pd=Decimal("0.0385"),
            lgd=Decimal("0.4400"),
            days_past_due=34,
            maturity_date=date(2028, 7, 31),
            last_review_date=date(2026, 11, 11),
        ),
        ClientPortfolioRecord(
            client_id="CB-CORP-012",
            name="Energía Eólica Atlántica S.A.",
            country="España",
            sector="Energía y Renovables",
            credit_rating="A",
            facility_type="Bono Verde Privado Senior",
            origin_currency=CurrencyCode.EUR,
            ead_origin=Decimal("31200000.00"),  # ~33.86M USD
            pd=Decimal("0.0085"),
            lgd=Decimal("0.2800"),
            days_past_due=0,
            maturity_date=date(2032, 5, 31),
            last_review_date=date(2026, 10, 30),
        ),
    ]


def build_initial_alerts() -> list[AlertRecord]:
    now = datetime.now(timezone.utc)
    return [
        AlertRecord(
            alert_id="ALT-2026-001",
            client_id="CB-CORP-005",
            client_name="Constructora Vial del Caribe S.A.S.",
            sector="Infraestructura",
            category="Morosidad Crítica (NPL > 90d)",
            title="Incumplimiento de cuota de capital — 118 días de mora",
            description=(
                "La facilidad puente en COP registra 118 días de atraso tras retrasos en desembolsos "
                "de vigencias futuras. PD interna recalibrada a 14.50%."
            ),
            recommendation=(
                "Ejecutar comité extraordinario de recuperación, constituir provisión específica adicional "
                "y activar cobertura sobre garantías fiduciarias del peaje."
            ),
            severity=RiskLevel.ALTO,
            status=AlertStatus.ABIERTA,
            origin_currency=CurrencyCode.COP,
            exposure_origin=Decimal("41200000000.00"),
            threshold_breach_bps=420,
            days_past_due=118,
            created_at_utc=now - timedelta(days=4),
            updated_at_utc=now - timedelta(days=1),
            updated_by="sistema-monitoreo@cymbalbank.com",
        ),
        AlertRecord(
            alert_id="ALT-2026-002",
            client_id="CB-CORP-009",
            client_name="Naviera Transcontinental S.A.",
            sector="Logística y Puertos",
            category="Morosidad Crítica (NPL > 90d)",
            title="Covenant DSCR perforado y atraso de 104 días",
            description=(
                "La contracción en tarifas de flete transpacífico redujo el DSCR a 0.92x frente al mínimo "
                "contractual de 1.25x, elevando la severidad de pérdida estimada a 52.00%."
            ),
            recommendation=(
                "Restringir desembolsos adicionales y exigir aporte de colateral líquido por el 15% del saldo vigente."
            ),
            severity=RiskLevel.ALTO,
            status=AlertStatus.EN_REVISION,
            origin_currency=CurrencyCode.USD,
            exposure_origin=Decimal("6400000.00"),
            threshold_breach_bps=365,
            days_past_due=104,
            created_at_utc=now - timedelta(days=6),
            updated_at_utc=now - timedelta(hours=14),
            updated_by="analista.riesgo@cymbalbank.com",
        ),
        AlertRecord(
            alert_id="ALT-2026-003",
            client_id="CB-CORP-004",
            client_name="Pacífico Agroexportadora Corp.",
            sector="Agroindustria",
            category="Vigilancia Preventiva (30–89d)",
            title="Atraso de 58 días y sensibilidad cambiaria USD/MXN",
            description=(
                "Acreditado con ingresos parciales en MXN y obligación en USD presenta presión en flujo "
                "de caja operativo y mora preventiva de 58 días."
            ),
            recommendation=(
                "Contratar cobertura cambiaria (forward USD/MXN a 12 meses) y reperfilar amortización del 1T."
            ),
            severity=RiskLevel.MEDIO,
            status=AlertStatus.ABIERTA,
            origin_currency=CurrencyCode.USD,
            exposure_origin=Decimal("14800000.00"),
            threshold_breach_bps=185,
            days_past_due=58,
            created_at_utc=now - timedelta(days=3),
            updated_at_utc=now - timedelta(days=2),
            updated_by="sistema-monitoreo@cymbalbank.com",
        ),
        AlertRecord(
            alert_id="ALT-2026-004",
            client_id="CB-CORP-007",
            client_name="Almacenes Centrales del Sur S.A.",
            sector="Retail Corporativo",
            category="Vigilancia Preventiva (30–89d)",
            title="Compresión de margen EBITDA y 41 días de mora",
            description=(
                "Aumento en costo de fondeo local incrementó la relación Deuda Neta / EBITDA a 3.85x, "
                "cerca del límite de apetito sectorial de 4.00x."
            ),
            recommendation=(
                "Revisar línea revolvente en MXN y condicionar renovación a reducción de inventario ocioso."
            ),
            severity=RiskLevel.MEDIO,
            status=AlertStatus.ABIERTA,
            origin_currency=CurrencyCode.MXN,
            exposure_origin=Decimal("315000000.00"),
            threshold_breach_bps=110,
            days_past_due=41,
            created_at_utc=now - timedelta(days=2),
            updated_at_utc=now - timedelta(days=2),
            updated_by="sistema-monitoreo@cymbalbank.com",
        ),
        AlertRecord(
            alert_id="ALT-2026-005",
            client_id="CB-CORP-011",
            client_name="Solstice Petroquímica & Materiales S.A.",
            sector="Manufactura Industrial",
            category="Descalce Cambiario y Tasa Variable",
            title="Exposición USD sin cobertura integral — 34 días de atraso",
            description=(
                "El crédito sindicado en USD muestra demora administrativa de 34 días y alta sensibilidad "
                "ante depreciaciones superiores al 10% en el tipo de cambio MXN."
            ),
            recommendation=(
                "Validar programa de cobertura cambiaria corporativa antes del cierre de trimestre."
            ),
            severity=RiskLevel.MEDIO,
            status=AlertStatus.EN_REVISION,
            origin_currency=CurrencyCode.USD,
            exposure_origin=Decimal("24600000.00"),
            threshold_breach_bps=95,
            days_past_due=34,
            created_at_utc=now - timedelta(days=5),
            updated_at_utc=now - timedelta(hours=8),
            updated_by="analista.riesgo@cymbalbank.com",
        ),
        AlertRecord(
            alert_id="ALT-2026-006",
            client_id="CB-CORP-002",
            client_name="Grupo Industrial Regiomontano S.A.B.",
            sector="Manufactura Industrial",
            category="Monitoreo Rutinario",
            title="Actualización trimestral de estados financieros auditados",
            description=(
                "Atraso menor de 12 días subsanado en liquidación bancaria; razones de liquidez dentro de rango."
            ),
            recommendation="Mantener calificación BBB y continuar seguimiento trimestral ordinario.",
            severity=RiskLevel.BAJO,
            status=AlertStatus.MITIGADA,
            origin_currency=CurrencyCode.MXN,
            exposure_origin=Decimal("640000000.00"),
            threshold_breach_bps=0,
            days_past_due=12,
            created_at_utc=now - timedelta(days=10),
            updated_at_utc=now - timedelta(days=1),
            updated_by="analista.riesgo@cymbalbank.com",
        ),
    ]


def build_monthly_history_usd() -> list[dict[str, str]]:
    """Serie histórica de 6 meses (valores base en USD exactos como cadenas)."""
    return [
        {"period": "2026-06", "ead_usd": "261400000.00", "el_usd": "3785000.00", "npl_ratio_pct": "3.12"},
        {"period": "2026-07", "ead_usd": "264950000.00", "el_usd": "3910000.00", "npl_ratio_pct": "3.28"},
        {"period": "2026-08", "ead_usd": "268200000.00", "el_usd": "4140000.00", "npl_ratio_pct": "3.45"},
        {"period": "2026-09", "ead_usd": "270800000.00", "el_usd": "4420000.00", "npl_ratio_pct": "4.85"},
        {"period": "2026-10", "ead_usd": "273100000.00", "el_usd": "4655000.00", "npl_ratio_pct": "5.42"},
        {"period": "2026-11", "ead_usd": "275210000.00", "el_usd": "4890000.00", "npl_ratio_pct": "5.82"},
    ]
