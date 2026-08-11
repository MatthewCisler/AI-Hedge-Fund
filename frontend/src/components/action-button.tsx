"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { clientApi } from "@/lib/client-api";

type ActionButtonProps = {
  label: string;
  path: string;
  method?: "GET" | "POST" | "DELETE";
  variant?: "primary" | "secondary";
};

export function ActionButton({ label, path, method = "POST", variant = "secondary" }: ActionButtonProps) {
  const [status, setStatus] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function runAction() {
    setBusy(true);
    setStatus("Running…");
    const result = await clientApi<{ message?: string; status?: string; failure_category?: string; mode?: string }>(path, { method });
    const summary = result.ok ? [result.data?.status, result.data?.mode, result.data?.failure_category].filter(Boolean).join(" · ") : "";
    setStatus(result.ok ? (result.data?.message ?? (summary || "Completed successfully.")) : result.error);
    setBusy(false);
    if (result.ok) router.refresh();
  }

  return (
    <div className="actionControl">
      <button className={`button ${variant}`} type="button" disabled={busy} onClick={runAction}>
        {label}
      </button>
      {status ? <span className={status.includes("failed") || status.includes("Failed") ? "formMessage error" : "formMessage"}>{status}</span> : null}
    </div>
  );
}
