"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { PortfolioDetail, PortfolioRule, RiskProfile } from "@/lib/types";
import { clientApi } from "@/lib/client-api";
const riskProfiles: RiskProfile[] = ["safe", "balanced", "risky", "custom"];
const benchmarks = ["SPY", "QQQ", "DIA", "60_40"];

function tickerList(value: string) {
  return value
    .split(/[,\s]+/)
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}

function pct(value: FormDataEntryValue | null) {
  return Math.min(100, Math.max(0, Number(value ?? 0)));
}

export function CreatePortfolioForm() {
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus("Creating…");
    const data = new FormData(event.currentTarget);
    const name = String(data.get("name") ?? "").trim();
    const initial = Number(data.get("initial_investment") ?? 0);
    if (!name) {
      setStatus("Portfolio name is required.");
      setBusy(false);
      return;
    }
    if (initial <= 0) {
      setStatus("Initial investment must be positive.");
      setBusy(false);
      return;
    }
    const result = await clientApi<PortfolioDetail>("/portfolios", { method: "POST", body: JSON.stringify({
      name,
      initial_investment: initial,
      risk_profile: data.get("risk_profile"),
      benchmark_symbol: data.get("benchmark_symbol"),
      rules: {
        etf_allowed: data.get("etf_allowed") === "on",
        max_position_size_pct: pct(data.get("max_position_size_pct")),
        max_daily_trades: Math.max(0, Number(data.get("max_daily_trades") ?? 0)),
        max_weekly_trades: Math.max(0, Number(data.get("max_weekly_trades") ?? 0)),
        rebalance_threshold: pct(data.get("rebalance_threshold")),
        sector_concentration_limit: pct(data.get("sector_concentration_limit")),
        cash_reserve_pct: pct(data.get("cash_reserve_pct")),
        cooldown_minutes_per_ticker: Math.max(0, Number(data.get("cooldown_minutes_per_ticker") ?? 0)),
        minimum_liquidity_volume: Math.max(0, Number(data.get("minimum_liquidity_volume") ?? 0)),
        allow_queued_after_hours: true,
        allowed_tickers: [],
        blocked_tickers: [],
        aggressiveness: pct(data.get("aggressiveness")),
        after_hours_news_scanning: true,
      },
    }) });
    if (!result.ok) {
      setStatus(result.error);
      setBusy(false);
      return;
    }
    router.push(`/portfolios/${result.data.id}/settings`);
    router.refresh();
  }

  return (
    <form className="settingsForm" onSubmit={submit}>
      <div className="formGrid">
        <label>
          Portfolio name
          <input name="name" required placeholder="Core AI Paper" />
        </label>
        <label>
          Initial paper investment
          <input name="initial_investment" type="number" min="1" step="100" required defaultValue="100000" />
        </label>
        <label>
          Risk profile
          <select name="risk_profile" defaultValue="balanced">
            {riskProfiles.map((profile) => (
              <option key={profile} value={profile}>
                {profile}
              </option>
            ))}
          </select>
        </label>
        <label>
          Benchmark
          <select name="benchmark_symbol" defaultValue="SPY">
            {benchmarks.map((benchmark) => (
              <option key={benchmark} value={benchmark}>
                {benchmark === "60_40" ? "60/40" : benchmark}
              </option>
            ))}
          </select>
        </label>
        <label>
          Max position %
          <input name="max_position_size_pct" type="number" min="0" max="100" defaultValue="12" />
        </label>
        <label>
          Max daily trades
          <input name="max_daily_trades" type="number" min="0" defaultValue="4" />
        </label>
        <label>
          Rebalance threshold %
          <input name="rebalance_threshold" type="number" min="0" max="100" defaultValue="5" />
        </label>
        <label>
          Cooldown minutes per ticker
          <input name="cooldown_minutes_per_ticker" type="number" min="0" defaultValue="90" />
        </label>
        <label>
          Minimum volume/liquidity
          <input name="minimum_liquidity_volume" type="number" min="0" defaultValue="750000" />
        </label>
        <label>
          Aggressiveness
          <input name="aggressiveness" type="range" min="0" max="100" defaultValue="50" />
        </label>
      </div>
      <label className="checkboxLine">
        <input name="etf_allowed" type="checkbox" defaultChecked />
        Allow ETFs
      </label>
      <button className="button primary" type="submit" disabled={busy}>
        {busy ? "Creating…" : "Create portfolio"}
      </button>
      {status ? <p className="muted">{status}</p> : null}
    </form>
  );
}

export function PortfolioSettingsForm({ portfolio }: { portfolio: PortfolioDetail }) {
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  const rules = portfolio.rules;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus("Saving…");
    const data = new FormData(event.currentTarget);
    const riskProfile = String(data.get("risk_profile") ?? portfolio.risk_profile) as RiskProfile;
    const active = data.get("is_active") === "on";
    const ruleBody: PortfolioRule = {
      portfolio_id: portfolio.id,
      max_position_size_pct: pct(data.get("max_position_size_pct")),
      max_daily_trades: Math.max(0, Number(data.get("max_daily_trades") ?? 0)),
      max_weekly_trades: Math.max(0, Number(data.get("max_weekly_trades") ?? 0)),
      etf_allowed: data.get("etf_allowed") === "on",
      rebalance_threshold: pct(data.get("rebalance_threshold")),
      sector_concentration_limit: pct(data.get("sector_concentration_limit")),
      cash_reserve_pct: pct(data.get("cash_reserve_pct")),
      minimum_liquidity_volume: Math.max(0, Number(data.get("minimum_liquidity_volume") ?? 0)),
      allow_queued_after_hours: data.get("allow_queued_after_hours") === "on",
      cooldown_minutes_per_ticker: Math.max(0, Number(data.get("cooldown_minutes_per_ticker") ?? 0)),
      allowed_tickers: tickerList(String(data.get("allowed_tickers") ?? "")),
      blocked_tickers: tickerList(String(data.get("blocked_tickers") ?? "")),
      aggressiveness: pct(data.get("aggressiveness")),
      after_hours_news_scanning: data.get("after_hours_news_scanning") === "on",
    };

    const portfolioResult = await clientApi<PortfolioDetail>(`/portfolios/${portfolio.id}`, { method: "PATCH", body: JSON.stringify({
      risk_profile: riskProfile,
      is_active: active,
      benchmark_symbol: data.get("benchmark_symbol"),
    }) });
    const ruleResult = await clientApi<PortfolioRule>(`/portfolios/${portfolio.id}/rules`, { method: "PATCH", body: JSON.stringify(ruleBody) });
    setStatus(portfolioResult.ok && ruleResult.ok ? "Rules saved." : !portfolioResult.ok ? portfolioResult.error : !ruleResult.ok ? ruleResult.error : "Save failed.");
    setBusy(false);
    if (portfolioResult.ok && ruleResult.ok) {
      router.refresh();
    }
  }

  return (
    <form className="settingsForm" onSubmit={submit}>
      <div className="formGrid">
        <label>
          Risk profile
          <select name="risk_profile" defaultValue={portfolio.risk_profile}>
            {riskProfiles.map((profile) => (
              <option key={profile} value={profile}>
                {profile}
              </option>
            ))}
          </select>
        </label>
        <label>
          Benchmark
          <select name="benchmark_symbol" defaultValue={portfolio.benchmark_symbol}>
            {benchmarks.map((benchmark) => (
              <option key={benchmark} value={benchmark}>
                {benchmark === "60_40" ? "60/40" : benchmark}
              </option>
            ))}
          </select>
        </label>
        <label>
          Max position %
          <input name="max_position_size_pct" type="number" min="0" max="100" defaultValue={rules?.max_position_size_pct ?? 10} />
        </label>
        <label>
          Max sector concentration %
          <input name="sector_concentration_limit" type="number" min="0" max="100" defaultValue={rules?.sector_concentration_limit ?? 25} />
        </label>
        <label>
          Max daily trades
          <input name="max_daily_trades" type="number" min="0" defaultValue={rules?.max_daily_trades ?? 3} />
        </label>
        <label>
          Max weekly trades
          <input name="max_weekly_trades" type="number" min="0" defaultValue={rules?.max_weekly_trades ?? 15} />
        </label>
        <label>
          Cash reserve %
          <input name="cash_reserve_pct" type="number" min="0" max="100" defaultValue={rules?.cash_reserve_pct ?? 5} />
        </label>
        <label>
          Rebalance threshold %
          <input name="rebalance_threshold" type="number" min="0" max="100" defaultValue={rules?.rebalance_threshold ?? 5} />
        </label>
        <label>
          Cooldown minutes
          <input name="cooldown_minutes_per_ticker" type="number" min="0" defaultValue={rules?.cooldown_minutes_per_ticker ?? 60} />
        </label>
        <label>
          Minimum volume/liquidity
          <input name="minimum_liquidity_volume" type="number" min="0" defaultValue={rules?.minimum_liquidity_volume ?? 500000} />
        </label>
        <label>
          Aggressiveness
          <input name="aggressiveness" type="range" min="0" max="100" defaultValue={rules?.aggressiveness ?? 50} />
        </label>
      </div>
      <label>
        Allowed tickers
        <input name="allowed_tickers" defaultValue={(rules?.allowed_tickers ?? []).join(", ")} placeholder="AAPL, MSFT, SPY" />
      </label>
      <label>
        Blocked tickers
        <input name="blocked_tickers" defaultValue={(rules?.blocked_tickers ?? []).join(", ")} placeholder="TSLA, GME" />
      </label>
      <div className="toggleGrid">
        <label className="checkboxLine">
          <input name="etf_allowed" type="checkbox" defaultChecked={rules?.etf_allowed ?? true} />
          ETF permission
        </label>
        <label className="checkboxLine">
          <input name="after_hours_news_scanning" type="checkbox" defaultChecked={rules?.after_hours_news_scanning ?? true} />
          After-hours news scanning
        </label>
        <label className="checkboxLine">
          <input name="allow_queued_after_hours" type="checkbox" defaultChecked={rules?.allow_queued_after_hours ?? true} />
          Queue trades for next open
        </label>
        <label className="checkboxLine">
          <input name="is_active" type="checkbox" defaultChecked={portfolio.is_active} />
          Portfolio active
        </label>
      </div>
      <button className="button primary" type="submit" disabled={busy}>
        {busy ? "Saving…" : "Save tuning"}
      </button>
      {status ? <p className="muted">{status}</p> : null}
    </form>
  );
}
