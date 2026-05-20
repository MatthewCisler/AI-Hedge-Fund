import Link from "next/link";
import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";
import { CreatePortfolioForm } from "@/components/portfolio-forms";
import { fetchDashboard } from "@/lib/api";

function money(value = 0) {
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function pct(value = 0) {
  return `${Number(value).toFixed(2)}%`;
}

export default async function PortfoliosPage() {
  const dashboard = await fetchDashboard();
  const portfolios = dashboard?.portfolios ?? [];

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Portfolios</p>
          <h1>AI paper portfolios</h1>
          <p className="muted">Demo Mode: values and recommendations fall back to local mock data when Alpaca or Ollama are unavailable.</p>
        </div>
      </div>

      <div className="dashboardGrid">
        <SectionCard title="All portfolios" subtitle="Each card is paper-trading only">
          {portfolios.length ? (
            <div className="portfolioGrid">
              {portfolios.map((portfolio) => {
                const benchmark = dashboard?.benchmarks.find(
                  (item) => item.portfolio_id === portfolio.id && item.benchmark_symbol === portfolio.benchmark_symbol,
                );
                return (
                  <Link key={portfolio.id} href={`/portfolios/${portfolio.id}`} className="portfolioCard">
                    <div className="cardTopline">
                      <strong>{portfolio.name}</strong>
                      <span className={portfolio.is_active ? "statusPill active" : "statusPill"}>{portfolio.is_active ? "Active" : "Paused"}</span>
                    </div>
                    <p className="muted">{portfolio.risk_profile} risk</p>
                    <div className="metricGrid compact">
                      <div>
                        <span>Initial</span>
                        <strong>{money(portfolio.initial_investment)}</strong>
                      </div>
                      <div>
                        <span>Current</span>
                        <strong>{money(portfolio.current_value)}</strong>
                      </div>
                      <div>
                        <span>Daily</span>
                        <strong className={portfolio.daily_gain_loss >= 0 ? "positiveText" : "negativeText"}>{money(portfolio.daily_gain_loss)}</strong>
                      </div>
                      <div>
                        <span>Total return</span>
                        <strong className={portfolio.total_return_pct >= 0 ? "positiveText" : "negativeText"}>{pct(portfolio.total_return_pct)}</strong>
                      </div>
                    </div>
                    <p className="muted">
                      Benchmark {portfolio.benchmark_symbol === "60_40" ? "60/40" : portfolio.benchmark_symbol}:{" "}
                      {benchmark ? `${pct(portfolio.total_return_pct - benchmark.total_return_pct)} vs benchmark` : "not available yet"}
                    </p>
                  </Link>
                );
              })}
            </div>
          ) : (
            <p className="muted">No portfolios yet. Create your first paper portfolio with the form.</p>
          )}
        </SectionCard>

        <SectionCard title="Create portfolio" subtitle="Paper allocation and trading rules">
          <CreatePortfolioForm />
        </SectionCard>
      </div>
    </AppLayout>
  );
}
