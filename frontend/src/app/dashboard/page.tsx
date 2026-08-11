import { AppLayout } from "@/components/layout";
import { SectionCard, StatCard } from "@/components/cards";
import { PortfolioSwitcher } from "@/components/portfolio-switcher";
import { fetchDashboard, fetchSystemStatus } from "@/lib/api";
import { formatChicagoTimestamp } from "@/lib/format";

export default async function DashboardPage() {
  const [dashboard, systemStatus] = await Promise.all([fetchDashboard(), fetchSystemStatus()]);
  const firstPortfolio = dashboard?.portfolios[0];
  const spy = dashboard?.benchmarks.find((item) => item.benchmark_symbol === "SPY");
  const qqq = dashboard?.benchmarks.find((item) => item.benchmark_symbol === "QQQ");
  const dia = dashboard?.benchmarks.find((item) => item.benchmark_symbol === "DIA");
  const totalReturn = firstPortfolio
    ? ((firstPortfolio.current_value - firstPortfolio.initial_investment) / firstPortfolio.initial_investment) * 100
    : 0;

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Portfolio command center</h1>
          <p className="muted">Demo Mode is used automatically when live market or AI services are unavailable.</p>
        </div>
        <PortfolioSwitcher portfolios={dashboard?.portfolios ?? []} selectedId={firstPortfolio?.id} />
      </div>

      <div className="statGrid">
        <StatCard label="Initial" value={`$${(firstPortfolio?.initial_investment ?? 0).toFixed(2)}`} />
        <StatCard label="Current value" value={`$${(firstPortfolio?.current_value ?? 0).toFixed(2)}`} />
        <StatCard
          label="Total return"
          value={`${totalReturn.toFixed(2)}%`}
          tone={totalReturn >= 0 ? "positive" : "negative"}
        />
        <StatCard label="Queued trades" value={`${dashboard?.queued_trades.length ?? 0}`} />
      </div>

      <SectionCard title="System status" subtitle="Paper-trading services and current portfolio state">
        <div className="statusGrid">
          <div><span>AI</span><strong className={`statusText ${systemStatus?.ai.status ?? "offline"}`}>{systemStatus?.ai.model_name ?? "Ollama"} — {systemStatus?.ai.status ?? "offline"}</strong></div>
          <div><span>Broker</span><strong className={`statusText ${systemStatus?.broker.status ?? "demo"}`}>Alpaca Paper — {systemStatus?.broker.status === "connected" ? "Connected" : systemStatus?.broker.status === "disconnected" ? "Disconnected" : "Demo"}</strong></div>
          <div><span>Market</span><strong className={`statusText ${systemStatus?.market.status ?? "closed"}`}>{systemStatus?.market.status === "open" ? "Open" : "Closed"}</strong></div>
          <div><span>Portfolio</span><strong className={`statusText ${firstPortfolio?.is_active ? "online" : "offline"}`}>{firstPortfolio?.is_active ? "Active" : "Paused"}</strong></div>
        </div>
      </SectionCard>

      <div className="dashboardGrid">
        <SectionCard title="Portfolios" subtitle="Current value, cash, and risk profile">
          <div className="list">
            {dashboard?.portfolios.map((portfolio) => (
              <div key={portfolio.id} className="listRow">
                <div>
                  <a href={`/portfolios/${portfolio.id}`}>
                    <strong>{portfolio.name}</strong>
                  </a>
                  <p className="muted">{portfolio.risk_profile}</p>
                </div>
                <div className="alignRight">
                  <strong>${portfolio.current_value.toFixed(2)}</strong>
                  <p className="muted">
                    Cash ${portfolio.cash_balance.toFixed(2)} | Initial ${portfolio.initial_investment.toFixed(2)}
                  </p>
                </div>
              </div>
            )) ?? <p className="muted">No portfolios yet.</p>}
          </div>
        </SectionCard>

        <SectionCard title="Benchmark comparison" subtitle="AI portfolio versus SPY, QQQ, DIA, and 60/40">
          <div className="metricGrid">
            {[spy, qqq, dia, ...(dashboard?.benchmarks.filter((item) => item.benchmark_symbol === "60_40") ?? [])].map(
              (benchmark) =>
                benchmark ? (
                  <div key={benchmark.id} className="metricTile">
                    <span>{benchmark.benchmark_symbol}</span>
                    <strong>{benchmark.total_return_pct.toFixed(2)}%</strong>
                    <p className={totalReturn > benchmark.total_return_pct ? "positiveText" : "negativeText"}>
                      {totalReturn > benchmark.total_return_pct ? "AI ahead" : "AI behind"}
                    </p>
                  </div>
                ) : null,
            )}
          </div>
        </SectionCard>

        <SectionCard title="Queued trades" subtitle="After-hours ideas waiting for next open">
          <div className="list">
            {dashboard?.queued_trades.map((trade) => (
              <div key={trade.id} className="listRow">
                <strong>
                  {trade.side.toUpperCase()} {trade.ticker}
                </strong>
                <p className="muted">{trade.reason}</p>
              </div>
            )) ?? <p className="muted">No queued trades.</p>}
          </div>
        </SectionCard>

        <SectionCard title="Recent news" subtitle="Signals available to the research layer">
          <div className="list">
            {dashboard?.recent_news.map((item, index) => (
              <div key={index} className="listRow">
                <strong>{item.headline}</strong>
                <p className="muted">
                  {item.source} {item.inferred_tickers?.length ? `| ${item.inferred_tickers.join(", ")}` : ""}
                </p>
              </div>
            )) ?? <p className="muted">No news ingested yet.</p>}
          </div>
        </SectionCard>

        <SectionCard title="Recent AI decisions" subtitle="Advisory only, never direct execution">
          <div className="list">
            {dashboard?.recent_ai_decisions.map((decision, index) => (
              <div key={index} className={`listRow stacked ${decision.provider === "deterministic_fallback" ? "fallbackDecision" : ""}`}>
                <div>
                  <strong>{decision.ticker} · {decision.action_suggestion.toUpperCase()} · {decision.provider === "deterministic_fallback" ? "AI FALLBACK" : `${(decision.confidence_score * 100).toFixed(0)}% confidence`}</strong>
                  <p className="muted">{formatChicagoTimestamp(decision.created_at)}</p>
                  <p>{decision.explanation}</p>
                  <p className="muted">Rules: {String(decision.rules_result?.status ?? "pending").replaceAll("_", " ")}</p>
                </div>
              </div>
            )) ?? <p className="muted">No AI decisions recorded yet.</p>}
          </div>
        </SectionCard>
      </div>
    </AppLayout>
  );
}
