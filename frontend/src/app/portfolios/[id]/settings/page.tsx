import Link from "next/link";
import { SectionCard } from "@/components/cards";
import { AppLayout } from "@/components/layout";
import { PortfolioSettingsForm } from "@/components/portfolio-forms";
import { fetchPortfolio } from "@/lib/api";

export default async function PortfolioSettingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const portfolio = await fetchPortfolio(id);

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Portfolio Tuning</p>
          <h1>{portfolio?.name ?? "Portfolio settings"}</h1>
        </div>
        <Link className="button secondary" href={portfolio ? `/portfolios/${portfolio.id}` : "/portfolios"}>
          Back
        </Link>
      </div>
      <SectionCard title="Rules and controls" subtitle="Paper-trading guardrails">
        {portfolio ? <PortfolioSettingsForm portfolio={portfolio} /> : <p className="muted">Portfolio not found.</p>}
      </SectionCard>
    </AppLayout>
  );
}
