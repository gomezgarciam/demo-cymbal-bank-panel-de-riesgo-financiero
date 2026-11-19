import type { CurrencyCode } from "@/types/risk";

/**
 * Formatea cifras monetarias con moneda ISO 4217 explícita, separadores de miles uniformes
 * y 2 decimales constantes conforme a la Guía de Marca de Cymbal Bank.
 */
export function formatMoney(
  value: string | number,
  currency: CurrencyCode
): string {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return `${currency} 0.00`;
  const formatted = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
  return `${currency} ${formatted}`;
}

/**
 * Formato ejecutivo compacto (M / B / K) para encabezados de KPI y ejes de gráficas.
 */
export function formatCompactMoney(
  value: string | number,
  currency: CurrencyCode
): string {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return `${currency} 0.00`;
  const abs = Math.abs(num);
  const sign = num < 0 ? "-" : "";

  if (abs >= 1_000_000_000) {
    return `${sign}${currency} ${(abs / 1_000_000_000).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}B`;
  }
  if (abs >= 1_000_000) {
    return `${sign}${currency} ${(abs / 1_000_000).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}M`;
  }
  if (abs >= 1_000) {
    return `${sign}${currency} ${(abs / 1_000).toLocaleString("en-US", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })}K`;
  }
  return `${sign}${formatMoney(abs, currency)}`;
}

export function formatPct(
  value: string | number,
  showSign = false
): string {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return "0.00%";
  const prefix = showSign && num > 0 ? "+" : "";
  return `${prefix}${num.toFixed(2)}%`;
}

export function formatBps(value: number): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value} pbs`;
}

export function formatRate(value: string | number): string {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return "0.0000";
  return num.toLocaleString("en-US", {
    minimumFractionDigits: 4,
    maximumFractionDigits: 6,
  });
}

export function formatUtcTimestamp(iso: string): string {
  try {
    const dt = new Date(iso);
    return (
      dt.toLocaleString("es-CO", {
        timeZone: "UTC",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }) + " UTC"
    );
  } catch {
    return iso;
  }
}

export function toNumeric(value: string | number): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}
