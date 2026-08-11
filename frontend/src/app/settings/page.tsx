import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";
import { ActionButton } from "@/components/action-button";
import { fetchDashboard, fetchRiskDefaults } from "@/lib/api";

export default async function SettingsPage() {
  const [defaults, dashboard] = await Promise.all([fetchRiskDefaults(), fetchDashboard()]);
  const portfolio = dashboard?.portfolios[0];

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Rules</p>
          <h1>Risk profile and execution constraints</h1>
        </div>
        <div className="pageActions">
          <ActionButton label="Test Ollama connection" path="/ai/status" method="GET" />
          <ActionButton label="Test Alpaca paper connection" path="/trades/broker/status" method="GET" />
          <ActionButton label="Refresh paper account" path="/trades/broker/account" method="GET" />
          {portfolio ? <ActionButton label="Generate one AI recommendation" path={`/ai/analyze?portfolio_id=${portfolio.id}`} /> : null}
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
