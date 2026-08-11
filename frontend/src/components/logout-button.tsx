"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  async function logout() {
    setBusy(true);
    await fetch("/api/session", { method: "DELETE" });
    router.replace("/login");
    router.refresh();
  }
  return <button className="button secondary" type="button" disabled={busy} onClick={logout}>{busy ? "Signing out…" : "Log out"}</button>;
}
