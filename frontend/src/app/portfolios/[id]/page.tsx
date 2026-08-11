import Link from "next/link";
import { ActionButton } from "@/components/action-button";
import { SectionCard, StatCard } from "@/components/cards";
import { AppLayout } from "@/components/layout";
import { PortfolioSettingsForm } from "@/components/portfolio-forms";
import { RecommendationWorkflow } from "@/components/trade-workflow";
import { ReportDownload } from "@/components/report-download";
import { fetchDashboard, fetchPortfolio } from "@/lib/api";
import { formatChicagoTimestamp } from "@/lib/format";

function money(value = 0) {
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function pct(value = 0) {
  return `${Number(value).toFixed(2)}%`;
}

export default async function PortfolioDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [portfolio, dashboard] = await Promise.all([fetchPortfolio(id), fetchDashboard()]);

  if (!portfolio) {
    return (
      <AppLayout>
        <SectionCard title="Portfolio not found" subtitle="The portfolio may not exist for this account">
          <Link className="button secondary" href="/portfolios">
            Back to portfolios
          </Link>
        </SectionCard>
      </AppLayout>
    );
  }

  const latestReport = portfolio.daily_reports[0];
  const spy = portfolio.benchmark_snapshots.find((item) => item.benchmark_symbol === "SPY");
  const news = dashboard?.recent_news.filter((item) =>
    item.inferred_tickers?.some((ticker) => portfolio.positions.some((position) => position.ticker === ticker)),
  );

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Portfolio Detail</p>
          <h1>{portfolio.name}</h1>
          <p className="muted">
            {portfolio.risk_profile} risk | {portfolio.is_active ? "Active" : "Paused"} | Demo Mode fallback enabled
          </p>
        </div>
        <div className="pageActions">
          <ActionButton label="Generate daily report now" path={`/portfolios/${portfolio.id}/generate-report`} />
          <ActionButton label="Rebalance now" path={`/portfolios/${portfolio.id}/rebalance`} />
          {portfolio.is_active ? (
            <ActionButton label="Pause portfolio" path={`/portfolios/${portfolio.id}/pause`} />
          ) : (
            <ActionButton label="Resume portfolio" path={`/portfolios/${portfolio.id}/resume`} />
          )}
          <ActionButton label="Clear queued trades" path={`/portfolios/${portfolio.id}/queued-trades`} method="DELETE" />
        </div>
      </div>

      <div className="statGrid">
        <StatCard label="Initial" value={money(portfolio.initial_investment)} />
        <StatCard label="Current value" value={money(portfolio.current_value)} />
        <StatCard label="Daily gain/loss" value={money(portfolio.daily_gain_loss)} tone={portfolio.daily_gain_loss >= 0 ? "positive" : "negative"} />
        <StatCard label="Total return" value={pct(portfolio.total_return_pct)} tone={portfolio.total_return_pct >= 0 ? "positive" : "negative"} />
      </div>

      <SectionCard title="AI recommendation to paper order" subtitle="Review the research, then explicitly confirm any proposed trade">
        <RecommendationWorkflow portfolio={portfolio} recent={portfolio.ai_decisions.slice(0, 6)} />
      </SectionCard>

      <div className="dashboardGrid">
        <SectionCard title="Current holdings" subtitle="Paper positions only">
          {portfolio.positions.length ? (
            <div className="tableLike">
              <div className="tableHeader">
                <span>Ticker</span>
                <span>Quantity</span>
                <span>Market value</span>
                <span>P/L</span>
                <span>Sector</span>
              </div>
              {portfolio.positions.map((position) => (
                <div key={position.id} className="tableRow">
                  <strong>{position.ticker}</strong>
                  <span>{position.quantity}</span>
                  <span>{money(position.market_value)}</span>
                  <span className={position.unrealized_pnl >= 0 ? "positiveText" : "negativeText"}>{money(position.unrealized_pnl)}</span>
                  <span>{position.sector ?? "Unclassified"}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No holdings yet. Run analysis or rebalance to create demo ideas.</p>
          )}
        </SectionCard>

        <SectionCard title="Allocation" subtitle="Based on current holdings">
          {portfolio.positions.length ? (
            <div className="allocationList">
              {portfolio.positions.map((position) => (
                <div key={position.id}>
                  <div className="cardTopline">
                    <span>{position.ticker}</span>
                    <strong>{pct((position.market_value / portfolio.current_value) * 100)}</strong>
                  </div>
                  <div className="bar">
                    <span style={{ width: `${Math.min(100, (position.market_value / portfolio.current_value) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">Allocation appears after positions are present.</p>
          )}
        </SectionCard>

        <SectionCard title="Queued trades" subtitle="Paper orders waiting for next open">
          <div className="list">
            {portfolio.queued_trades.length ? (
              portfolio.queued_trades.map((trade) => (
                <div key={trade.id} className="listRow">
                  <strong>
                    {trade.side.toUpperCase()} {trade.ticker}
                  </strong>
                  <p className="muted">{trade.reason}</p>
                </div>
              ))
            ) : (
              <p className="muted">No queued trades.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Recent trades" subtitle="Filled paper trades">
          <div className="list">
            {portfolio.trades.length ? (
              portfolio.trades.slice(0, 6).map((trade) => (
                <div key={trade.id} className="listRow">
                  <strong>
                    {trade.side.toUpperCase()} {trade.ticker}
                  </strong>
                  <p className="muted">
                    {trade.quantity} @ {money(trade.fill_price)}
                  </p>
                </div>
              ))
            ) : (
              <p className="muted">No completed paper trades yet.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Recent AI decisions" subtitle="Last recommendation reasoning">
          <div className="list">
            {portfolio.ai_decisions.length ? (
              portfolio.ai_decisions.slice(0, 6).map((decision) => (
                <details key={decision.id} className="detailBox">
                  <summary>
                    {decision.ticker} {decision.action_suggestion} ({(decision.confidence_score * 100).toFixed(0)}%)
                  </summary>
                  <p className="muted">{decision.explanation}</p>
                  <p className="muted">{formatChicagoTimestamp(decision.created_at)} · Rules {String(decision.rules_result?.status ?? "pending").replaceAll("_", " ")}</p>
                </details>
              ))
            ) : (
              <p className="muted">No AI decisions yet. Run analysis to generate demo recommendations.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Benchmark performance" subtitle="SPY comparison if available">
          {spy ? (
            <div className="metricGrid">
              <div className="metricTile">
                <span>SPY total return</span>
                <strong>{pct(spy.total_return_pct)}</strong>
              </div>
              <div className="metricTile">
                <span>Portfolio vs SPY</span>
                <strong className={portfolio.total_return_pct >= spy.total_return_pct ? "positiveText" : "negativeText"}>
                  {pct(portfolio.total_return_pct - spy.total_return_pct)}
                </strong>
              </div>
            </div>
          ) : (
            <p className="muted">SPY benchmark is not available yet. Generate a report or refresh benchmarks.</p>
          )}
        </SectionCard>

        <SectionCard title="Recent news" subtitle="News matching current holdings">
          <div className="list">
            {news?.length ? (
              news.slice(0, 5).map((item) => (
                <div key={item.id} className="listRow stacked">
                  <strong>{item.headline}</strong>
                  <p className="muted">{item.source}</p>
                </div>
              ))
            ) : (
              <p className="muted">No matching news yet. Demo feed data appears when live feeds are unavailable.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Latest daily report" subtitle="Generated report output">
          {latestReport ? (
            <ReportDownload reportId={latestReport.id} label="Open latest report CSV" />
          ) : (
            <p className="muted">No daily report generated for this portfolio yet.</p>
          )}
        </SectionCard>

        <SectionCard title="Tuning" subtitle="Rules for this portfolio">
          <PortfolioSettingsForm portfolio={portfolio} />
        </SectionCard>
      </div>
    </AppLayout>
  );
}
