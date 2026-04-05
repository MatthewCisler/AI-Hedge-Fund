import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";

export default function TradesPage() {
  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Trades</p>
          <h1>Orders, fills, and queued activity</h1>
        </div>
      </div>
      <SectionCard title="Order workflow" subtitle="Paper market orders for the MVP">
        <p className="muted">
          This page is ready for order history, trade fills, and queued next-open trade review.
        </p>
      </SectionCard>
    </AppLayout>
  );
}
