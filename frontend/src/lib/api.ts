import { cookies } from "next/headers";
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
  UserSession,
  SystemStatus,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const SESSION_COOKIE = "paper_fund_session";

async function apiFetch<T>(path: string): Promise<T | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    return response.ok ? ((await response.json()) as T) : null;
  } catch {
    return null;
  }
}

async function apiList<T>(path: string): Promise<T[]> {
  return (await apiFetch<T[]>(path)) ?? [];
}

export function fetchSession() { return apiFetch<UserSession>("/auth/me"); }
export function fetchSystemStatus() { return apiFetch<SystemStatus>("/settings/system-status"); }
export function fetchDashboard() { return apiFetch<DashboardData>("/dashboard"); }
export function fetchPortfolios() { return apiList<PortfolioSummary>("/portfolios"); }
export function fetchPortfolio(id: string | number) { return apiFetch<PortfolioDetail>(`/portfolios/${id}`); }
export function fetchPortfolioRules(id: string | number) { return apiFetch<PortfolioRule>(`/portfolios/${id}/rules`); }
export function fetchOrders() { return apiList<Order>("/trades/orders"); }
export function fetchQueuedTrades() { return apiList<QueuedTrade>("/trades/queued"); }
export function fetchTrades() { return apiList<Trade>("/trades"); }
export function fetchReports() { return apiList<DailyReport>("/reports"); }
export function fetchAIDecisions() { return apiList<AIDecision>("/ai/decisions"); }
export async function fetchRiskDefaults(): Promise<Record<string, Record<string, number | boolean | string[]>>> {
  return (await apiFetch("/settings/risk-profile-defaults")) ?? {};
}
