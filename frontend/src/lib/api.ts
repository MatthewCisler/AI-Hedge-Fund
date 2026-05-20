import {
  AIDecision,
  DailyReport,
  DashboardData,
  Order,
  PortfolioDetail,
  PortfolioRule,
  PortfolioSummary,
  QueuedTrade,
  Trade,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function fetchDashboard(userId = "1"): Promise<DashboardData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard`, {
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as DashboardData;
  } catch {
    return null;
  }
}

async function apiGet<T>(path: string, userId = "1"): Promise<T[]> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return [];
    }
    return (await response.json()) as T[];
  } catch {
    return [];
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}, userId = "1"): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
        ...(options.headers ?? {}),
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export function fetchPortfolios() {
  return apiGet<PortfolioSummary>("/portfolios");
}

export function fetchPortfolio(id: string | number) {
  return apiRequest<PortfolioDetail>(`/portfolios/${id}`);
}

export function fetchPortfolioRules(id: string | number) {
  return apiRequest<PortfolioRule>(`/portfolios/${id}/rules`);
}

export function fetchOrders() {
  return apiGet<Order>("/trades/orders");
}

export function fetchQueuedTrades() {
  return apiGet<QueuedTrade>("/trades/queued");
}

export function fetchTrades() {
  return apiGet<Trade>("/trades");
}

export function fetchReports() {
  return apiGet<DailyReport>("/reports");
}

export function fetchAIDecisions() {
  return apiGet<AIDecision>("/ai/decisions");
}

export async function fetchRiskDefaults(): Promise<Record<string, Record<string, number | boolean | string[]>>> {
  try {
    const response = await fetch(`${API_BASE_URL}/settings/risk-profile-defaults`, {
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": "1",
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return {};
    }
    return (await response.json()) as Record<string, Record<string, number | boolean | string[]>>;
  } catch {
    return {};
  }
}

export function reportCsvUrl(reportId: number) {
  return `${API_BASE_URL}/reports/${reportId}/csv?user_id=1`;
}
