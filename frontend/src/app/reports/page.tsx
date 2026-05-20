import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";
import { ActionButton } from "@/components/action-button";
import { fetchDashboard, fetchReports, reportCsvUrl } from "@/lib/api";

export default async function ReportsPage() {
  const reports = await fetchReports();
  const dashboard = await fetchDashboard();
  const portfolio = dashboard?.portfolios[0];

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Daily reports</p>
          <h1>Spreadsheet-style portfolio snapshots</h1>
        </div>
        {portfolio ? (
          <div className="pageActions">
            <ActionButton label="Generate Report" path={`/reports/generate?portfolio_id=${portfolio.id}`} variant="primary" />
          </div>
        ) : null}
      </div>
      <SectionCard title="Generated reports" subtitle="Website-backed reports with CSV downloads">
        <div className="list">
          {reports.length ? (
            reports.map((report) => (
              <div key={report.id} className="listRow stacked">
                <div>
                  <strong>{report.report_date}</strong>
                  <p className="muted">{report.narrative ?? "Daily portfolio report"}</p>
                  <div className="reportRows">
                    {report.rows.slice(0, 8).map((row) => (
                      <span key={row.id}>
                        {row.section}: {row.label} = {row.value}
                      </span>
                    ))}
                  </div>
                </div>
                <a className="button secondary" href={reportCsvUrl(report.id)}>
                  CSV
                </a>
              </div>
            ))
          ) : (
            <p className="muted">No reports generated yet.</p>
          )}
        </div>
      </SectionCard>
    </AppLayout>
  );
}
