import { NextRequest, NextResponse } from "next/server";
import {
  buildAuthorizeUrl,
  generateNonce,
  generatePkcePair,
  generateState,
} from "@/lib/oidc-federation";
import { createOidcTransactionToken, OIDC_TXN_COOKIE_NAME } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSecureRequest } from "@/lib/request-meta";

// Third, distinct real auth path -- external OIDC federation. This is a
// plain GET (a real full-page browser navigation the "Sign in with our IdP"
// button on /login points at with a real <a href>, not a fetch() call),
// because its whole job is to issue a real 302 redirect to a REAL external
// provider's real /authorize endpoint -- see lib/oidc-federation.ts's
// module doc for which provider and why. Public path (middleware.ts) --
// this route mints no session, it only starts the federation handshake.
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const next = request.nextUrl.searchParams.get("next") ?? "/";

  const state = generateState();
  const nonce = generateNonce();
  const { codeVerifier, codeChallenge } = generatePkcePair();

  let authorizeUrl: string;
  try {
    authorizeUrl = await buildAuthorizeUrl({ state, nonce, codeChallenge });
  } catch (err) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "anonymous",
      method: "GET",
      path: "/api/auth/oidc-login",
      status: 502,
      requestId,
    });
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: `external OIDC provider unreachable or misconfigured: ${message}` },
      { status: 502 },
    );
  }

  const txnToken = await createOidcTransactionToken({ state, nonce, codeVerifier, next });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "anonymous",
    method: "GET",
    path: "/api/auth/oidc-login",
    status: 302,
    requestId,
  });

  const response = NextResponse.redirect(authorizeUrl, { status: 302 });
  response.cookies.set(OIDC_TXN_COOKIE_NAME, txnToken, {
    httpOnly: true,
    secure: isSecureRequest(request),
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 10,
  });
  return response;
}
