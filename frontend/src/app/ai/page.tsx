import { AppLayout } from "@/components/layout";
import { SectionCard, StatCard } from "@/components/cards";
import { ActionButton } from "@/components/action-button";
import { fetchAIDecisions, fetchDashboard } from "@/lib/api";
import { formatChicagoTimestamp } from "@/lib/format";

export default async function AIDecisionsPage() {
  const decisions = await fetchAIDecisions();
  const dashboard = await fetchDashboard();
  const portfolio = dashboard?.portfolios[0];
  const latest = decisions[0];
  const latestRun = latest?.analysis_run_id
    ? decisions.filter((item) => item.analysis_run_id === latest.analysis_run_id)
    : decisions.slice(0, 1);
  const fallbackActive = latest?.provider === "deterministic_fallback" || latest?.analysis_status === "fallback";
  const completed = decisions.filter((item) => item.provider === "ollama");
  const averageConfidence = completed.length
    ? completed.reduce((total, decision) => total + decision.confidence_score, 0) / completed.length
    : 0;
  const modelName = completed.find((item) => item.model_name)?.model_name ?? "Not yet confirmed";

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">AI decisions</p>
          <h1>Advisory research log</h1>
          <p className="muted">Newest first. History is limited by the backend configuration.</p>
        </div>
        <div className="pageActions">
          {portfolio ? <ActionButton label="Run AI Analysis" path={`/ai/analyze?portfolio_id=${portfolio.id}`} variant="primary" /> : null}
          <ActionButton label="Test AI Connection" path="/ai/debug-sample" />
        </div>
      </div>

      {fallbackActive ? (
        <div className="warningBanner" role="alert">
          <strong>Deterministic fallback is active.</strong>
          <span>
            Ollama did not produce a validated result ({latest.failure_category ?? "unavailable"}). On the backend host,
            verify Ollama is running, the configured model is installed, and `OLLAMA_URL` is reachable. This fallback is
            non-actionable and cannot create a trade.
          </span>
        </div>
      ) : latest?.provider === "ollama" ? (
        <div className="successBanner"><strong>Validated Ollama analysis completed.</strong><span>Model: {latest.model_name}</span></div>
      ) : null}

      <div className="statGrid">
        <StatCard label="History" value={`${decisions.length}`} />
        <StatCard label="Latest run" value={`${latestRun.length}`} />
        <StatCard label="Avg Ollama confidence" value={completed.length ? `${(averageConfidence * 100).toFixed(0)}%` : "N/A"} />
        <StatCard label="Model" value={modelName} />
      </div>

      <SectionCard title="Research history" subtitle="AI and fallback output remain advisory; deterministic rules and user confirmation govern orders">
        <div className="list">
          {decisions.length ? decisions.map((decision) => {
            const snapshot = decision.input_snapshot ?? {};
            const sentiment = Number(snapshot.sentiment_score ?? 0);
            const urls = Array.isArray(snapshot.news_urls) ? snapshot.news_urls : [];
            const fallback = decision.provider === "deterministic_fallback";
            return (
              <div key={decision.id} className={`listRow stacked decisionRow ${fallback ? "fallbackDecision" : ""}`}>
                <div>
                  <div className="decisionTopline">
                    <strong>{decision.action_suggestion.toUpperCase()} {decision.ticker}</strong>
                    <span className={`providerPill ${fallback ? "fallback" : "ollama"}`}>
                      {fallback ? "Deterministic fallback" : decision.model_name || "Ollama"}
                    </span>
                  </div>
                  <p>{decision.explanation}</p>
                  <p className="muted">
                    {fallback ? "No model confidence" : `Confidence ${(decision.confidence_score * 100).toFixed(0)}%`} | Sentiment {sentiment.toFixed(2)}
                    {decision.failure_category ? ` | Failure: ${decision.failure_category}` : ""}
                  </p>
                  {urls.length ? <p className="muted">News used: {urls.slice(0, 3).join(", ")}</p> : null}
                  <small className="muted">{formatChicagoTimestamp(decision.created_at)} · Run {decision.analysis_run_id?.slice(0, 8) ?? "legacy"} · Rules {String(decision.rules_result?.status ?? "pending").replaceAll("_", " ")}</small>
                </div>
              </div>
            );
          }) : <div className="emptyState">No analysis history yet. Select a portfolio and run analysis.</div>}
        </div>
      </SectionCard>
    </AppLayout>
  );
}
