"use client";

import { Moon, ShieldCheck, Sun, UserCheck } from "lucide-react";
import type { CurrencyCode, FxRatesSnapshot, UserRole } from "@/types/risk";
import { formatRate } from "@/lib/formatters";

export type NavTabId =
  | "overview"
  | "clients"
  | "simulator"
  | "alerts"
  | "audit";

interface TopBarProps {
  currency: CurrencyCode;
  onCurrencyChange: (currency: CurrencyCode) => void;
  role: UserRole;
  onRoleChange: (role: UserRole) => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  openHighAlerts: number;
  lastLatencyMs: number | null;
  fxSnapshot: FxRatesSnapshot | null;
}

const CURRENCIES: CurrencyCode[] = ["USD", "EUR", "MXN", "COP"];

const NAV_ITEMS: Array<{ id: NavTabId; label: string }> = [
  { id: "overview", label: "Resumen Ejecutivo" },
  { id: "clients", label: "Cartera y Clientes" },
  { id: "simulator", label: "Simulador de Estrés" },
  { id: "alerts", label: "Alertas de Morosidad" },
  { id: "audit", label: "Auditoría JSON y FX" },
];

export function TopBar({
  currency,
  onCurrencyChange,
  role,
  onRoleChange,
  theme,
  onToggleTheme,
  activeTab,
  onTabChange,
  openHighAlerts,
  lastLatencyMs,
  fxSnapshot,
}: TopBarProps) {
  const sloClass =
    lastLatencyMs === null
      ? ""
      : lastLatencyMs >= 500
        ? "breach"
        : lastLatencyMs >= 300
          ? "warn"
          : "";

  return (
    <>
      <header className="cb-topbar">
        <div className="cb-topbar-inner">
          <div className="cb-brand-zone">
            <div className="cb-logo-wrap">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={
                  theme === "dark"
                    ? "/logos/cymbal-bank-logo-modo-oscuro.png"
                    : "/logos/cymbal-bank-logo-principal-claro.png"
                }
                alt="Cymbal Bank"
                className="cb-logo-img"
              />
            </div>
            <div className="cb-brand-divider" aria-hidden="true" />
            <div className="cb-app-title-block">
              <span className="cb-app-title">Panel de Riesgo Financiero</span>
              <span className="cb-app-subtitle">
                Banca Corporativa y Gestión de Riesgos · MVP v1.0
              </span>
            </div>
          </div>

          <div className="cb-controls-zone">
            {/* Selector Multimoneda (USD, EUR, MXN, COP) */}
            <div
              id="currency-selector"
              className="cb-segmented"
              role="group"
              aria-label="Selector multimoneda"
            >
              {CURRENCIES.map((code) => (
                <button
                  key={code}
                  id={`btn-currency-${code}`}
                  type="button"
                  className={`cb-seg-btn numeric ${currency === code ? "active" : ""}`}
                  onClick={() => onCurrencyChange(code)}
                  aria-pressed={currency === code}
                >
                  {code}
                </button>
              ))}
            </div>

            {/* Selector RBAC (Identity Platform OIDC + MFA) */}
            <div
              id="rbac-role-selector"
              className="cb-segmented"
              role="group"
              aria-label="Perfil RBAC activo"
            >
              <button
                id="btn-role-cfo"
                type="button"
                className={`cb-seg-btn ${role === "cfo" ? "active" : ""}`}
                onClick={() => onRoleChange("cfo")}
                aria-pressed={role === "cfo"}
                title="Perfil CFO: supervisión ejecutiva y lectura auditable"
              >
                <ShieldCheck size={14} aria-hidden="true" />
                CFO
              </button>
              <button
                id="btn-role-analyst"
                type="button"
                className={`cb-seg-btn ${role === "risk_analyst" ? "active" : ""}`}
                onClick={() => onRoleChange("risk_analyst")}
                aria-pressed={role === "risk_analyst"}
                title="Perfil Analista de Riesgo: simulador de estrés y gestión de alertas"
              >
                <UserCheck size={14} aria-hidden="true" />
                Analista de Riesgo
              </button>
            </div>

            {/* Telemetría SLO (< 500 ms) */}
            <div
              className="cb-slo-chip numeric"
              title="Latencia del último llamado a cymbal-riesgo-api frente al SLO < 500 ms"
            >
              <span className={`cb-slo-dot ${sloClass}`} aria-hidden="true" />
              <span>
                {lastLatencyMs !== null
                  ? `${lastLatencyMs.toFixed(1)} ms`
                  : "-- ms"}{" "}
                / SLO &lt; 500 ms
              </span>
            </div>

            {/* Alternador Fondo Claro (#F8F9FA) / Fondo Oscuro (#12161F) */}
            <button
              id="btn-theme-toggle"
              type="button"
              className="cb-icon-btn"
              onClick={onToggleTheme}
              aria-label={
                theme === "dark"
                  ? "Cambiar a Fondo Claro"
                  : "Cambiar a Fondo Oscuro"
              }
            >
              {theme === "dark" ? (
                <>
                  <Sun size={15} aria-hidden="true" />
                  Claro
                </>
              ) : (
                <>
                  <Moon size={15} aria-hidden="true" />
                  Oscuro
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <nav className="cb-nav-bar" aria-label="Secciones del Panel de Riesgo">
        <div className="cb-nav-inner">
          <div className="cb-tabs" role="tablist">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                id={`tab-${item.id}`}
                type="button"
                role="tab"
                aria-selected={activeTab === item.id}
                className={`cb-tab ${activeTab === item.id ? "active" : ""}`}
                onClick={() => onTabChange(item.id)}
              >
                <span>{item.label}</span>
                {item.id === "alerts" && openHighAlerts > 0 && (
                  <span className="cb-tab-count numeric">{openHighAlerts}</span>
                )}
              </button>
            ))}
          </div>

          {fxSnapshot && (
            <div className="cb-fx-ticker numeric">
              <span>FX Base USD:</span>
              <span>
                EUR <strong>{formatRate(fxSnapshot.rates.EUR)}</strong>
              </span>
              <span>
                MXN <strong>{formatRate(fxSnapshot.rates.MXN)}</strong>
              </span>
              <span>
                COP <strong>{formatRate(fxSnapshot.rates.COP)}</strong>
              </span>
            </div>
          )}
        </div>
      </nav>
    </>
  );
}
