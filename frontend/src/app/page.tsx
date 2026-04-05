import Link from "next/link";

export default function HomePage() {
  return (
    <main className="landing">
      <div className="hero">
        <p className="eyebrow">Paper Trading Only</p>
        <h1>Build, test, and review hedge-fund-style strategies without risking real money.</h1>
        <p className="muted">
          Local AI can rank ideas, but deterministic rules decide whether anything gets queued or
          sent to Alpaca paper trading.
        </p>
        <div className="heroActions">
          <Link href="/register" className="button primary">
            Create account
          </Link>
          <Link href="/dashboard" className="button secondary">
            Open dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
