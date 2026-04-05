import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";

export default function PortfolioDetailPage() {
  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Portfolio Detail</p>
          <h1>Single portfolio view</h1>
        </div>
      </div>
      <SectionCard title="Overview" subtitle="Starter detail page for holdings, allocations, and rules">
        <p className="muted">
          Wire this page to `/api/v1/portfolios/:id` for positions, rules, P&amp;L, and queued orders.
        </p>
      </SectionCard>
    </AppLayout>
  );
}
