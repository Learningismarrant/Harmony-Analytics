/**
 * Next.js middleware — auth guard
 *
 * Routes are protected by checking the presence of the `harmony_session` cookie,
 * which is a lightweight flag set by the client on login/register and cleared on
 * logout. The actual token validity is confirmed by /auth/refresh on first API call.
 *
 * Public routes: /login, /register, /invite/*
 */
import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/register", "/invite"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow static files and API routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Check for session cookie set by auth.store on login/register
  const hasSession = request.cookies.has("harmony_session");
  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
