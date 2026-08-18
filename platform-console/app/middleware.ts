import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, createApiKeySessionToken, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import { resolveApiKeyAuth } from "@/lib/api-keys";
import { checkAndTouchSession } from "@/lib/active-sessions";
import { clientIpFrom } from "@/lib/request-meta";

// Runs on the Node.js middleware runtime (`export const runtime = "nodejs"`
// below -- Next.js 15's node-middleware support, not the edge runtime this
// file used before this pass), specifically so it can resolve a real
// `Authorization: Bearer pk_live_...` API key against the live
// `platform-console-api-keys` k8s Secret via lib/api-keys.ts -> lib/k8s.ts,
// which needs Node's fs/https to read the pod's own ServiceAccount token
// (lib/k8s.ts's own header comment: "never import this from middleware" --
// true under the edge runtime, no longer true once this file opts into the
// Node.js runtime). `jose` (session JWT sign/verify) is edge-safe and
// unaffected by this move; every session-cookie code path below is
// unchanged from before.

// Paths that must stay reachable without a session: the login page itself,
// the login API route (issues the session), static assets, and Next.js
// internals. Everything else is a gated dashboard route.
const PUBLIC_PATHS = [
  "/login",
  "/api/login",
  "/api/auth/gotrue-login",
  "/api/auth/gotrue-signup",
  // Third, distinct real auth path -- external OIDC federation. Both legs
  // must stay reachable without an existing session: /oidc-login issues
  // the redirect to the real external provider, /oidc-callback is where
  // that provider redirects back to before this app has minted anything.
  "/api/auth/oidc-login",
  "/api/auth/oidc-callback",
  // Public status page -- matches AWS Service Health Dashboard /
  // statuspage.io convention (no login to view real-time platform status).
  "/status",
  "/api/status",
];

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.includes(pathname)) return true;
  if (pathname.startsWith("/_next/")) return true;
  if (pathname === "/favicon.ico") return true;
  return false;
}

function isApiPath(pathname: string): boolean {
  return pathname.startsWith("/api/");
}

export const runtime = "nodejs";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const requestId = newRequestId();

  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const apiRoute = isApiPath(pathname);
  const cookieToken = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  let session = cookieToken ? await verifySessionToken(cookieToken) : null;
  let forwardHeaders: Headers | null = null;
  let revokedBySessionRegistry = false;

  // Real, second authentication method (alongside the browser session
  // cookie above): a bound API key, presented as a standard
  // `Authorization: Bearer pk_live_...` header -- exactly how a real
  // hyperscaler PaaS's own CLI/SDK authenticates, and the reason this
  // console is genuinely programmatically drivable, not only
  // browser-session-drivable. Deliberately scoped to API routes only
  // (never page routes -- a Bearer header has no business driving
  // server-rendered page navigation) and only attempted when no session
  // cookie already resolved one (a real browser session always wins).
  if (!session && apiRoute) {
    const authHeader = request.headers.get("authorization");
    if (authHeader?.startsWith("Bearer ")) {
      const presentedKey = authHeader.slice("Bearer ".length).trim();
      const resolved = await resolveApiKeyAuth(presentedKey);
      if (resolved) {
        // Mints a REAL session token of the exact same JWT shape every
        // other session already is (lib/session.ts's
        // createApiKeySessionToken), then forwards it as this request's
        // own Cookie header -- so every downstream route handler's
        // existing requireSession()/requireRole() call (unchanged, reads
        // only the cookie) transparently authenticates this request too.
        // This IS the entire mechanism: an alternate authentication
        // method feeding the exact same authorization layer, never a
        // parallel one -- zero route files were edited to support this.
        // Deliberately deterministic, not a fresh crypto.randomUUID() --
        // this path mints a brand-new app-local JWT on literally every
        // request (there is no persistent cookie for a Bearer-token
        // caller), so a random sessionId here would register a brand-new
        // registry row on every single request instead of one row per key
        // that heartbeats over time. See lib/active-sessions.ts's module
        // doc for the full reasoning and how checkAndTouchSession's
        // self-heal-create branch below stands in for this path's missing
        // separate login step.
        const apiKeySessionId = `apikey-${resolved.keyId}`;
        const apiKeyToken = await createApiKeySessionToken(
          resolved.identifier,
          resolved.role,
          resolved.keyId,
          apiKeySessionId,
        );
        forwardHeaders = new Headers(request.headers);
        forwardHeaders.set("cookie", `${SESSION_COOKIE_NAME}=${apiKeyToken}`);
        session = await verifySessionToken(apiKeyToken);
      }
    }
  }

  // Real Active Session Management enforcement (lib/active-sessions.ts):
  // an otherwise-valid, unexpired JWT is rejected here if its own
  // `sessionId` claim resolves to a registry row marked revoked -- the one
  // check that makes revocation genuinely real rather than merely hiding a
  // session from the /sessions list. `session.sessionId` is absent only
  // for a cookie minted before this claim existed (see lib/session.ts's
  // own doc comment) -- that legacy case is intentionally left unchecked,
  // riding out its own unchanged expiry, exactly as it would have before
  // this pass. A registry lookup failure (Postgres genuinely unreachable)
  // fails OPEN, disclosed in lib/active-sessions.ts's own module doc --
  // this is the one and only place that trade-off is made; a row that
  // WAS successfully read back as `revoked: true` is never let through.
  if (session?.sessionId) {
    const check = await checkAndTouchSession(session.sessionId, {
      identifier: session.sub,
      authProvider: session.authProvider,
      ip: clientIpFrom(request),
      userAgent: request.headers.get("user-agent"),
    });
    if (check.ok && check.data.revoked) {
      session = null;
      revokedBySessionRegistry = true;
    }
  }

  if (!session) {
    if (apiRoute) {
      // A real API client (curl, a CLI, an SDK) gets a real JSON 401, not
      // a 307 redirect to an HTML login page -- the correct hyperscaler-
      // API convention, and what makes a missing/invalid/revoked key's
      // rejection actually machine-checkable by a script rather than
      // requiring HTML-scraping a redirect target. `reason` is only ever
      // set on the real, specific "this exact session was revoked via
      // /sessions" path (never on a plain missing/malformed/expired
      // token), so a caller -- or this control's own live verification --
      // can tell the two 401s apart without guessing from status code
      // alone.
      return NextResponse.json(
        {
          error: "unauthenticated",
          ...(revokedBySessionRegistry ? { reason: "session revoked" } : {}),
        },
        { status: 401 },
      );
    }
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const response = forwardHeaders
    ? NextResponse.next({ request: { headers: forwardHeaders } })
    : NextResponse.next();
  response.headers.set("x-request-id", requestId);

  // Structured audit-log line for this authenticated request. Status is
  // recorded as 200 at the point middleware allows the request through --
  // middleware runs before the route handler produces its own status, so
  // this records "request was authenticated and forwarded", not the
  // downstream handler's final status code. `actor` is the API key's
  // bound identifier when this request authenticated via Bearer token,
  // same field, same shape as a cookie-authenticated request's actor.
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
