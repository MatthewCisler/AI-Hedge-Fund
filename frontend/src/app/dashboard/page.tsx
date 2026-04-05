import { AppLayout } from "@/components/layout";
import { SectionCard, StatCard } from "@/components/cards";
import { fetchDashboard } from "@/lib/api";

export default async function DashboardPage() {
  const dashboard = await fetchDashboard();

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Portfolio command center</h1>
        </div>
      </div>

      <div className="statGrid">
        <StatCard label="Portfolios" value={`${dashboard?.portfolios.length ?? 0}`} />
        <StatCard label="Queued trades" value={`${dashboard?.queued_trades.length ?? 0}`} />
        <StatCard label="Recent AI ideas" value={`${dashboard?.recent_ai_decisions.length ?? 0}`} />
        <StatCard label="Reports" value={`${dashboard?.latest_reports.length ?? 0}`} />
      </div>

      <div className="dashboardGrid">
        <SectionCard title="Portfolios" subtitle="Current value, cash, and risk profile">
          <div className="list">
            {dashboard?.portfolios.map((portfolio) => (
              <div key={portfolio.id} className="listRow">
                <div>
                  <strong>{portfolio.name}</strong>
                  <p className="muted">{portfolio.risk_profile}</p>
                </div>
                <div className="alignRight">
                  <strong>${portfolio.current_value.toFixed(2)}</strong>
                  <p className="muted">Cash ${portfolio.cash_balance.toFixed(2)}</p>
                </div>
              </div>
            )) ?? <p className="muted">No portfolios yet.</p>}
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
                <strong>{String(item.headline ?? "Headline")}</strong>
                <p className="muted">{String(item.source ?? "Source")}</p>
              </div>
            )) ?? <p className="muted">No news ingested yet.</p>}
          </div>
        </SectionCard>

        <SectionCard title="Recent AI decisions" subtitle="Advisory only, never direct execution">
          <div className="list">
            {dashboard?.recent_ai_decisions.map((decision, index) => (
              <div key={index} className="listRow">
                <strong>
                  {String(decision.ticker ?? "TICKER")} {String(decision.action_suggestion ?? "hold")}
                </strong>
                <p className="muted">{String(decision.explanation ?? "No explanation available.")}</p>
              </div>
            )) ?? <p className="muted">No AI decisions recorded yet.</p>}
          </div>
        </SectionCard>
      </div>
    </AppLayout>
  );
}
