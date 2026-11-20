"use client";

import type { AlertStatus, RiskLevel } from "@/types/risk";

const RISK_LABELS: Record<RiskLevel, string> = {
  BAJO: "Riesgo Bajo",
  MEDIO: "Riesgo Medio",
  ALTO: "Riesgo Alto",
};

const STATUS_LABELS: Record<AlertStatus, string> = {
  ABIERTA: "Abierta",
  EN_REVISION: "En revisión",
  MITIGADA: "Mitigada",
};

export function RiskBadge({
  level,
  compact = false,
}: {
  level: RiskLevel;
  compact?: boolean;
}) {
  return (
    <span className={`cb-badge risk-${level}`}>
      <span className="cb-badge-dot" aria-hidden="true" />
      {compact ? level : RISK_LABELS[level]}
    </span>
  );
}

export function AlertStatusBadge({ status }: { status: AlertStatus }) {
  const variant =
    status === "MITIGADA"
      ? "risk-BAJO"
      : status === "EN_REVISION"
        ? "primary"
        : "neutral";
  return <span className={`cb-badge ${variant}`}>{STATUS_LABELS[status]}</span>;
}
