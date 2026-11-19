export type CurrencyCode = "USD" | "EUR" | "MXN" | "COP";
export type UserRole = "cfo" | "risk_analyst";
export type RiskLevel = "BAJO" | "MEDIO" | "ALTO";
export type AlertStatus = "ABIERTA" | "EN_REVISION" | "MITIGADA";

export interface FxRatesSnapshot {
  base_currency: CurrencyCode;
  rates: Record<CurrencyCode, string>;
  as_of_utc: string;
  source: string;
}

export interface ClientPortfolioView {
  client_id: string;
  name: string;
  country: string;
  sector: string;
  credit_rating: string;
  facility_type: string;
  origin_currency: CurrencyCode;
  reporting_currency: CurrencyCode;
  fx_rate_applied: string;
  ead_origin: string;
  ead: string;
  pd_pct: string;
  lgd_pct: string;
  expected_loss: string;
  el_rate_pct: string;
  days_past_due: number;
  is_npl: boolean;
  risk_level: RiskLevel;
  maturity_date: string;
  last_review_date: string;
}

export interface SectorExposure {
  sector: string;
  client_count: number;
  ead: string;
  expected_loss: string;
  el_rate_pct: string;
  npl_ratio_pct: string;
  share_of_portfolio_pct: string;
  risk_level: RiskLevel;
}

export interface CurrencyBreakdown {
  origin_currency: CurrencyCode;
  ead_in_reporting: string;
  share_pct: string;
  client_count: number;
}

export interface MonthlyRiskPoint {
  period: string;
  ead: string;
  expected_loss: string;
  npl_ratio_pct: string;
  el_rate_pct: string;
}

export interface ExecutiveInsight {
  headline: string;
  summary: string;
  recommendation: string;
  overall_status: RiskLevel;
  npl_variance_bps: number;
  el_variance_bps: number;
}

export interface PortfolioSummaryResponse {
  reporting_currency: CurrencyCode;
  as_of_utc: string;
  fx_snapshot: FxRatesSnapshot;
  total_clients: number;
  total_ead: string;
  total_expected_loss: string;
  el_rate_pct: string;
  el_appetite_limit_pct: string;
  npl_ead: string;
  npl_ratio_pct: string;
  npl_appetite_limit_pct: string;
  weighted_pd_pct: string;
  weighted_lgd_pct: string;
  risk_distribution: Record<RiskLevel, number>;
  alerts_summary: Record<RiskLevel, number>;
  open_alerts_total: number;
  sector_exposures: SectorExposure[];
  currency_breakdown: CurrencyBreakdown[];
  monthly_trend: MonthlyRiskPoint[];
  executive_insight: ExecutiveInsight;
}

export interface StressTestRequest {
  name: string;
  pd_shock_pct: string;
  lgd_shock_pp: string;
  fx_depreciation_latam_pct: string;
  sector_filter: string | null;
  reporting_currency: CurrencyCode;
  notes?: string | null;
}

export interface SectorStressImpact {
  sector: string;
  base_el: string;
  stressed_el: string;
  delta_el: string;
  delta_el_pct: string;
  stressed_npl_pct: string;
  risk_level: RiskLevel;
}

export interface StressTestRecord {
  simulation_id: string;
  name: string;
  created_at_utc: string;
  executed_by: string;
  executed_role: UserRole;
  reporting_currency: CurrencyCode;
  sector_filter: string | null;
  notes: string | null;
  pd_shock_pct: string;
  lgd_shock_pp: string;
  fx_depreciation_latam_pct: string;
  fx_snapshot_base: FxRatesSnapshot;
  fx_snapshot_stressed: FxRatesSnapshot;
  base_ead: string;
  stressed_ead: string;
  base_el: string;
  stressed_el: string;
  delta_el: string;
  delta_el_pct: string;
  base_el_rate_pct: string;
  stressed_el_rate_pct: string;
  base_npl_pct: string;
  stressed_npl_pct: string;
  delta_npl_bps: number;
  capital_buffer_impact_pct: string;
  stressed_risk_level: RiskLevel;
  sector_impacts: SectorStressImpact[];
  executive_conclusion: string;
}

export interface AlertView {
  alert_id: string;
  client_id: string;
  client_name: string;
  sector: string;
  category: string;
  title: string;
  description: string;
  recommendation: string;
  severity: RiskLevel;
  status: AlertStatus;
  origin_currency: CurrencyCode;
  exposure_origin: string;
  reporting_currency: CurrencyCode;
  exposure_reporting: string;
  fx_rate_applied: string;
  threshold_breach_bps: number;
  days_past_due: number;
  created_at_utc: string;
  updated_at_utc: string;
  updated_by: string;
}

export interface AuditEvent {
  event_id: string;
  timestamp_utc: string;
  severity: string;
  service: string;
  action: string;
  actor_email: string;
  actor_role: string;
  http_method: string;
  path: string;
  status_code: number;
  latency_ms: string;
  currency: string | null;
  resource_id: string | null;
  outcome: string;
  details: Record<string, unknown>;
}
