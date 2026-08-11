import { Suspense } from "react";
import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return <main className="authPage"><Suspense fallback={<p>Loading…</p>}><AuthForm mode="register" /></Suspense></main>;
}
