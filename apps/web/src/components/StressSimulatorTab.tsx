"use client";

import { useState } from "react";
import { AlertTriangle, Lock, Play } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  CurrencyCode,
  StressTestRecord,
  StressTestRequest,
  UserRole,
} from "@/types/risk";
import {
  formatBps,
  formatCompactMoney,
  formatMoney,
  formatPct,
  formatUtcTimestamp,
  toNumeric,
} from "@/lib/formatters";
import { RiskBadge } from "@/components/RiskBadge";

interface StressSimulatorTabProps {
  simulations: StressTestRecord[];
  sectors: string[];
  currency: CurrencyCode;
  role: UserRole;
  onRunSimulation: (payload: StressTestRequest) => Promise<StressTestRecord>;
  onSwitchToAnalyst: () => void;
}

const PRESETS = [
  {
    label: "Alza de Tasas +150 pbs (Moderado)",
    meta: "PD +25% · LGD +3.0 pp · FX LATAM +8%",
    name: "Estrés Moderado — Alza de Tasas +150 pbs",
    pd: 25,
    lgd: 3,
    fx: 8,
  },
  {
    label: "Recesión Regional (Severo)",
    meta: "PD +75% · LGD +9.0 pp · FX LATAM +20%",
    name: "Estrés Severo — Recesión Regional y Deterioro Crediticio",
    pd: 75,
    lgd: 9,
    fx: 20,
  },
  {
    label: "Choque Cambiario MXN / COP (+25%)",
    meta: "PD +40% · LGD +5.0 pp · FX LATAM +25%",
    name: "Choque Cambiario LATAM — Depreciación 25%",
    pd: 40,
    lgd: 5,
    fx: 25,
  },
];

function StressTooltip({
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

export function StressSimulatorTab({
  simulations,
  sectors,
  currency,
  role,
  onRunSimulation,
  onSwitchToAnalyst,
}: StressSimulatorTabProps) {
  const [name, setName] = useState("Escenario Comité de Riesgo — Choque Mixto");
  const [pdShock, setPdShock] = useState<number>(45);
  const [lgdShock, setLgdShock] = useState<number>(6);
  const [fxShock, setFxShock] = useState<number>(15);
  const [sectorFilter, setSectorFilter] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(
    simulations[0]?.simulation_id ?? null
  );

  const activeSim =
    simulations.find((s) => s.simulation_id === selectedId) ??
    simulations[0] ??
    null;

  const isAnalyst = role === "risk_analyst";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    setSubmitting(true);
    try {
      const created = await onRunSimulation({
        name: name.trim() || "Escenario de Estrés Ad-Hoc",
        pd_shock_pct: pdShock.toFixed(2),
        lgd_shock_pp: lgdShock.toFixed(2),
        fx_depreciation_latam_pct: fxShock.toFixed(2),
        sector_filter: sectorFilter || null,
        reporting_currency: currency,
        notes: notes.trim() || null,
      });
      setSelectedId(created.simulation_id);
      setNotes("");
    } catch (err) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "No fue posible ejecutar la simulación."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const sectorChartData = (activeSim?.sector_impacts ?? []).map((item) => ({
    sector: item.sector,
    baseEl: toNumeric(item.base_el),
    stressedEl: toNumeric(item.stressed_el),
  }));

  return (
    <>
      <div className="cb-page-header">
        <div>
          <h1 className="cb-h1">Simulador de Estrés Crediticio y Cambiario</h1>
          <p className="cb-lead">
            Motor determinístico (EL = PD × LGD × EAD, NPL y FX LATAM) con
            aritmética Python Decimal y persistencia auditable.
          </p>
        </div>
        <div className="cb-meta-stamp numeric">
          <span>Moneda de simulación: <strong>{currency}</strong></span>
          <span>Simulaciones registradas: <strong>{simulations.length}</strong></span>
        </div>
      </div>

      <section className="cb-grid-simulator">
        {/* Formulario Paramétrico */}
        <div className="cb-panel">
          <div className="cb-panel-header">
            <div>
              <h2 className="cb-panel-title">Parámetros del Escenario</h2>
              <p className="cb-panel-subtitle">
                Ejecución restringida por RBAC a Analista de Riesgo
              </p>
            </div>
          </div>
          <div className="cb-panel-body">
            {!isAnalyst && (
              <div className="cb-notice warn" style={{ marginBottom: 14 }}>
                <Lock size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Perfil CFO en modo lectura ejecutiva.</strong> La
                  ejecución y persistencia de nuevas pruebas de estrés requiere
                  perfil <em>Analista de Riesgo</em>.{" "}
                  <button
                    type="button"
                    onClick={onSwitchToAnalyst}
                    style={{
                      border: "none",
                      background: "none",
                      padding: 0,
                      color: "var(--cb-primary)",
                      fontWeight: 600,
                      cursor: "pointer",
                      textDecoration: "underline",
                    }}
                  >
                    Cambiar a Analista de Riesgo
                  </button>
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="cb-notice error" style={{ marginBottom: 14 }}>
                <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="cb-field" style={{ marginBottom: 14 }}>
              <span className="cb-label">Escenarios institucionales rápidos</span>
              <div className="cb-preset-list">
                {PRESETS.map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    className="cb-preset-btn"
                    onClick={() => {
                      setName(preset.name);
                      setPdShock(preset.pd);
                      setLgdShock(preset.lgd);
                      setFxShock(preset.fx);
                    }}
                  >
                    <span className="cb-preset-title">{preset.label}</span>
                    <span className="cb-preset-meta numeric">{preset.meta}</span>
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSubmit} className="cb-form-stack">
              <div className="cb-field">
                <label htmlFor="sim-name" className="cb-label">
                  Nombre del escenario
                </label>
                <input
                  id="sim-name"
                  type="text"
                  className="cb-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  minLength={3}
                  maxLength={120}
                />
              </div>

              <div className="cb-field">
                <div className="cb-field-row">
                  <label htmlFor="sim-pd" className="cb-label">
                    Choque multiplicativo PD (%)
                  </label>
                  <span className="cb-range-value numeric">
                    {pdShock >= 0 ? `+${pdShock}%` : `${pdShock}%`}
                  </span>
                </div>
                <input
                  id="sim-pd"
                  type="range"
                  className="cb-range"
                  min={-30}
                  max={200}
                  step={5}
                  value={pdShock}
                  onChange={(e) => setPdShock(Number(e.target.value))}
                />
              </div>

              <div className="cb-field">
                <div className="cb-field-row">
                  <label htmlFor="sim-lgd" className="cb-label">
                    Choque aditivo LGD (pp)
                  </label>
                  <span className="cb-range-value numeric">
                    {lgdShock >= 0 ? `+${lgdShock.toFixed(1)} pp` : `${lgdShock.toFixed(1)} pp`}
                  </span>
                </div>
                <input
                  id="sim-lgd"
                  type="range"
                  className="cb-range"
                  min={-10}
                  max={35}
                  step={0.5}
                  value={lgdShock}
                  onChange={(e) => setLgdShock(Number(e.target.value))}
                />
              </div>

              <div className="cb-field">
                <div className="cb-field-row">
                  <label htmlFor="sim-fx" className="cb-label">
                    Depreciación FX LATAM (MXN / COP)
                  </label>
                  <span className="cb-range-value numeric">
                    {fxShock >= 0 ? `+${fxShock}%` : `${fxShock}%`}
                  </span>
                </div>
                <input
                  id="sim-fx"
                  type="range"
                  className="cb-range"
                  min={-15}
                  max={45}
                  step={1}
                  value={fxShock}
                  onChange={(e) => setFxShock(Number(e.target.value))}
                />
              </div>

              <div className="cb-field">
                <label htmlFor="sim-sector" className="cb-label">
                  Alcance sectorial
                </label>
                <select
                  id="sim-sector"
                  className="cb-select"
                  value={sectorFilter}
                  onChange={(e) => setSectorFilter(e.target.value)}
                >
                  <option value="">Toda la cartera corporativa</option>
                  {sectors.map((s) => (
                    <option key={s} value={s}>
                      Solo {s}
                    </option>
                  ))}
                </select>
              </div>

              <div className="cb-field">
                <label htmlFor="sim-notes" className="cb-label">
                  Supuesto metodológico / nota de comité (opcional)
                </label>
                <textarea
                  id="sim-notes"
                  className="cb-textarea"
                  rows={2}
                  placeholder="Ej. Sensibilidad ante recorte de liquidez regional..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <button
                id="btn-run-stress-test"
                type="submit"
                className="cb-btn cb-btn-primary"
                disabled={submitting}
              >
                <Play size={14} aria-hidden="true" />
                {submitting
                  ? "Calculando escenario..."
                  : isAnalyst
                    ? `Ejecutar Simulación (${currency})`
                    : `Probar Guardia RBAC 403 (${currency})`}
              </button>
            </form>
          </div>
        </div>

        {/* Resultados Comparativos del Escenario Seleccionado */}
        <div className="cb-form-stack">
          {activeSim ? (
            <>
              <section
                className={`cb-executive-brief status-${activeSim.stressed_risk_level}`}
              >
                <div className="cb-brief-top">
                  <span className="cb-brief-eyebrow numeric">
                    {activeSim.simulation_id} · {formatUtcTimestamp(activeSim.created_at_utc)} ·{" "}
                    {activeSim.executed_by}
                  </span>
                  <RiskBadge level={activeSim.stressed_risk_level} />
                </div>
                <h2 className="cb-brief-headline">{activeSim.name}</h2>
                <p className="cb-brief-body numeric">
                  {activeSim.executive_conclusion}
                </p>
              </section>

              <div className="cb-kpi-grid" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
                <div className="cb-kpi-card">
                  <span className="cb-kpi-label">EL Estresada</span>
                  <div className="cb-kpi-value numeric">
                    {formatCompactMoney(
                      activeSim.stressed_el,
                      activeSim.reporting_currency
                    )}
                  </div>
                  <div className="cb-kpi-sub numeric">
                    <span>
                      Base:{" "}
                      {formatCompactMoney(
                        activeSim.base_el,
                        activeSim.reporting_currency
                      )}
                    </span>
                    <span className="cb-delta-neg">
                      {formatPct(activeSim.delta_el_pct, true)}
                    </span>
                  </div>
                </div>

                <div className="cb-kpi-card">
                  <span className="cb-kpi-label">NPL Estresado</span>
                  <div className="cb-kpi-value numeric">
                    {formatPct(activeSim.stressed_npl_pct)}
                  </div>
                  <div className="cb-kpi-sub numeric">
                    <span>Base: {formatPct(activeSim.base_npl_pct)}</span>
                    <span
                      className={
                        activeSim.delta_npl_bps > 0 ? "cb-delta-neg" : "cb-delta-pos"
                      }
                    >
                      {formatBps(activeSim.delta_npl_bps)}
                    </span>
                  </div>
                </div>

                <div className="cb-kpi-card">
                  <span className="cb-kpi-label">Consumo Colchón CET1</span>
                  <div className="cb-kpi-value numeric">
                    {formatPct(activeSim.capital_buffer_impact_pct)}
                  </div>
                  <div className="cb-kpi-sub numeric">
                    <span>
                      Delta EL:{" "}
                      {formatCompactMoney(
                        activeSim.delta_el,
                        activeSim.reporting_currency
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="cb-panel">
                <div className="cb-panel-header">
                  <div>
                    <h2 className="cb-panel-title">
                      Comparativa Sectorial: Pérdida Esperada Base vs. Estresada
                    </h2>
                    <p className="cb-panel-subtitle">
                      Impacto exacto en {activeSim.reporting_currency} por sector
                      económico
                    </p>
                  </div>
                </div>
                <div className="cb-panel-body">
                  <div className="cb-chart-box" style={{ height: 270 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={sectorChartData}
                        margin={{ top: 8, right: 16, left: 10, bottom: 20 }}
                      >
                        <CartesianGrid
                          stroke="var(--chart-grid)"
                          strokeDasharray="3 3"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="sector"
                          tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                          interval={0}
                          angle={-12}
                          textAnchor="end"
                          height={46}
                        />
                        <YAxis
                          tickFormatter={(v: number) =>
                            formatCompactMoney(v, activeSim.reporting_currency)
                          }
                          tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          width={94}
                        />
                        <Tooltip
                          content={
                            <StressTooltip
                              currency={activeSim.reporting_currency}
                            />
                          }
                        />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        <Bar
                          dataKey="baseEl"
                          name="EL Base"
                          fill="#1A73E8"
                          radius={[4, 4, 0, 0]}
                        />
                        <Bar
                          dataKey="stressedEl"
                          name="EL Estresada"
                          fill="#D93025"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="cb-panel cb-loading">
              No existen simulaciones registradas aún.
            </div>
          )}

          {/* Historial Auditable de Simulaciones */}
          <div className="cb-panel">
            <div className="cb-panel-header">
              <div>
                <h2 className="cb-panel-title">
                  Historial Auditable de Simulaciones
                </h2>
                <p className="cb-panel-subtitle">
                  Seleccione cualquier registro para inspeccionar su impacto
                  sectorial y snapshot FX
                </p>
              </div>
            </div>
            <div className="cb-table-wrap">
              <table className="cb-table">
                <thead>
                  <tr>
                    <th>ID / Escenario</th>
                    <th>Choques (PD / LGD / FX)</th>
                    <th className="numeric">Delta EL</th>
                    <th className="numeric">NPL Estresado</th>
                    <th>Severidad</th>
                  </tr>
                </thead>
                <tbody>
                  {simulations.map((sim) => {
                    const isSelected = sim.simulation_id === activeSim?.simulation_id;
                    return (
                      <tr
                        key={sim.simulation_id}
                        onClick={() => setSelectedId(sim.simulation_id)}
                        style={{
                          cursor: "pointer",
                          backgroundColor: isSelected
                            ? "var(--cb-primary-soft)"
                            : undefined,
                        }}
                      >
                        <td>
                          <span className="cb-table-primary-cell">
                            {sim.name}
                          </span>
                          <span className="cb-table-secondary-cell numeric">
                            {sim.simulation_id} · {sim.reporting_currency} ·{" "}
                            {formatUtcTimestamp(sim.created_at_utc)}
                          </span>
                        </td>
                        <td className="numeric">
                          PD {formatPct(sim.pd_shock_pct, true)} · LGD +
                          {sim.lgd_shock_pp} pp · FX{" "}
                          {formatPct(sim.fx_depreciation_latam_pct, true)}
                        </td>
                        <td className="numeric cb-delta-neg">
                          +{formatCompactMoney(sim.delta_el, sim.reporting_currency)}{" "}
                          ({formatPct(sim.delta_el_pct, true)})
                        </td>
                        <td className="numeric" style={{ fontWeight: 600 }}>
                          {formatPct(sim.stressed_npl_pct)} (
                          {formatBps(sim.delta_npl_bps)})
                        </td>
                        <td>
                          <RiskBadge level={sim.stressed_risk_level} compact />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
