"use client";

import { useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import type {
  AuditEvent,
  CurrencyCode,
  FxRatesSnapshot,
  UserRole,
} from "@/types/risk";
import { formatRate, formatUtcTimestamp } from "@/lib/formatters";

interface AuditFxTabProps {
  fxSnapshot: FxRatesSnapshot | null;
  auditEvents: AuditEvent[];
  role: UserRole;
  onRefreshFx: () => Promise<void>;
  onRefreshAudit: () => Promise<void>;
}

const CURRENCY_NAMES: Record<CurrencyCode, string> = {
  USD: "Dólar Estadounidense (Base)",
  EUR: "Euro (Zona Euro)",
  MXN: "Peso Mexicano",
  COP: "Peso Colombiano",
};

export function AuditFxTab({
  fxSnapshot,
  auditEvents,
  role,
  onRefreshFx,
  onRefreshAudit,
}: AuditFxTabProps) {
  const [refreshingFx, setRefreshingFx] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleFxSync() {
    setErrorMsg(null);
    setRefreshingFx(true);
    try {
      await onRefreshFx();
    } catch (err) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "No fue posible sincronizar las tasas FX."
      );
    } finally {
      setRefreshingFx(false);
    }
  }

  return (
    <>
      <div className="cb-page-header">
        <div>
          <h1 className="cb-h1">Observabilidad, Tasas FX y Auditoría Bancaria</h1>
          <p className="cb-lead">
            Trazabilidad inmutable en JSON (Cloud Logging) y tasas oficiales de
            cambio alimentadas por Cloud Scheduler + FX.
          </p>
        </div>
        <div className="cb-toolbar">
          <button
            type="button"
            className="cb-btn cb-btn-secondary cb-btn-sm"
            onClick={() => void onRefreshAudit()}
          >
            <RefreshCw size={14} aria-hidden="true" />
            Recargar Logs
          </button>
          <button
            id="btn-refresh-fx"
            type="button"
            className="cb-btn cb-btn-primary cb-btn-sm"
            disabled={refreshingFx}
            onClick={() => void handleFxSync()}
          >
            <RefreshCw size={14} aria-hidden="true" />
            {refreshingFx
              ? "Sincronizando FX..."
              : role === "risk_analyst"
                ? "Ejecutar Job FX (Cloud Scheduler)"
                : "Probar Guardia RBAC FX"}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="cb-notice error">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Matriz de Tasas FX */}
      {fxSnapshot && (
        <section className="cb-panel">
          <div className="cb-panel-header">
            <div>
              <h2 className="cb-panel-title">
                Snapshot Multimoneda FX Vigente (Base 1 USD)
              </h2>
              <p className="cb-panel-subtitle numeric">
                Fuente: {fxSnapshot.source} · Último corte:{" "}
                {formatUtcTimestamp(fxSnapshot.as_of_utc)}
              </p>
            </div>
            <span className="cb-badge risk-BAJO">Precisión 6 decimales · ROUND_HALF_EVEN</span>
          </div>
          <div className="cb-table-wrap">
            <table className="cb-table">
              <thead>
                <tr>
                  <th>Divisa (ISO 4217)</th>
                  <th>Descripción</th>
                  <th className="numeric">Unidades por 1 USD</th>
                  <th className="numeric">Equivalente en USD (1 unidad)</th>
                </tr>
              </thead>
              <tbody>
                {(["USD", "EUR", "MXN", "COP"] as CurrencyCode[]).map((code) => {
                  const rate = Number(fxSnapshot.rates[code]);
                  const inverse = rate > 0 ? 1 / rate : 0;
                  return (
                    <tr key={code}>
                      <td>
                        <span className="cb-badge primary numeric">{code}</span>
                      </td>
                      <td>{CURRENCY_NAMES[code]}</td>
                      <td className="numeric" style={{ fontWeight: 600 }}>
                        {formatRate(fxSnapshot.rates[code])} {code}
                      </td>
                      <td className="numeric">
                        USD {inverse.toFixed(6)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Flujo de Auditoría JSON (Cloud Logging) */}
      <section className="cb-panel">
        <div className="cb-panel-header">
          <div>
            <h2 className="cb-panel-title">
              Registro de Auditoría Inmutable JSON (Cloud Logging)
            </h2>
            <p className="cb-panel-subtitle">
              Cada consulta ejecutiva, simulación de estrés, actualización de
              alerta o denegación RBAC queda registrada en formato JSON
              estructurado.
            </p>
          </div>
          <span className="cb-badge neutral numeric">
            {auditEvents.length} eventos recientes
          </span>
        </div>

        <div className="cb-table-wrap">
          <table className="cb-table">
            <thead>
              <tr>
                <th>Timestamp UTC</th>
                <th>Acción</th>
                <th>Actor / Rol</th>
                <th>Endpoint</th>
                <th className="numeric">HTTP</th>
                <th className="numeric">Latencia</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              {auditEvents.map((ev) => {
                const isExpanded = expandedId === ev.event_id;
                return (
                  <tr key={ev.event_id}>
                    <td className="numeric" style={{ whiteSpace: "nowrap" }}>
                      {formatUtcTimestamp(ev.timestamp_utc)}
                    </td>
                    <td>
                      <span
                        className={`cb-badge ${
                          ev.outcome === "DENIED"
                            ? "risk-ALTO"
                            : ev.action === "STRESS_TEST_EXECUTED"
                              ? "primary"
                              : "risk-BAJO"
                        }`}
                      >
                        {ev.action}
                      </span>
                    </td>
                    <td>
                      <span className="cb-table-primary-cell">
                        {ev.actor_email}
                      </span>
                      <span className="cb-table-secondary-cell">
                        Rol: {ev.actor_role}
                      </span>
                    </td>
                    <td className="numeric">
                      {ev.http_method} {ev.path}
                    </td>
                    <td className="numeric" style={{ fontWeight: 600 }}>
                      {ev.status_code}
                    </td>
                    <td className="numeric">{ev.latency_ms} ms</td>
                    <td>
                      <button
                        type="button"
                        className="cb-btn cb-btn-secondary cb-btn-sm"
                        onClick={() =>
                          setExpandedId(isExpanded ? null : ev.event_id)
                        }
                      >
                        {isExpanded ? "Ocultar JSON" : "Ver JSON"}
                      </button>
                      {isExpanded && (
                        <pre className="cb-json-pre">
                          {JSON.stringify(ev, null, 2)}
                        </pre>
                      )}
                    </td>
                  </tr>
                );
              })}
              {auditEvents.length === 0 && (
                <tr>
                  <td colSpan={7} className="cb-loading">
                    Aún no hay eventos de auditoría en la sesión actual.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
