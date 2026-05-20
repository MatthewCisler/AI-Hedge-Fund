import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";
import { ActionButton } from "@/components/action-button";
import { fetchRiskDefaults } from "@/lib/api";

export default async function SettingsPage() {
  const defaults = await fetchRiskDefaults();

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Rules</p>
          <h1>Risk profile and execution constraints</h1>
        </div>
        <div className="pageActions">
          <ActionButton label="Run Intraday Analysis" path="/jobs/intraday-analysis" />
          <ActionButton label="Run Evening Scan" path="/jobs/evening-scan" />
          <ActionButton label="Daily Reports" path="/jobs/daily-reports" />
        </div>
      </div>
      <SectionCard title="Risk profile defaults" subtitle="Portfolio rules are editable through the API per portfolio">
        <div className="profileGrid">
          {Object.entries(defaults).map(([profile, rules]) => (
            <div key={profile} className="profilePanel">
              <h3>{profile}</h3>
              <div className="ruleList">
                {Object.entries(rules).map(([name, value]) => (
                  <div key={name} className="listRow">
                    <span>{name.replaceAll("_", " ")}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </AppLayout>
  );
}
