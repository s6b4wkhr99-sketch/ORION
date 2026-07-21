import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const CAMPAIGN_ROUTES = ["/recommendations", "/campaign-center", "/campaigns", "/learning"];

const LEGACY_REDIRECTS: Record<string, string> = {
  "/dashboard": "/mission-control",
  "/executive": "/mission-control",
  "/retail": "/market-intelligence",
  "/roi": "/mission-control",
  "/campaign-center": "/recommendations",
  "/settings": "/admin",
  "/explorer": "/market-intelligence",
  "/states": "/market-intelligence",
  "/zip": "/market-intelligence",
};

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (pathname === "/customers" || pathname.startsWith("/customers/")) {
    if (process.env.NEXT_PUBLIC_SHOW_CUSTOMER_DATABASE !== "true") {
      return NextResponse.redirect(new URL("/mission-control", request.url));
    }
    return NextResponse.next();
  }

  const legacyTarget = LEGACY_REDIRECTS[pathname];
  if (legacyTarget) {
    return NextResponse.redirect(new URL(`${legacyTarget}${search}`, request.url));
  }

  const showCampaign = process.env.NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES === "true";
  if (!showCampaign) {
    const blocked = CAMPAIGN_ROUTES.some(
      (route) => pathname === route || pathname.startsWith(`${route}/`),
    );
    if (blocked) {
      return NextResponse.redirect(new URL("/mission-control", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard",
    "/executive",
    "/retail",
    "/roi",
    "/campaign-center",
    "/settings",
    "/explorer",
    "/states",
    "/zip",
    "/customers",
    "/customers/:path*",
    "/recommendations/:path*",
    "/campaigns/:path*",
    "/learning/:path*",
  ],
};
