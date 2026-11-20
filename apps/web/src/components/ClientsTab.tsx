"use client";

import { useMemo, useState } from "react";
import type { ClientPortfolioView, CurrencyCode, RiskLevel } from "@/types/risk";
import { formatMoney, formatPct, formatRate } from "@/lib/formatters";
import { RiskBadge } from "@/components/RiskBadge";

interface ClientsTabProps {
  clients: ClientPortfolioView[];
  currency: CurrencyCode;
}

export function ClientsTab({ clients, currency }: ClientsTabProps) {
  const [search, setSearch] = useState("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "">("");
  const [originFilter, setOriginFilter] = useState<CurrencyCode | "">("");

  const sectors = useMemo(
    () => Array.from(new Set(clients.map((c) => c.sector))).sort(),
    [clients]
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return clients.filter((c) => {
      if (sectorFilter && c.sector !== sectorFilter) return false;
      if (riskFilter && c.risk_level !== riskFilter) return false;
      if (originFilter && c.origin_currency !== originFilter) return false;
      if (
        q &&
        !c.name.toLowerCase().includes(q) &&
        !c.client_id.toLowerCase().includes(q) &&
        !c.country.toLowerCase().includes(q) &&
        !c.sector.toLowerCase().includes(q)
      ) {
        return false;
      }
      return true;
    });
  }, [clients, search, sectorFilter, riskFilter, originFilter]);

  const totalFilteredEad = useMemo(
    () => filtered.reduce((acc, c) => acc + Number(c.ead), 0),
    [filtered]
  );
  const totalFilteredEl = useMemo(
    () => filtered.reduce((acc, c) => acc + Number(c.expected_loss), 0),
    [filtered]
  );

  return (
    <>
      <div className="cb-page-header">
        <div>
          <h1 className="cb-h1">Cartera Corporativa y Clientes</h1>
          <p className="cb-lead">
            Detalle por acreditado con conversión exacta a {currency}, parámetros
            PD/LGD y clasificación semafórica de morosidad.
          </p>
        </div>
        <div className="cb-meta-stamp numeric">
          <span>
            Mostrando <strong>{filtered.length}</strong> de {clients.length}{" "}
            acreditados
          </span>
        </div>
      </div>

      <section className="cb-panel">
        <div className="cb-panel-header">
          <div className="cb-toolbar">
            <input
              id="clients-search-input"
              type="search"
              className="cb-input"
              style={{ minWidth: 240 }}
              placeholder="Buscar cliente, ID o país..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              id="clients-sector-select"
              className="cb-select"
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
              aria-label="Filtrar por sector"
            >
              <option value="">Todos los sectores</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <select
              id="clients-risk-select"
              className="cb-select"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value as RiskLevel | "")}
              aria-label="Filtrar por severidad"
            >
              <option value="">Todos los niveles de riesgo</option>
              <option value="ALTO">Riesgo Alto</option>
              <option value="MEDIO">Riesgo Medio</option>
              <option value="BAJO">Riesgo Bajo</option>
            </select>
            <select
              id="clients-origin-select"
              className="cb-select"
              value={originFilter}
              onChange={(e) =>
                setOriginFilter(e.target.value as CurrencyCode | "")
              }
              aria-label="Filtrar por moneda de origen"
            >
              <option value="">Todas las monedas origen</option>
              <option value="USD">Origen USD</option>
              <option value="EUR">Origen EUR</option>
              <option value="MXN">Origen MXN</option>
              <option value="COP">Origen COP</option>
            </select>
          </div>

          <div className="cb-meta-stamp numeric">
            <span>
              EAD: <strong>{formatMoney(totalFilteredEad, currency)}</strong>
            </span>
            <span>
              EL: <strong>{formatMoney(totalFilteredEl, currency)}</strong>
            </span>
          </div>
        </div>

        <div className="cb-table-wrap">
          <table className="cb-table">
            <thead>
              <tr>
                <th>Acreditado / Facilidad</th>
                <th>Sector / País</th>
                <th>Rating</th>
                <th>Origen</th>
                <th className="numeric">EAD ({currency})</th>
                <th className="numeric">PD</th>
                <th className="numeric">LGD</th>
                <th className="numeric">Pérdida Esperada ({currency})</th>
                <th className="numeric">Mora</th>
                <th>Riesgo</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((client) => (
                <tr key={client.client_id}>
                  <td>
                    <span className="cb-table-primary-cell">{client.name}</span>
                    <span className="cb-table-secondary-cell">
                      {client.client_id} · {client.facility_type}
                    </span>
                  </td>
                  <td>
                    <span className="cb-table-primary-cell">{client.sector}</span>
                    <span className="cb-table-secondary-cell">
                      {client.country}
                    </span>
                  </td>
                  <td className="numeric" style={{ fontWeight: 600 }}>
                    {client.credit_rating}
                  </td>
                  <td>
                    <span className="cb-badge neutral numeric">
                      {client.origin_currency}
                    </span>
                    {client.origin_currency !== currency && (
                      <span
                        className="cb-table-secondary-cell numeric"
                        style={{ marginTop: 2 }}
                      >
                        FX {formatRate(client.fx_rate_applied)}
                      </span>
                    )}
                  </td>
                  <td className="numeric" style={{ fontWeight: 600 }}>
                    {formatMoney(client.ead, currency)}
                  </td>
                  <td className="numeric">{formatPct(client.pd_pct)}</td>
                  <td className="numeric">{formatPct(client.lgd_pct)}</td>
                  <td className="numeric" style={{ fontWeight: 600 }}>
                    {formatMoney(client.expected_loss, currency)}
                  </td>
                  <td className="numeric">
                    {client.days_past_due} d
                    {client.is_npl && (
                      <span
                        className="cb-table-secondary-cell"
                        style={{ color: "var(--cb-risk-high)", fontWeight: 600 }}
                      >
                        NPL &gt;90d
                      </span>
                    )}
                  </td>
                  <td>
                    <RiskBadge level={client.risk_level} compact />
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={10} className="cb-loading">
                    No existen acreditados que coincidan con los filtros
                    seleccionados.
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
