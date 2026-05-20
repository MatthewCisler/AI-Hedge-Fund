"use client";

import { useRouter } from "next/navigation";
import { PortfolioSummary } from "@/lib/types";

export function PortfolioSwitcher({ portfolios, selectedId }: { portfolios: PortfolioSummary[]; selectedId?: number }) {
  const router = useRouter();

  return (
    <label className="switcher">
      Portfolio
      <select
        value={selectedId ?? portfolios[0]?.id ?? ""}
        onChange={(event) => router.push(`/portfolios/${event.target.value}`)}
        disabled={!portfolios.length}
      >
        {portfolios.length ? (
          portfolios.map((portfolio) => (
            <option key={portfolio.id} value={portfolio.id}>
              {portfolio.name}
            </option>
          ))
        ) : (
          <option>No portfolios</option>
        )}
      </select>
    </label>
  );
}
