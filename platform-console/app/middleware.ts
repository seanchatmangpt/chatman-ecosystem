import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";

// Paths that must stay reachable without a session: the login page itself,
// the login API route (issues the session), static assets, and Next.js
// internals. Everything else is a gated dashboard route.
const PUBLIC_PATHS = ["/login", "/api/login"];

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.includes(pathname)) return true;
  if (pathname.startsWith("/_next/")) return true;
  if (pathname === "/favicon.ico") return true;
  return false;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const requestId = newRequestId();

  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  if (!session) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const response = NextResponse.next();
  response.headers.set("x-request-id", requestId);

  // Structured audit-log line for this authenticated request. Status is
  // recorded as 200 at the point middleware allows the request through --
  // middleware runs before the route handler produces its own status, so
  // this records "request was authenticated and forwarded", not the
  // downstream handler's final status code.
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: request.method,
    path: pathname,
    status: 200,
    requestId,
  });

  return response;
}

export const config = {
  matcher: [
    /*
     * Match every request path except:
     * - _next/static, _next/image (build assets)
     * - favicon.ico
     * These are excluded purely to keep the audit log free of noise from
     * asset requests; the actual auth check above is what gates access.
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
