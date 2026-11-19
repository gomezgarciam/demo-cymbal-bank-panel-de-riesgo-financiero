"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import type {
  AlertStatus,
  AlertView,
  AuditEvent,
  ClientPortfolioView,
  CurrencyCode,
  PortfolioSummaryResponse,
  StressTestRecord,
  StressTestRequest,
  UserRole,
} from "@/types/risk";
import {
  executeStressTest,
  fetchAlerts,
  fetchAuditEvents,
  fetchClients,
  fetchPortfolioSummary,
  fetchStressTests,
  refreshFxRates,
  updateAlertStatus,
} from "@/lib/api";
import { TopBar, type NavTabId } from "@/components/TopBar";
import { OverviewTab } from "@/components/OverviewTab";
import { ClientsTab } from "@/components/ClientsTab";
import { StressSimulatorTab } from "@/components/StressSimulatorTab";
import { AlertsTab } from "@/components/AlertsTab";
import { AuditFxTab } from "@/components/AuditFxTab";

export function RiskDashboardApp() {
  const [currency, setCurrency] = useState<CurrencyCode>("USD");
  const [role, setRole] = useState<UserRole>("cfo");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [activeTab, setActiveTab] = useState<NavTabId>("overview");

  const [summary, setSummary] = useState<PortfolioSummaryResponse | null>(null);
  const [clients, setClients] = useState<ClientPortfolioView[]>([]);
  const [alerts, setAlerts] = useState<AlertView[]>([]);
  const [simulations, setSimulations] = useState<StressTestRecord[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastLatencyMs, setLastLatencyMs] = useState<number | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const fetchAllWorkspaceData = useCallback(
    async (targetCurrency: CurrencyCode, targetRole: UserRole) => {
      const [summaryRes, clientsRes, alertsRes, simsRes, auditRes] =
        await Promise.all([
          fetchPortfolioSummary(targetCurrency, targetRole),
          fetchClients(targetCurrency, targetRole),
          fetchAlerts(targetCurrency, targetRole),
          fetchStressTests(targetRole),
          fetchAuditEvents(targetRole),
        ]);
      return {
        summary: summaryRes.data,
        clients: clientsRes.data,
        alerts: alertsRes.data,
        simulations: simsRes.data,
        auditEvents: auditRes.data,
        latencyMs: summaryRes.latencyMs,
      };
    },
    []
  );

  const loadWorkspaceData = useCallback(
    async (targetCurrency: CurrencyCode, targetRole: UserRole) => {
      try {
        const snapshot = await fetchAllWorkspaceData(targetCurrency, targetRole);
        setError(null);
        setSummary(snapshot.summary);
        setClients(snapshot.clients);
        setAlerts(snapshot.alerts);
        setSimulations(snapshot.simulations);
        setAuditEvents(snapshot.auditEvents);
        setLastLatencyMs(snapshot.latencyMs);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Error al conectar con cymbal-riesgo-api (/api/v1)."
        );
      } finally {
        setLoading(false);
      }
    },
    [fetchAllWorkspaceData]
  );

  useEffect(() => {
    let cancelled = false;
    async function syncWorkspace() {
      try {
        const snapshot = await fetchAllWorkspaceData(currency, role);
        if (cancelled) return;
        setError(null);
        setSummary(snapshot.summary);
        setClients(snapshot.clients);
        setAlerts(snapshot.alerts);
        setSimulations(snapshot.simulations);
        setAuditEvents(snapshot.auditEvents);
        setLastLatencyMs(snapshot.latencyMs);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof Error
            ? err.message
            : "Error al conectar con cymbal-riesgo-api (/api/v1)."
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void syncWorkspace();
    return () => {
      cancelled = true;
    };
  }, [currency, role, fetchAllWorkspaceData]);

  const sectors = useMemo(
    () => (summary ? summary.sector_exposures.map((s) => s.sector) : []),
    [summary]
  );

  const openHighAlerts = useMemo(
    () =>
      alerts.filter((a) => a.severity === "ALTO" && a.status !== "MITIGADA")
        .length,
    [alerts]
  );

  async function handleRunSimulation(
    payload: StressTestRequest
  ): Promise<StressTestRecord> {
    try {
      const res = await executeStressTest(payload, role);
      setLastLatencyMs(res.latencyMs);
      const [simsRes, auditRes] = await Promise.all([
        fetchStressTests(role),
        fetchAuditEvents(role),
      ]);
      setSimulations(simsRes.data);
      setAuditEvents(auditRes.data);
      return res.data;
    } catch (err) {
      // Recargar auditoría para reflejar inmediatamente eventual bloqueo RBAC 403
      const auditRes = await fetchAuditEvents(role).catch(() => null);
      if (auditRes) setAuditEvents(auditRes.data);
      throw err;
    }
  }

  async function handleUpdateAlertStatus(
    alertId: string,
    status: AlertStatus,
    note?: string
  ): Promise<void> {
    try {
      const res = await updateAlertStatus(alertId, currency, status, note, role);
      setLastLatencyMs(res.latencyMs);
      await loadWorkspaceData(currency, role);
    } catch (err) {
      const auditRes = await fetchAuditEvents(role).catch(() => null);
      if (auditRes) setAuditEvents(auditRes.data);
      throw err;
    }
  }

  async function handleRefreshFx(): Promise<void> {
    try {
      const res = await refreshFxRates(role);
      setLastLatencyMs(res.latencyMs);
      await loadWorkspaceData(currency, role);
    } catch (err) {
      const auditRes = await fetchAuditEvents(role).catch(() => null);
      if (auditRes) setAuditEvents(auditRes.data);
      throw err;
    }
  }

  async function handleRefreshAudit(): Promise<void> {
    const res = await fetchAuditEvents(role);
    setAuditEvents(res.data);
    setLastLatencyMs(res.latencyMs);
  }

  return (
    <div className="cb-shell">
      <TopBar
        currency={currency}
        onCurrencyChange={setCurrency}
        role={role}
        onRoleChange={setRole}
        theme={theme}
        onToggleTheme={() =>
          setTheme((prev) => (prev === "light" ? "dark" : "light"))
        }
        activeTab={activeTab}
        onTabChange={setActiveTab}
        openHighAlerts={openHighAlerts}
        lastLatencyMs={lastLatencyMs}
        fxSnapshot={summary?.fx_snapshot ?? null}
      />

      <main className="cb-main">
        {error && (
          <div className="cb-notice error">
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            <div style={{ flex: 1 }}>
              <strong>Incidencia de conexión con el servicio financiero:</strong>{" "}
              {error}
            </div>
            <button
              type="button"
              className="cb-btn cb-btn-secondary cb-btn-sm"
              onClick={() => void loadWorkspaceData(currency, role)}
            >
              <RefreshCw size={13} aria-hidden="true" />
              Reintentar
            </button>
          </div>
        )}

        {loading && !summary ? (
          <div className="cb-panel cb-loading">
            Cargando consolidado de cartera corporativa desde cymbal-riesgo-api...
          </div>
        ) : (
          summary && (
            <>
              {activeTab === "overview" && (
                <OverviewTab
                  summary={summary}
                  alerts={alerts}
                  currency={currency}
                  onNavigateTab={(tab) => setActiveTab(tab)}
                />
              )}

              {activeTab === "clients" && (
                <ClientsTab clients={clients} currency={currency} />
              )}

              {activeTab === "simulator" && (
                <StressSimulatorTab
                  simulations={simulations}
                  sectors={sectors}
                  currency={currency}
                  role={role}
                  onRunSimulation={handleRunSimulation}
                  onSwitchToAnalyst={() => setRole("risk_analyst")}
                />
              )}

              {activeTab === "alerts" && (
                <AlertsTab
                  alerts={alerts}
                  currency={currency}
                  role={role}
                  onUpdateStatus={handleUpdateAlertStatus}
                  onSwitchToAnalyst={() => setRole("risk_analyst")}
                />
              )}

              {activeTab === "audit" && (
                <AuditFxTab
                  fxSnapshot={summary.fx_snapshot}
                  auditEvents={auditEvents}
                  role={role}
                  onRefreshFx={handleRefreshFx}
                  onRefreshAudit={handleRefreshAudit}
                />
              )}
            </>
          )
        )}
      </main>

      <footer className="cb-footer">
        <div className="cb-footer-inner">
          <span>
            Cymbal Bank — Banca Corporativa y Gestión de Riesgos · Arquitectura
            MVP v1.0 sobre Google Cloud Run
          </span>
          <span className="numeric">
            Motor exacto Python Decimal (ROUND_HALF_EVEN) · Multimoneda USD /
            EUR / MXN / COP · Cumplimiento WCAG AA
          </span>
        </div>
      </footer>
    </div>
  );
}
