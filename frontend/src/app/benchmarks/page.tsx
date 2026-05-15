import { AppLayout } from "@/components/layout";
import { SectionCard, StatCard } from "@/components/cards";
import { fetchDashboard } from "@/lib/api";

export default async function BenchmarksPage() {
  const dashboard = await fetchDashboard();
  const portfolio = dashboard?.portfolios[0];
  const benchmarks = dashboard?.benchmarks ?? [];
  const aiReturn = portfolio
    ? ((portfolio.current_value - portfolio.initial_investment) / portfolio.initial_investment) * 100
    : 0;

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Benchmarks</p>
          <h1>AI versus the market</h1>
        </div>
      </div>

      <div className="statGrid">
        <StatCard label="AI return" value={`${aiReturn.toFixed(2)}%`} tone={aiReturn >= 0 ? "positive" : "negative"} />
        <StatCard label="SPY" value={`${benchmarks.find((item) => item.benchmark_symbol === "SPY")?.total_return_pct.toFixed(2) ?? "0.00"}%`} />
        <StatCard label="QQQ" value={`${benchmarks.find((item) => item.benchmark_symbol === "QQQ")?.total_return_pct.toFixed(2) ?? "0.00"}%`} />
        <StatCard label="DIA" value={`${benchmarks.find((item) => item.benchmark_symbol === "DIA")?.total_return_pct.toFixed(2) ?? "0.00"}%`} />
      </div>

      <SectionCard title="Benchmark snapshots" subtitle="SPY, QQQ, DIA, and optional 60/40 comparison">
        <div className="tableLike">
          <div className="tableHeader">
            <span>Benchmark</span>
            <span>Current value</span>
            <span>Daily</span>
            <span>Total</span>
            <span>Status</span>
          </div>
          {benchmarks.length ? (
            benchmarks.map((benchmark) => (
              <div key={benchmark.id} className="tableRow">
                <span>{benchmark.benchmark_symbol}</span>
                <span>${benchmark.current_value.toFixed(2)}</span>
                <span>{benchmark.daily_return_pct.toFixed(2)}%</span>
                <span>{benchmark.total_return_pct.toFixed(2)}%</span>
                <span className={aiReturn > benchmark.total_return_pct ? "positiveText" : "negativeText"}>
                  {aiReturn > benchmark.total_return_pct ? "AI ahead" : "AI behind"}
                </span>
              </div>
            ))
          ) : (
            <p className="muted">No benchmark snapshots yet. Generate a report or refresh benchmarks from the API.</p>
          )}
        </div>
      </SectionCard>
    </AppLayout>
  );
}
