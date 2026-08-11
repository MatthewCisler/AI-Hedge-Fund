"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus(mode === "login" ? "Signing in…" : "Creating account…");
    const form = new FormData(event.currentTarget);
    const payload = {
      email: String(form.get("email") ?? "").trim(),
      password: String(form.get("password") ?? ""),
      ...(mode === "register" ? { full_name: String(form.get("full_name") ?? "").trim() || null } : {}),
    };
    const response = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: mode, payload }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
      setStatus(detail ?? "Authentication failed.");
      setBusy(false);
      return;
    }
    router.replace(mode === "register" ? "/portfolios" : searchParams.get("next") || "/dashboard");
    router.refresh();
  }

  return (
    <form className="authCard" onSubmit={submit}>
      <p className="eyebrow">{mode === "login" ? "Welcome back" : "Paper trading setup"}</p>
      <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
      {mode === "register" ? <label>Full name<input name="full_name" autoComplete="name" placeholder="Alex Investor" /></label> : null}
      <label>Email<input name="email" type="email" autoComplete="email" required placeholder="you@example.com" /></label>
      <label>Password<input name="password" type="password" minLength={8} autoComplete={mode === "login" ? "current-password" : "new-password"} required placeholder="At least 8 characters" /></label>
      <button type="submit" className="button primary" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Register"}</button>
      {status ? <p className={status.includes("failed") || status.includes("Invalid") ? "formMessage error" : "formMessage"}>{status}</p> : null}
      <p className="muted">{mode === "login" ? <>New here? <Link href="/register">Create an account</Link>.</> : <>Already registered? <Link href="/login">Sign in</Link>.</>}</p>
    </form>
  );
}
