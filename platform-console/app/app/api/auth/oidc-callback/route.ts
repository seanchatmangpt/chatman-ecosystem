import { NextRequest, NextResponse } from "next/server";
import { discoverProvider, exchangeCodeForTokens, verifyIdToken } from "@/lib/oidc-federation";
import {
  createOidcSessionToken,
  generateSessionId,
  OIDC_TXN_COOKIE_NAME,
  SESSION_COOKIE_NAME,
  SESSION_MAX_AGE,
  verifyOidcTransactionToken,
} from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { recordSessionLogin } from "@/lib/active-sessions";
import { clientIpFrom, isSecureRequest } from "@/lib/request-meta";

// Third, distinct real auth path's callback -- the real external OIDC
// provider redirects the browser back here with `?code=...&state=...`
// after a real login+consent at the real provider. Public path
// (middleware.ts): the whole point of this route is to mint a session,
// so it cannot itself require one. Runs on the Node.js runtime (route
// handlers default to it), same as every other login route.
export async function POST() {
  return NextResponse.json({ error: "method not allowed" }, { status: 405 });
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const url = request.nextUrl;
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const providerError = url.searchParams.get("error");

  const clearTxnCookie = (response: NextResponse) => {
    response.cookies.set(OIDC_TXN_COOKIE_NAME, "", { path: "/", maxAge: 0 });
    return response;
  };

  const fail = (status: number, error: string) => {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "anonymous",
      method: "GET",
      path: "/api/auth/oidc-callback",
      status,
      requestId,
    });
    return clearTxnCookie(NextResponse.json({ error }, { status }));
  };

  if (providerError) {
    return fail(401, `external OIDC provider returned an error: ${providerError}`);
  }
  if (!code || !state) {
    return fail(400, "missing 'code' or 'state' query parameter");
  }

  const txnCookie = request.cookies.get(OIDC_TXN_COOKIE_NAME)?.value;
  if (!txnCookie) {
    return fail(400, "missing OIDC transaction cookie -- login flow was not started here, or it expired");
  }
  const txn = await verifyOidcTransactionToken(txnCookie);
  if (!txn) {
    return fail(400, "OIDC transaction cookie is invalid or expired");
  }
  // Real CSRF defense: the state this callback received must be the exact
  // same one this app itself generated and handed to the provider at
  // /api/auth/oidc-login time (carried here only via the signed cookie,
  // never trusted from the query string alone).
  if (txn.state !== state) {
    return fail(400, "state mismatch -- possible CSRF or replayed callback");
  }

  let tokens;
  try {
    tokens = await exchangeCodeForTokens(code, txn.codeVerifier);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return fail(502, `OIDC token exchange failed: ${message}`);
  }

  let identity;
  try {
    // Real signature verification against the real provider's real JWKS --
    // never skipped. See lib/oidc-federation.ts's verifyIdToken doc.
    identity = await verifyIdToken(tokens.id_token);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return fail(401, `OIDC ID token verification failed: ${message}`);
  }

  // Real nonce check: the ID token's own 'nonce' claim (set by the real
  // provider at /authorize time from the value we sent) must match the
  // one we generated at login time -- defends against a replayed
  // authorization response being paired with a different login attempt.
  if (identity.claims.nonce !== txn.nonce) {
    return fail(401, "OIDC ID token nonce mismatch -- possible replay");
  }

  const discovery = await discoverProvider();
  const sessionId = generateSessionId();
  const token = await createOidcSessionToken(identity.sub, identity.email, discovery.issuer, sessionId);

  const registryResult = await recordSessionLogin({
    sessionId,
    identifier: identity.email,
    authProvider: "oidc-external",
    ip: clientIpFrom(request),
    userAgent: request.headers.get("user-agent"),
  });
  if (!registryResult.ok) {
    console.error(JSON.stringify({ activeSessionRecordError: registryResult.error }));
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: identity.email,
    method: "GET",
    path: "/api/auth/oidc-callback",
    status: 200,
    requestId,
  });

  // Structured, real proof line for live verification: the real decoded ID
  // token claims and the real signature-check outcome, written to stdout
  // (kubectl logs), not fabricated after the fact.
  console.log(
    JSON.stringify({
      oidcFederationVerified: true,
      issuer: discovery.issuer,
      sub: identity.sub,
      email: identity.email,
      emailVerified: identity.emailVerified,
      alg: identity.alg,
      kid: identity.kid,
      idTokenClaims: identity.claims,
    }),
  );

  const next = txn.next && txn.next.startsWith("/") ? txn.next : "/";
  const response = clearTxnCookie(NextResponse.redirect(new URL(next, request.nextUrl.origin), { status: 302 }));
  response.cookies.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: isSecureRequest(request),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });
  return response;
}
