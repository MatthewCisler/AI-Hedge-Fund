export type RiskProfile = "safe" | "balanced" | "risky";

export type PortfolioSummary = {
  id: number;
  name: string;
  initial_investment: number;
  cash_balance: number;
  current_value: number;
  risk_profile: RiskProfile;
  is_active: boolean;
};

export type QueuedTrade = {
  id: number;
  portfolio_id: number;
  ticker: string;
  side: string;
  quantity: number;
  reason: string;
  execute_on_market_open: boolean;
};

export type DashboardData = {
  portfolios: PortfolioSummary[];
  queued_trades: QueuedTrade[];
  recent_orders: Array<Record<string, unknown>>;
  recent_news: Array<Record<string, unknown>>;
  recent_ai_decisions: Array<Record<string, unknown>>;
  latest_reports: Array<Record<string, unknown>>;
};
