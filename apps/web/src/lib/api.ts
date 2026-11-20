import type {
  AlertStatus,
  AlertView,
  AuditEvent,
  ClientPortfolioView,
  CurrencyCode,
  FxRatesSnapshot,
  PortfolioSummaryResponse,
  RiskLevel,
  StressTestRecord,
  StressTestRequest,
  UserRole,
} from "@/types/risk";

export interface ApiResult<T> {
  data: T;
  latencyMs: number;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

const ROLE_EMAILS: Record<UserRole, string> = {
  cfo: "cfo.corporativo@cymbalbank.com",
  risk_analyst: "analista.riesgo@cymbalbank.com",
};

async function apiFetch<T>(
  path: string,
  role: UserRole,
  init?: RequestInit
): Promise<ApiResult<T>> {
  const started = performance.now();
  const headers = new Headers(init?.headers);
  headers.set("X-Cymbal-Role", role);
  headers.set("X-Cymbal-User", ROLE_EMAILS[role]);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, {
    ...init,
    headers,
    cache: "no-store",
  });

  const serverLatency = response.headers.get("X-Response-Time-Ms");
  const measuredMs = serverLatency
    ? Number(serverLatency)
    : Math.round((performance.now() - started) * 100) / 100;

  if (!response.ok) {
    let detail = `Error HTTP ${response.status}`;
    try {
      const errBody = await response.json();
      if (typeof errBody?.detail === "string") {
        detail = errBody.detail;
      }
    } catch {
      // keep default detail
    }
    throw new ApiError(response.status, detail);
  }

  const data = (await response.json()) as T;
  return { data, latencyMs: Number.isFinite(measuredMs) ? measuredMs : 0 };
}

export function fetchPortfolioSummary(
  currency: CurrencyCode,
  role: UserRole
): Promise<ApiResult<PortfolioSummaryResponse>> {
  return apiFetch<PortfolioSummaryResponse>(
    `/api/v1/portfolio/summary?currency=${currency}`,
    role
  );
}

export function fetchClients(
  currency: CurrencyCode,
  role: UserRole,
  filters?: {
    sector?: string;
    risk_level?: RiskLevel | "";
    origin_currency?: CurrencyCode | "";
    search?: string;
  }
): Promise<ApiResult<ClientPortfolioView[]>> {
  const params = new URLSearchParams({ currency });
  if (filters?.sector) params.set("sector", filters.sector);
  if (filters?.risk_level) params.set("risk_level", filters.risk_level);
  if (filters?.origin_currency) {
    params.set("origin_currency", filters.origin_currency);
  }
  if (filters?.search?.trim()) params.set("search", filters.search.trim());
  return apiFetch<ClientPortfolioView[]>(
    `/api/v1/clients?${params.toString()}`,
    role
  );
}

export function fetchStressTests(
  role: UserRole
): Promise<ApiResult<StressTestRecord[]>> {
  return apiFetch<StressTestRecord[]>("/api/v1/stress-tests", role);
}

export function executeStressTest(
  payload: StressTestRequest,
  role: UserRole
): Promise<ApiResult<StressTestRecord>> {
  return apiFetch<StressTestRecord>("/api/v1/stress-tests", role, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchAlerts(
  currency: CurrencyCode,
  role: UserRole
): Promise<ApiResult<AlertView[]>> {
  return apiFetch<AlertView[]>(`/api/v1/alerts?currency=${currency}`, role);
}

export function updateAlertStatus(
  alertId: string,
  currency: CurrencyCode,
  status: AlertStatus,
  analystNote: string | undefined,
  role: UserRole
): Promise<ApiResult<AlertView>> {
  return apiFetch<AlertView>(
    `/api/v1/alerts/${encodeURIComponent(alertId)}?currency=${currency}`,
    role,
    {
      method: "PATCH",
      body: JSON.stringify({
        status,
        analyst_note: analystNote?.trim() || null,
      }),
    }
  );
}

export function fetchFxRates(
  role: UserRole
): Promise<ApiResult<FxRatesSnapshot>> {
  return apiFetch<FxRatesSnapshot>("/api/v1/fx/rates", role);
}

export function refreshFxRates(
  role: UserRole
): Promise<ApiResult<FxRatesSnapshot>> {
  return apiFetch<FxRatesSnapshot>("/api/v1/fx/refresh", role, {
    method: "POST",
  });
}

export function fetchAuditEvents(
  role: UserRole,
  limit = 40
): Promise<ApiResult<AuditEvent[]>> {
  return apiFetch<AuditEvent[]>(`/api/v1/audit/events?limit=${limit}`, role);
}
