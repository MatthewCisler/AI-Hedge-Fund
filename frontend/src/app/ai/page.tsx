import { AppLayout } from "@/components/layout";
import { SectionCard, StatCard } from "@/components/cards";
import { ActionButton } from "@/components/action-button";
import { fetchAIDecisions, fetchDashboard } from "@/lib/api";

export default async function AIDecisionsPage() {
  const decisions = await fetchAIDecisions();
  const dashboard = await fetchDashboard();
  const portfolio = dashboard?.portfolios[0];
  const averageConfidence = decisions.length
    ? decisions.reduce((total, decision) => total + decision.confidence_score, 0) / decisions.length
    : 0;

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">AI decisions</p>
          <h1>Local model research log</h1>
        </div>
        <div className="pageActions">
          {portfolio ? <ActionButton label="Run AI Analysis" path={`/ai/analyze?portfolio_id=${portfolio.id}`} variant="primary" /> : null}
          <ActionButton label="Debug Sample" path="/ai/debug-sample" />
        </div>
      </div>

      <div className="statGrid">
        <StatCard label="Decisions" value={`${decisions.length}`} />
        <StatCard label="Avg confidence" value={`${(averageConfidence * 100).toFixed(0)}%`} />
        <StatCard label="Model" value="qwen3:8b" />
        <StatCard label="Authority" value="Advisory" />
      </div>

      <SectionCard title="Recent AI research" subtitle="Structured suggestions that still require rules validation">
        <div className="list">
          {decisions.length ? (
            decisions.map((decision) => {
              const snapshot = decision.input_snapshot ?? {};
              const sentiment = Number(snapshot.sentiment_score ?? 0);
              const urls = Array.isArray(snapshot.news_urls) ? snapshot.news_urls : [];
              return (
                <div key={decision.id} className="listRow stacked">
                  <div>
                    <strong>
                      {decision.action_suggestion.toUpperCase()} {decision.ticker}
                    </strong>
                    <p className="muted">{decision.explanation}</p>
                    <p className="muted">
                      Confidence {(decision.confidence_score * 100).toFixed(0)}% | Sentiment {sentiment.toFixed(2)}
                    </p>
                    {urls.length ? <p className="muted">News used: {urls.slice(0, 3).join(", ")}</p> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <p className="muted">No AI decisions recorded yet.</p>
          )}
        </div>
      </SectionCard>
    </AppLayout>
  );
}
