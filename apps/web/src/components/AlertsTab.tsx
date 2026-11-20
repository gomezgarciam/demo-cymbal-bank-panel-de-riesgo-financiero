"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Lock } from "lucide-react";
import type {
  AlertStatus,
  AlertView,
  CurrencyCode,
  RiskLevel,
  UserRole,
} from "@/types/risk";
import {
  formatBps,
  formatMoney,
  formatUtcTimestamp,
} from "@/lib/formatters";
import { AlertStatusBadge, RiskBadge } from "@/components/RiskBadge";

interface AlertsTabProps {
  alerts: AlertView[];
  currency: CurrencyCode;
  role: UserRole;
  onUpdateStatus: (
    alertId: string,
    status: AlertStatus,
    note?: string
  ) => Promise<void>;
  onSwitchToAnalyst: () => void;
}

export function AlertsTab({
  alerts,
  currency,
  role,
  onUpdateStatus,
  onSwitchToAnalyst,
}: AlertsTabProps) {
  const [severityFilter, setSeverityFilter] = useState<RiskLevel | "">("");
  const [statusFilter, setStatusFilter] = useState<AlertStatus | "">("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return alerts.filter((a) => {
      if (severityFilter && a.severity !== severityFilter) return false;
      if (statusFilter && a.status !== statusFilter) return false;
      return true;
    });
  }, [alerts, severityFilter, statusFilter]);

  const isAnalyst = role === "risk_analyst";

  async function handleAction(alertId: string, nextStatus: AlertStatus) {
    setErrorMsg(null);
    setBusyId(alertId);
    try {
      await onUpdateStatus(alertId, nextStatus);
    } catch (err) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "No fue posible actualizar la alerta."
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="cb-page-header">
        <div>
          <h1 className="cb-h1">Alertas de Morosidad y Brechas de Umbral</h1>
          <p className="cb-lead">
            Monitoreo semafórico estricto (#0F9D58 / #F9AB00 / #D93025) con
            exposición actualizada en {currency} y registro de auditoría JSON.
          </p>
        </div>

        <div className="cb-toolbar">
          <select
            id="alerts-severity-select"
            className="cb-select"
            value={severityFilter}
            onChange={(e) =>
              setSeverityFilter(e.target.value as RiskLevel | "")
            }
            aria-label="Filtrar alertas por severidad"
          >
            <option value="">Todas las severidades</option>
            <option value="ALTO">Riesgo Alto</option>
            <option value="MEDIO">Riesgo Medio</option>
            <option value="BAJO">Riesgo Bajo</option>
          </select>
          <select
            id="alerts-status-select"
            className="cb-select"
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as AlertStatus | "")
            }
            aria-label="Filtrar alertas por estado"
          >
            <option value="">Todos los estados</option>
            <option value="ABIERTA">Abiertas</option>
            <option value="EN_REVISION">En revisión</option>
            <option value="MITIGADA">Mitigadas</option>
          </select>
        </div>
      </div>

      {!isAnalyst && (
        <div className="cb-notice warn">
          <Lock size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>Modo lectura (CFO):</strong> El cambio de estado de alertas
            está reservado al perfil <em>Analista de Riesgo</em> conforme a la
            política de segregación de funciones.{" "}
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
        <div className="cb-notice error">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          <span>{errorMsg}</span>
        </div>
      )}

      <section className="cb-alert-list" aria-label="Listado de alertas">
        {filtered.map((alert) => (
          <article
            key={alert.alert_id}
            className={`cb-alert-item severity-${alert.severity}`}
          >
            <div className="cb-alert-top">
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    flexWrap: "wrap",
                    marginBottom: 4,
                  }}
                >
                  <RiskBadge level={alert.severity} />
                  <AlertStatusBadge status={alert.status} />
                  <span className="cb-badge neutral numeric">
                    {alert.alert_id} · {alert.category}
                  </span>
                </div>
                <h2 className="cb-brief-headline">{alert.title}</h2>
                <span className="cb-table-secondary-cell">
                  {alert.client_name} ({alert.client_id}) · {alert.sector}
                </span>
              </div>

              <div className="numeric" style={{ textAlign: "right" }}>
                <div style={{ fontSize: 17, fontWeight: 700 }}>
                  {formatMoney(alert.exposure_reporting, currency)}
                </div>
                <span className="cb-table-secondary-cell">
                  Origen: {formatMoney(alert.exposure_origin, alert.origin_currency)}
                </span>
              </div>
            </div>

            <p className="cb-brief-body">{alert.description}</p>
            <p className="cb-brief-rec" style={{ borderTop: "none", paddingTop: 0 }}>
              Acción recomendada: {alert.recommendation}
            </p>

            <div className="cb-alert-actions">
              <div className="cb-alert-metrics numeric">
                <span>
                  Mora: <strong>{alert.days_past_due} días</strong>
                </span>
                <span>
                  Brecha umbral:{" "}
                  <strong
                    className={
                      alert.threshold_breach_bps > 0 ? "cb-delta-neg" : ""
                    }
                  >
                    {formatBps(alert.threshold_breach_bps)}
                  </strong>
                </span>
                <span>
                  Actualizado: {formatUtcTimestamp(alert.updated_at_utc)} por{" "}
                  {alert.updated_by}
                </span>
              </div>

              <div className="cb-toolbar">
                {alert.status !== "EN_REVISION" && (
                  <button
                    type="button"
                    className="cb-btn cb-btn-secondary cb-btn-sm"
                    disabled={busyId === alert.alert_id}
                    onClick={() => handleAction(alert.alert_id, "EN_REVISION")}
                  >
                    Pasar a En Revisión
                  </button>
                )}
                {alert.status !== "MITIGADA" && (
                  <button
                    type="button"
                    className="cb-btn cb-btn-primary cb-btn-sm"
                    disabled={busyId === alert.alert_id}
                    onClick={() => handleAction(alert.alert_id, "MITIGADA")}
                  >
                    Marcar Mitigada
                  </button>
                )}
                {alert.status === "MITIGADA" && (
                  <button
                    type="button"
                    className="cb-btn cb-btn-secondary cb-btn-sm"
                    disabled={busyId === alert.alert_id}
                    onClick={() => handleAction(alert.alert_id, "ABIERTA")}
                  >
                    Reabrir Alerta
                  </button>
                )}
              </div>
            </div>
          </article>
        ))}

        {filtered.length === 0 && (
          <div className="cb-panel cb-loading">
            No existen alertas con los filtros seleccionados.
          </div>
        )}
      </section>
    </>
  );
}
