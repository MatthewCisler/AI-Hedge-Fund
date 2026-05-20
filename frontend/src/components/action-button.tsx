"use client";

import { useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type ActionButtonProps = {
  label: string;
  path: string;
  method?: "POST" | "DELETE";
  variant?: "primary" | "secondary";
};

export function ActionButton({ label, path, method = "POST", variant = "secondary" }: ActionButtonProps) {
  const [status, setStatus] = useState<string>("");

  async function runAction() {
    setStatus("Running...");
    try {
      const response = await fetch(`${API_BASE_URL}${path}`, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": "1",
        },
      });
      setStatus(response.ok ? "Done. Refresh to see updates." : `Failed: ${response.status}`);
    } catch {
      setStatus("Failed to reach backend.");
    }
  }

  return (
    <div className="actionControl">
      <button className={`button ${variant}`} type="button" onClick={runAction}>
        {label}
      </button>
      {status ? <span className="muted">{status}</span> : null}
    </div>
  );
}
