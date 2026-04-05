import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";

export default function ReportsPage() {
  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Daily reports</p>
          <h1>Spreadsheet-style portfolio snapshots</h1>
        </div>
      </div>
      <SectionCard title="Generated reports" subtitle="Visible on the website and downloadable as CSV">
        <p className="muted">
          Hook this page to `/api/v1/reports` and `/api/v1/reports/generate` to browse and publish reports.
        </p>
      </SectionCard>
    </AppLayout>
  );
}
