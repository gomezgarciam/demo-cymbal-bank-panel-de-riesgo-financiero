"use client";

import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  AlertView,
  CurrencyCode,
  PortfolioSummaryResponse,
} from "@/types/risk";
import {
  formatBps,
  formatCompactMoney,
  formatMoney,
  formatPct,
  formatUtcTimestamp,
  toNumeric,
} from "@/lib/formatters";
import { AlertStatusBadge, RiskBadge } from "@/components/RiskBadge";

interface OverviewTabProps {
  summary: PortfolioSummaryResponse;
  alerts: AlertView[];
  currency: CurrencyCode;
  onNavigateTab: (tab: "clients" | "simulator" | "alerts") => void;
}

function TrendTooltip({
  active,
  payload,
  label,
  currency,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number; color?: string; dataKey?: string }>;
  label?: string;
  currency: CurrencyCode;
}) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      style={{
        background: "var(--chart-tooltip-bg)",
        border: "1px solid var(--chart-tooltip-border)",
        borderRadius: 8,
        padding: "10px 12px",
        boxShadow: "var(--shadow-raised)",
        fontSize: 12,
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6, color: "var(--ink-primary)" }}>
        Corte {label}
      </div>
      {payload.map((entry) => (
        <div
          key={entry.dataKey}
          className="numeric"
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 16,
            marginBottom: 3,
            color: "var(--ink-secondary)",
          }}
        >
          <span>{entry.name}:</span>
          <strong style={{ color: "var(--ink-primary)" }}>
            {entry.dataKey === "nplPct"
              ? `${Number(entry.value ?? 0).toFixed(2)}%`
              : formatCompactMoney(Number(entry.value ?? 0), currency)}
          </strong>
        </div>
      ))}
    </div>
  );
}

function SectorTooltip({
  active,
  payload,
  label,
  currency,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number; dataKey?: string }>;
  label?: string;
  currency: CurrencyCode;
}) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      style={{
        background: "var(--chart-tooltip-bg)",
        border: "1px solid var(--chart-tooltip-border)",
        borderRadius: 8,
        padding: "10px 12px",
        boxShadow: "var(--shadow-raised)",
        fontSize: 12,
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6, color: "var(--ink-primary)" }}>
        {label}
      </div>
      {payload.map((entry) => (
        <div
          key={entry.dataKey}
          className="numeric"
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 16,
            marginBottom: 3,
            color: "var(--ink-secondary)",
          }}
        >
          <span>{entry.name}:</span>
          <strong style={{ color: "var(--ink-primary)" }}>
            {formatMoney(Number(entry.value ?? 0), currency)}
          </strong>
        </div>
      ))}
    </div>
  );
}

const SECTOR_RISK_COLOR = {
  BAJO: "#0F9D58",
  MEDIO: "#F9AB00",
  ALTO: "#D93025",
} as const;

export function OverviewTab({
  summary,
  alerts,
  currency,
  onNavigateTab,
}: OverviewTabProps) {
  const trendData = summary.monthly_trend.map((pt) => ({
    period: pt.period,
    ead: toNumeric(pt.ead),
    el: toNumeric(pt.expected_loss),
    nplPct: toNumeric(pt.npl_ratio_pct),
  }));

  const sectorData = summary.sector_exposures.map((s) => ({
    sector: s.sector,
    ead: toNumeric(s.ead),
    el: toNumeric(s.expected_loss),
    risk: s.risk_level,
  }));

  const priorityAlerts = alerts
    .filter((a) => a.status !== "MITIGADA")
    .slice(0, 4);

  return (
    <>
      <div className="cb-page-header">
        <div>
          <h1 className="cb-h1">Resumen Ejecutivo de Riesgo Crediticio</h1>
          <p className="cb-lead">
            Consolidado corporativo multimoneda ({currency}) con cálculo exacto
            Python Decimal y trazabilidad FX.
          </p>
        </div>
        <div className="cb-meta-stamp numeric">
          <span>Corte: {formatUtcTimestamp(summary.as_of_utc)}</span>
          <button
            type="button"
            className="cb-btn cb-btn-primary cb-btn-sm"
            onClick={() => onNavigateTab("simulator")}
          >
            Abrir Simulador de Estrés
          </button>
        </div>
      </div>

      {/* Banner Conclusión Primero — Estándar de comunicación CFO */}
      <section
        className={`cb-executive-brief status-${summary.executive_insight.overall_status}`}
        aria-label="Conclusión ejecutiva para CFO"
      >
        <div className="cb-brief-top">
          <span className="cb-brief-eyebrow">
            Síntesis Ejecutiva · Conclusión Primero (Comité CFO)
          </span>
          <RiskBadge level={summary.executive_insight.overall_status} />
        </div>
        <h2 className="cb-brief-headline numeric">
          {summary.executive_insight.headline}
        </h2>
        <p className="cb-brief-body numeric">
          {summary.executive_insight.summary}
        </p>
        <p className="cb-brief-rec">
          {summary.executive_insight.recommendation}
        </p>
      </section>

      {/* 4 Tarjetas KPI Institucionales */}
      <section className="cb-kpi-grid" aria-label="Indicadores clave de riesgo">
        <article className="cb-kpi-card">
          <div className="cb-kpi-header">
            <span className="cb-kpi-label">Exposición Total (EAD)</span>
            <span className="cb-badge primary numeric">
              {summary.total_clients} acreditados
            </span>
          </div>
          <div className="cb-kpi-value numeric">
            {formatCompactMoney(summary.total_ead, currency)}
          </div>
          <div className="cb-kpi-sub numeric">
            <span>{formatMoney(summary.total_ead, currency)}</span>
          </div>
        </article>

        <article className="cb-kpi-card">
          <div className="cb-kpi-header">
            <span className="cb-kpi-label">Pérdida Esperada (EL)</span>
            <RiskBadge
              level={
                summary.executive_insight.el_variance_bps > 0
                  ? "ALTO"
                  : summary.executive_insight.el_variance_bps > -50
                    ? "MEDIO"
                    : "BAJO"
              }
              compact
            />
          </div>
          <div className="cb-kpi-value numeric">
            {formatCompactMoney(summary.total_expected_loss, currency)}
          </div>
          <div className="cb-kpi-sub numeric">
            <span>Tasa EL: {formatPct(summary.el_rate_pct)}</span>
            <span
              className={
                summary.executive_insight.el_variance_bps > 0
                  ? "cb-delta-neg"
                  : "cb-delta-pos"
              }
            >
              {formatBps(summary.executive_insight.el_variance_bps)} vs. límite
            </span>
          </div>
        </article>

        <article className="cb-kpi-card">
          <div className="cb-kpi-header">
            <span className="cb-kpi-label">Índice de Morosidad (NPL)</span>
            <RiskBadge
              level={
                summary.executive_insight.npl_variance_bps > 0 ? "ALTO" : "BAJO"
              }
              compact
            />
          </div>
          <div className="cb-kpi-value numeric">
            {formatPct(summary.npl_ratio_pct)}
          </div>
          <div className="cb-kpi-sub numeric">
            <span>Cartera &gt;90d: {formatCompactMoney(summary.npl_ead, currency)}</span>
            <span
              className={
                summary.executive_insight.npl_variance_bps > 0
                  ? "cb-delta-neg"
                  : "cb-delta-pos"
              }
            >
              {formatBps(summary.executive_insight.npl_variance_bps)} vs.{" "}
              {formatPct(summary.npl_appetite_limit_pct)}
            </span>
          </div>
        </article>

        <article className="cb-kpi-card">
          <div className="cb-kpi-header">
            <span className="cb-kpi-label">Alertas Activas &amp; PD / LGD</span>
            <span className="cb-badge risk-ALTO numeric">
              {summary.alerts_summary.ALTO} críticas
            </span>
          </div>
          <div className="cb-kpi-value numeric">
            {summary.open_alerts_total} activas
          </div>
          <div className="cb-kpi-sub numeric">
            <span>
              PD prom.: {formatPct(summary.weighted_pd_pct)} · LGD prom.:{" "}
              {formatPct(summary.weighted_lgd_pct)}
            </span>
          </div>
        </article>
      </section>

      {/* Gráficas Financieras Recharts */}
      <section className="cb-grid-2" aria-label="Visualizaciones de cartera">
        <div className="cb-panel">
          <div className="cb-panel-header">
            <div>
              <h2 className="cb-panel-title">
                Evolución de Exposición (EAD) e Índice de Morosidad (NPL)
              </h2>
              <p className="cb-panel-subtitle">
                Serie histórica de 6 meses en {currency} frente a umbral interno
                NPL ({formatPct(summary.npl_appetite_limit_pct)})
              </p>
            </div>
          </div>
          <div className="cb-panel-body">
            <div className="cb-chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={trendData}
                  margin={{ top: 10, right: 16, left: 6, bottom: 4 }}
                >
                  <CartesianGrid
                    stroke="var(--chart-grid)"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="period"
                    tick={{ fill: "var(--chart-axis)", fontSize: 12 }}
                    axisLine={{ stroke: "var(--border-hairline)" }}
                    tickLine={false}
                  />
                  <YAxis
                    yAxisId="left"
                    tickFormatter={(v: number) => formatCompactMoney(v, currency)}
                    tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={92}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tickFormatter={(v: number) => `${v.toFixed(1)}%`}
                    tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={46}
                  />
                  <Tooltip content={<TrendTooltip currency={currency} />} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="ead"
                    name={`EAD (${currency})`}
                    fill="rgba(26, 115, 232, 0.14)"
                    stroke="#1A73E8"
                    strokeWidth={2}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="nplPct"
                    name="Índice NPL (%)"
                    stroke="#D93025"
                    strokeWidth={2.5}
                    dot={{ r: 3.5, fill: "#D93025" }}
                  />
                  <ReferenceLine
                    yAxisId="right"
                    y={toNumeric(summary.npl_appetite_limit_pct)}
                    stroke="#F9AB00"
                    strokeDasharray="5 4"
                    label={{
                      value: `Límite ${summary.npl_appetite_limit_pct}%`,
                      position: "insideTopRight",
                      fill: "var(--chart-axis)",
                      fontSize: 11,
                    }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="cb-panel">
          <div className="cb-panel-header">
            <div>
              <h2 className="cb-panel-title">
                Pérdida Esperada (EL) por Sector Económico
              </h2>
              <p className="cb-panel-subtitle">
                Color semafórico por nivel de riesgo sectorial ({currency})
              </p>
            </div>
          </div>
          <div className="cb-panel-body">
            <div className="cb-chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={sectorData}
                  layout="vertical"
                  margin={{ top: 6, right: 18, left: 10, bottom: 4 }}
                >
                  <CartesianGrid
                    stroke="var(--chart-grid)"
                    strokeDasharray="3 3"
                    horizontal={false}
                  />
                  <XAxis
                    type="number"
                    tickFormatter={(v: number) => formatCompactMoney(v, currency)}
                    tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                    axisLine={{ stroke: "var(--border-hairline)" }}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="sector"
                    width={142}
                    tick={{ fill: "var(--chart-axis)", fontSize: 11.5 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<SectorTooltip currency={currency} />} />
                  <Bar
                    dataKey="el"
                    name={`Pérdida Esperada (${currency})`}
                    radius={[0, 4, 4, 0]}
                    barSize={18}
                  >
                    {sectorData.map((entry) => (
                      <Cell
                        key={entry.sector}
                        fill={SECTOR_RISK_COLOR[entry.risk]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* Alertas Prioritarias + Composición por Divisa de Origen */}
      <section className="cb-grid-asymmetric">
        <div className="cb-panel">
          <div className="cb-panel-header">
            <div>
              <h2 className="cb-panel-title">Alertas Prioritarias de Morosidad</h2>
              <p className="cb-panel-subtitle">
                Exposiciones activas fuera de umbral convertidas a {currency}
              </p>
            </div>
            <button
              type="button"
              className="cb-btn cb-btn-secondary cb-btn-sm"
              onClick={() => onNavigateTab("alerts")}
            >
              Ver todas ({alerts.length})
            </button>
          </div>
          <div className="cb-table-wrap">
            <table className="cb-table">
              <thead>
                <tr>
                  <th>Acreditado</th>
                  <th>Severidad</th>
                  <th className="numeric">Mora</th>
                  <th className="numeric">Exposición ({currency})</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {priorityAlerts.map((alert) => (
                  <tr key={alert.alert_id}>
                    <td>
                      <span className="cb-table-primary-cell">
                        {alert.client_name}
                      </span>
                      <span className="cb-table-secondary-cell">
                        {alert.title}
                      </span>
                    </td>
                    <td>
                      <RiskBadge level={alert.severity} compact />
                    </td>
                    <td className="numeric">{alert.days_past_due} d</td>
                    <td className="numeric">
                      {formatMoney(alert.exposure_reporting, currency)}
                    </td>
                    <td>
                      <AlertStatusBadge status={alert.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="cb-panel">
          <div className="cb-panel-header">
            <div>
              <h2 className="cb-panel-title">Composición por Moneda de Origen</h2>
              <p className="cb-panel-subtitle">
                Exposición original consolidada en {currency}
              </p>
            </div>
            <button
              type="button"
              className="cb-btn cb-btn-secondary cb-btn-sm"
              onClick={() => onNavigateTab("clients")}
            >
              Ver cartera
            </button>
          </div>
          <div className="cb-panel-body">
            <div className="cb-form-stack">
              {summary.currency_breakdown.map((item) => (
                <div key={item.origin_currency} className="cb-field">
                  <div className="cb-field-row numeric">
                    <span className="cb-table-primary-cell">
                      {item.origin_currency}{" "}
                      <span style={{ fontWeight: 400, color: "var(--ink-muted)" }}>
                        ({item.client_count} líneas)
                      </span>
                    </span>
                    <span style={{ fontWeight: 600 }}>
                      {formatCompactMoney(item.ead_in_reporting, currency)} ·{" "}
                      {formatPct(item.share_pct)}
                    </span>
                  </div>
                  <div className="cb-bar-track">
                    <div
                      className="cb-bar-fill"
                      style={{ width: `${Math.min(100, toNumeric(item.share_pct))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
