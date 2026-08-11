import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const action = body.action === "register" ? "register" : "login";
  const response = await fetch(`${API_BASE_URL}/auth/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body.payload),
    cache: "no-store",
  });
  const data = await response.json().catch(() => ({ detail: "Authentication failed." }));
  const nextResponse = NextResponse.json(data, { status: response.status });
  if (response.ok && data.access_token) {
    nextResponse.cookies.set(SESSION_COOKIE, data.access_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24,
    });
  }
  return nextResponse;
}

export async function DELETE() {
  const response = NextResponse.json({ status: "logged_out" });
  response.cookies.set(SESSION_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
  return response;
}
