import { NextRequest, NextResponse } from "next/server";

const protectedPaths = ["/dashboard", "/portfolios", "/trades", "/ai", "/benchmarks", "/reports", "/settings"];

export function middleware(request: NextRequest) {
  const authenticated = Boolean(request.cookies.get("paper_fund_session")?.value);
  const isProtected = protectedPaths.some((path) => request.nextUrl.pathname === path || request.nextUrl.pathname.startsWith(`${path}/`));
  if (isProtected && !authenticated) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(login);
  }
  if (authenticated && ["/login", "/register"].includes(request.nextUrl.pathname)) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/dashboard/:path*", "/portfolios/:path*", "/trades/:path*", "/ai/:path*", "/benchmarks/:path*", "/reports/:path*", "/settings/:path*", "/login", "/register"] };
