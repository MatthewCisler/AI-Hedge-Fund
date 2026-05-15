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

export type BenchmarkSnapshot = {
  id: number;
  portfolio_id: number;
  benchmark_symbol: string;
  snapshot_date: string;
  initial_value: number;
  current_value: number;
  daily_return_pct: number;
  total_return_pct: number;
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

export type Order = {
  id: number;
  portfolio_id: number;
  ticker: string;
  side: string;
  quantity: number;
  order_type: string;
  status: string;
  requested_price: number | null;
  broker_order_id: string | null;
  rejection_reason: string | null;
};

export type Trade = {
  id: number;
  portfolio_id: number;
  ticker: string;
  side: string;
  quantity: number;
  fill_price: number;
  realized_pnl: number | null;
  notes: string | null;
};

export type NewsArticle = {
  id: number;
  source: string;
  headline: string;
  url: string;
  published_at: string;
  summary: string | null;
  inferred_tickers: string[] | null;
};

export type AIDecision = {
  id: number;
  portfolio_id: number;
  ticker: string;
  action_suggestion: string;
  confidence_score: number;
  explanation: string;
  input_snapshot: Record<string, unknown> | null;
  rules_result: Record<string, unknown> | null;
  created_at: string;
};

export type DailyReport = {
  id: number;
  portfolio_id: number;
  report_date: string;
  csv_path: string | null;
  summary: Record<string, unknown>;
  narrative: string | null;
  rows: Array<{
    id: number;
    section: string;
    label: string;
    value: string;
    numeric_value: number | null;
  }>;
};

export type DashboardData = {
  portfolios: PortfolioSummary[];
  queued_trades: QueuedTrade[];
  recent_orders: Order[];
  recent_news: NewsArticle[];
  recent_ai_decisions: AIDecision[];
  latest_reports: DailyReport[];
  benchmarks: BenchmarkSnapshot[];
};
