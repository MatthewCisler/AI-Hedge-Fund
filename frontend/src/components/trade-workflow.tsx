"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AIDecision, Order, PortfolioSummary, QueuedTrade } from "@/lib/types";
import { clientApi } from "@/lib/client-api";

type Submission = Order | QueuedTrade;
type OrderPayload = { portfolio_id: number; ticker: string; side: string; quantity: number; ai_decision_id?: number };
type OrderPreview = {
  approved: boolean; reasons: string[]; ticker: string; side: string; quantity: number;
  estimated_price: number; estimated_dollar_amount: number; portfolio_cash: number;
  resulting_position_pct: number; queue_for_next_open: boolean;
  ai_confidence: number | null; ai_reasoning: string | null;
};

function outcomeLabel(result: Submission) {
  return "status" in result
    ? `Paper order ${result.status}: ${result.side.toUpperCase()} ${result.quantity} ${result.ticker}.`
    : `Queued for next market open: ${result.side.toUpperCase()} ${result.quantity} ${result.ticker}.`;
}

export function OrderForm({ portfolios, initialDecision }: { portfolios: PortfolioSummary[]; initialDecision?: AIDecision }) {
  const router = useRouter();
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<OrderPreview | null>(null);
  const [pendingPayload, setPendingPayload] = useState<OrderPayload | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus("Checking deterministic portfolio rules…");
    const form = new FormData(event.currentTarget);
    const payload: OrderPayload = {
      portfolio_id: Number(form.get("portfolio_id")),
      ticker: String(form.get("ticker") ?? "").trim().toUpperCase(),
      side: String(form.get("side") ?? "buy"),
      quantity: Number(form.get("quantity")),
      ...(initialDecision ? { ai_decision_id: initialDecision.id } : {}),
    };
    const result = await clientApi<OrderPreview>("/trades/orders/validate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setBusy(false);
    if (!result.ok) {
      setPreview(null);
      setStatus(`Rules rejected this proposal: ${result.error}`);
      return;
    }
    setPreview(result.data);
    setPendingPayload(payload);
    setStatus("Approved by deterministic rules. Review the estimate and explicitly execute when ready.");
  }

  async function executePaperTrade() {
    if (!pendingPayload || !preview || !window.confirm("Submit this PAPER MONEY order? No live trading will occur.")) return;
    setBusy(true);
    setStatus("Submitting confirmed paper order…");
    const result = await clientApi<Submission>("/trades/orders", { method: "POST", body: JSON.stringify(pendingPayload) });
    setBusy(false);
    if (!result.ok) { setStatus(`Execution rejected: ${result.error}`); return; }
    setStatus(outcomeLabel(result.data));
    setPreview(null);
    router.refresh();
  }

  return (
    <form className="settingsForm orderForm" onSubmit={submit} onChange={() => setPreview(null)}>
      <div className="formGrid">
        <label>Portfolio<select name="portfolio_id" defaultValue={initialDecision?.portfolio_id ?? portfolios[0]?.id}>{portfolios.map((portfolio) => <option key={portfolio.id} value={portfolio.id}>{portfolio.name}</option>)}</select></label>
        <label>Ticker<input name="ticker" required maxLength={16} defaultValue={initialDecision?.ticker ?? ""} placeholder="SPY" /></label>
        <label>Side<select name="side" defaultValue={initialDecision?.action_suggestion === "sell" ? "sell" : "buy"}><option value="buy">Buy</option><option value="sell">Sell</option></select></label>
        <label>Quantity<input name="quantity" type="number" min="0.0001" step="0.0001" required defaultValue={Number(initialDecision?.input_snapshot?.quantity ?? 1)} /></label>
      </div>
      <div className="safetyNotice"><strong>User confirmation required.</strong> Submission always goes through backend deterministic rules. AI cannot place or bypass an order.</div>
      <button className="button secondary" type="submit" disabled={busy || !portfolios.length}>{busy ? "Validating…" : "Run through rules engine"}</button>
      {preview ? <div className="executionPreview">
        <strong>Approved by rules engine</strong>
        <div className="metricGrid compact">
          <div><span>Trade</span><strong>{preview.side.toUpperCase()} {preview.quantity} {preview.ticker}</strong></div>
          <div><span>Current price</span><strong>${preview.estimated_price.toFixed(2)}</strong></div>
          <div><span>Estimated amount</span><strong>${preview.estimated_dollar_amount.toFixed(2)}</strong></div>
          <div><span>Portfolio cash</span><strong>${preview.portfolio_cash.toFixed(2)}</strong></div>
          <div><span>Approx. position</span><strong>{preview.resulting_position_pct.toFixed(2)}%</strong></div>
          <div><span>AI confidence</span><strong>{preview.ai_confidence == null ? "Manual" : `${(preview.ai_confidence * 100).toFixed(0)}%`}</strong></div>
        </div>
        {preview.ai_reasoning ? <p>{preview.ai_reasoning}</p> : null}
        <p className="muted">{preview.reasons.join(" ")}{preview.queue_for_next_open ? " Market is closed; execution will queue for next open." : ""}</p>
        <button className="button primary" type="button" onClick={executePaperTrade} disabled={busy}>{busy ? "Submitting…" : initialDecision ? "Execute Paper Trade" : "Submit Manual Paper Trade"}</button>
      </div> : null}
      {status ? <p className={status.startsWith("Rules rejected") ? "formMessage error" : "formMessage success"}>{status}</p> : null}
    </form>
  );
}

export function RecommendationWorkflow({ portfolio, recent }: { portfolio: PortfolioSummary; recent: AIDecision[] }) {
  const router = useRouter();
  const [decisions, setDecisions] = useState(recent);
  const [selected, setSelected] = useState<AIDecision | undefined>(recent.find((item) => ["buy", "sell"].includes(item.action_suggestion)));
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const fallbackActive = decisions[0]?.provider === "deterministic_fallback";

  async function analyze() {
    setBusy(true);
    setStatus("Running research analysis…");
    const result = await clientApi<AIDecision[]>(`/ai/analyze?portfolio_id=${portfolio.id}`, { method: "POST" });
    setBusy(false);
    if (!result.ok) { setStatus(result.error); return; }
    setDecisions(result.data);
    setSelected(result.data.find((item) => ["buy", "sell"].includes(item.action_suggestion)));
    setStatus("Analysis complete. Review a proposal before taking action.");
    router.refresh();
  }

  return (
    <div className="workflowStack">
      <div className="safetyNotice"><strong>AI proposes. Rules govern. You decide.</strong> Analysis creates advisory records only; it never creates an order.</div>
      {fallbackActive ? <div className="warningBanner"><strong>Fallback result — not an AI recommendation.</strong><span>Restore Ollama on the backend host before relying on model analysis. Fallback holds cannot be submitted as trades.</span></div> : null}
      <button className="button primary" type="button" onClick={analyze} disabled={busy}>{busy ? "Analyzing…" : "Run AI analysis"}</button>
      {status ? <p className="formMessage">{status}</p> : null}
      {decisions.length ? <div className="recommendationGrid">{decisions.map((decision) => {
        const rulesStatus = String(decision.rules_result?.status ?? "pending_user_confirmation");
        return <button type="button" key={decision.id} className={`recommendationCard ${selected?.id === decision.id ? "selected" : ""}`} onClick={() => setSelected(decision)}>
          <span className="statusPill">{decision.action_suggestion.toUpperCase()}</span>
          <strong>{decision.ticker}</strong>
          <span>{(decision.confidence_score * 100).toFixed(0)}% confidence</span>
          <small>{decision.explanation}</small>
          <small>Provider: {decision.provider === "deterministic_fallback" ? "deterministic fallback" : decision.model_name || "Ollama"}</small>
          <small>Rule state: {rulesStatus.replaceAll("_", " ")}</small>
        </button>;
      })}</div> : <p className="emptyState">No recommendations yet. Run analysis to begin.</p>}
      {selected && ["buy", "sell"].includes(selected.action_suggestion) ? <OrderForm portfolios={[portfolio]} initialDecision={selected} /> : selected ? <p className="emptyState">This recommendation proposes no trade.</p> : null}
    </div>
  );
}
