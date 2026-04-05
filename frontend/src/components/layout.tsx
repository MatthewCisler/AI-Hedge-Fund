import Link from "next/link";
import { ReactNode } from "react";

type LayoutProps = {
  children: ReactNode;
};

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/settings", label: "Rules" },
  { href: "/trades", label: "Trades" },
  { href: "/reports", label: "Reports" },
];

export function AppLayout({ children }: LayoutProps) {
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
        <nav>
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="navLink">
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
