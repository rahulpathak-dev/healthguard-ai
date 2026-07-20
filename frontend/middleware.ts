import { NextRequest, NextResponse } from "next/server";

const protectedPaths = ["/account", "/dashboard", "/profiles", "/chat"];

export function middleware(request: NextRequest) {
  const isProtected = protectedPaths.some((path) => request.nextUrl.pathname.startsWith(path));
  const hasAccessCookie = request.cookies.has("hg_access");
  if (isProtected && !hasAccessCookie) {
    const login = new URL("/auth/login", request.url);
    login.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(login);
  }
  if (request.nextUrl.pathname.startsWith("/auth/login") && hasAccessCookie) {
    return NextResponse.redirect(new URL("/account", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/account/:path*", "/dashboard/:path*", "/profiles/:path*", "/chat/:path*", "/auth/login"] };
