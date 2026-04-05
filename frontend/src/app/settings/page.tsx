import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";

export default function SettingsPage() {
  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Rules</p>
          <h1>Risk profile and execution constraints</h1>
        </div>
      </div>
      <SectionCard title="Portfolio rules" subtitle="Editable per user and per portfolio">
        <form className="settingsForm">
          <label>
            Max position size %
            <input type="number" defaultValue={10} />
          </label>
          <label>
            Max daily trades
            <input type="number" defaultValue={3} />
          </label>
          <label>
            Rebalance threshold
            <input type="number" defaultValue={5} />
          </label>
          <label>
            Sector concentration limit
            <input type="number" defaultValue={25} />
          </label>
          <label>
            Minimum liquidity volume
            <input type="number" defaultValue={500000} />
          </label>
          <button type="submit" className="button primary">
            Save rules
          </button>
        </form>
      </SectionCard>
    </AppLayout>
  );
}
