import { Suspense } from "react";
import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return <main className="authPage"><Suspense fallback={<p>Loading…</p>}><AuthForm mode="login" /></Suspense></main>;
}
