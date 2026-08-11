import Link from "next/link";
import { ReactNode } from "react";
import { fetchSession } from "@/lib/api";
import { LogoutButton } from "@/components/logout-button";

type LayoutProps = {
  children: ReactNode;
};

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/portfolios", label: "Portfolios" },
  { href: "/settings", label: "Rules" },
  { href: "/trades", label: "Trades" },
  { href: "/ai", label: "AI Decisions" },
  { href: "/benchmarks", label: "Benchmarks" },
  { href: "/reports", label: "Reports" },
];

export async function AppLayout({ children }: LayoutProps) {
  const session = await fetchSession();
  return (
    <div className="shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Educational Simulation</p>
          <h1>Paper Hedge Fund</h1>
          <p className="muted">
            Multi-user paper portfolios with local AI research and deterministic controls.
          </p>
        </div>
        <nav className="sideNav">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="navLink">
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sessionPanel">
          <span className={`modePill ${session?.broker_mode === "alpaca-paper" ? "paper" : "demo"}`}>
            {session?.broker_mode === "alpaca-paper" ? "Alpaca paper" : "Demo simulation"}
          </span>
          <small>{session?.full_name || session?.email || "Authenticated user"}</small>
          <LogoutButton />
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
