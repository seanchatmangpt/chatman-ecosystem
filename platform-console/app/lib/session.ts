/**
 * Hand-rolled session handling using `jose` (HS256 JWT), edge-runtime safe so
 * it can run inside middleware.ts without pulling in Node-only crypto APIs.
 *
 * Two session-issuing paths share this one cookie/JWT format, discriminated
 * by `authProvider`:
 *
 *  - "local-admin": the original, unchanged path. Exactly one seeded account
 *    (the admin), whose bcrypt password hash comes from the
 *    ADMIN_PASSWORD_HASH env var -- never a plaintext secret in source. See
 *    lib/credentials.ts for the password check (bcryptjs, which needs the
 *    Node.js runtime, so that check happens only in the login route
 *    handler, not in middleware).
 *  - "gotrue": additive identity-federation path. The session's `sub` is the
 *    real GoTrue (Supabase Auth) user id (a UUID), not a local username, and
 *    the session additionally carries the real GoTrue account's email. See
 *    lib/gotrue-auth.ts for the real signup/login calls against the live
 *    GoTrue REST API that produce the identity this session wraps.
 *  - "oidc-external": third, distinct real auth path -- external OIDC
 *    federation against a real, separate, standards-compliant OIDC
 *    provider (services/oidc-idp; see lib/oidc-federation.ts's module doc
 *    for the full "why this provider" reasoning). `sub` is the real `sub`
 *    claim from that provider's real, signature-verified ID token; `email`
 *    likewise. Structurally identical to the "gotrue" variant (both are
 *    "a real external identity, not this app's own admin account"), kept
 *    as a distinct `authProvider` literal so a session's JWT shape always
 *    discloses which of the three real login paths minted it, same
 *    convention as the "api-key" variant below.
 *
 * All three (four, counting api-key) paths mint the exact same kind of app-local HS256 JWT, signed with
 * this app's own AUTH_SECRET -- this app's session cookie is never a GoTrue
 * access token passed through, so every existing session consumer
 * (middleware.ts, the various /api/* route handlers' requireActor helpers)
 * keeps working unchanged: they all only ever read `session.sub`.
 *
 * Every variant below additionally carries a `sessionId` claim (Active
 * Session Management -- see lib/active-sessions.ts) -- a fresh
 * `crypto.randomUUID()` minted once per real login, distinct from every
 * other claim on the token (never derived from `sub`, which for the
 * API-key path is shared across every key belonging to the same identity
 * and would be useless as a per-session revocation handle). Optional on
 * the type (`sessionId?: string`) purely for backward compatibility: a
 * session cookie already issued before this claim existed still verifies
 * successfully (no forced logout on deploy), it just carries no
 * `sessionId` -- middleware.ts's registry check is a no-op for such a
 * token (nothing to look up), which is the correct, disclosed behavior for
 * a session minted under the old contract: it simply rides out its own
 * unchanged 8h expiry with no way to be force-revoked, exactly like every
 * session did before this pass.
 */
import { SignJWT, jwtVerify, type JWTPayload } from "jose";

const COOKIE_NAME = "platform_console_session";
const SESSION_TTL_SECONDS = 60 * 60 * 8; // 8 hours

export interface LocalAdminSessionPayload extends JWTPayload {
  sub: string; // username
  role: "admin";
  authProvider: "local-admin";
  sessionId?: string;
}

export interface GoTrueSessionPayload extends JWTPayload {
  sub: string; // real GoTrue user id (uuid)
  role: "authenticated";
  authProvider: "gotrue";
  email: string;
  sessionId?: string;
}

/**
 * Third session-issuing path: external OIDC federation (lib/oidc-federation.ts,
 * app/api/auth/oidc-callback/route.ts). `sub` is the real `sub` claim from
 * the external provider's real, signature-verified ID token; `email`
 * likewise. `idpIssuer` records which real provider vouched for this
 * identity (useful once more than one external OIDC provider is ever
 * wired up) -- purely informational, never itself an authorization input.
 */
export interface OidcSessionPayload extends JWTPayload {
  sub: string; // real 'sub' claim from the external provider's verified ID token
  role: "authenticated";
  authProvider: "oidc-external";
  email: string;
  idpIssuer: string;
  sessionId?: string;
}

/**
 * Third session-issuing path: a real API key (lib/api-keys.ts), presented
 * as `Authorization: Bearer pk_live_...` and resolved by middleware.ts
 * against the live `platform-console-api-keys` Secret. `sub` is the API
 * key's bound identifier (an org-roles identifier -- an email, or
 * "admin"), and `boundRole` is the app-level role (viewer/member/owner)
 * fixed at key creation time -- never re-derived from the ConfigMap
 * lib/authz.ts's getRoleFor otherwise reads, since an API key's role
 * cannot change after issuance (only revocation changes anything about an
 * existing key). Deliberately kept structurally separate from `role`
 * (this claim is always the literal "api-key", matching the other two
 * variants' own fixed-per-provider `role` claim) so a JWT's shape alone
 * discloses which of the three authentication paths minted it.
 */
export interface ApiKeySessionPayload extends JWTPayload {
  sub: string; // the API key's bound identifier
  role: "api-key";
  authProvider: "api-key";
  boundRole: "viewer" | "member" | "owner";
  keyId: string;
  sessionId?: string;
}

export type SessionPayload =
  | LocalAdminSessionPayload
  | GoTrueSessionPayload
  | OidcSessionPayload
  | ApiKeySessionPayload;

/**
 * A fresh, real random session identifier -- Web Crypto's own
 * `randomUUID()` (a real RFC 4122 v4 UUID, 122 real random bits), available
 * as a global in both the Node.js runtime and the edge runtime this module
 * is written to stay compatible with, so this file still needs no
 * Node-only `node:crypto` import. Callers (the login/signup routes, and
 * middleware.ts's deterministic `apikey-<keyId>` construction for the
 * Bearer-token path) mint the id themselves and pass it in here, rather
 * than this module generating one internally and handing it back -- so the
 * exact same id is usable both as this JWT's `sessionId` claim and as the
 * lib/active-sessions.ts registry row's primary key, minted once, in one
 * place, by the caller that owns both writes.
 */
export function generateSessionId(): string {
  return globalThis.crypto.randomUUID();
}

function getSecretKey(): Uint8Array {
  const secret = process.env.AUTH_SECRET;
  if (!secret || secret.length < 16) {
    throw new Error(
      "AUTH_SECRET is not set (or too short). Set a real random secret " +
        "in the environment before starting the app.",
    );
  }
  return new TextEncoder().encode(secret);
}

/**
 * Unchanged from before this pass: same signature, same claims shape, same
 * caller (app/api/login/route.ts). The only difference is the new
 * `authProvider: "local-admin"` claim added alongside the existing
 * `role: "admin"` claim, so old and new sessions are both self-describing.
 */
export async function createSessionToken(username: string, sessionId: string): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({
    sub: username,
    role: "admin",
    authProvider: "local-admin",
    sessionId,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_TTL_SECONDS}s`)
    .sign(key);
}

/**
 * New: mints this app's own session for a real, already-authenticated
 * GoTrue user (called only after a real GoTrue /token?grant_type=password
 * or /signup success -- see lib/gotrue-auth.ts and
 * app/api/auth/gotrue-login/route.ts). `userId`/`email` come straight from
 * GoTrue's real response, never fabricated.
 */
export async function createGoTrueSessionToken(
  userId: string,
  email: string,
  sessionId: string,
): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({
    sub: userId,
    role: "authenticated",
    authProvider: "gotrue",
    email,
    sessionId,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_TTL_SECONDS}s`)
    .sign(key);
}

/**
 * Third session-issuing path: mints this app's own session for a real,
 * already-authenticated external-OIDC identity (called only after
 * lib/oidc-federation.ts's `verifyIdToken` has real-verified the external
 * provider's real ID-token signature -- see
 * app/api/auth/oidc-callback/route.ts). `userId`/`email`/`idpIssuer` come
 * straight from that verified token's own claims, never fabricated.
 */
export async function createOidcSessionToken(
  userId: string,
  email: string,
  idpIssuer: string,
  sessionId: string,
): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({
    sub: userId,
    role: "authenticated",
    authProvider: "oidc-external",
    email,
    idpIssuer,
    sessionId,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_TTL_SECONDS}s`)
    .sign(key);
}

const OIDC_TXN_TTL_SECONDS = 60 * 10; // 10 minutes -- a login round trip through a real external IdP should never take longer

export interface OidcTransactionPayload extends JWTPayload {
  state: string;
  nonce: string;
  codeVerifier: string;
  next: string;
}

/**
 * Short-lived, httpOnly, signed transaction cookie carrying the real PKCE
 * `code_verifier`, `state`, and `nonce` minted at `/api/auth/oidc-login`
 * time across the redirect to the external provider and back -- a Next.js
 * route handler has no server-side request-scoped memory to hold these in
 * between the two separate requests, so they travel in this signed cookie
 * instead (never trusted client input: the whole point of `state` is a
 * value the callback re-derives from what it itself set, not something an
 * attacker-controlled callback URL could forge, since this JWT is signed
 * with the same AUTH_SECRET every other session token is).
 */
export async function createOidcTransactionToken(payload: {
  state: string;
  nonce: string;
  codeVerifier: string;
  next: string;
}): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({ ...payload })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${OIDC_TXN_TTL_SECONDS}s`)
    .sign(key);
}

export async function verifyOidcTransactionToken(
  token: string,
): Promise<OidcTransactionPayload | null> {
  try {
    const key = getSecretKey();
    const { payload } = await jwtVerify(token, key, { algorithms: ["HS256"] });
    if (
      typeof payload.state !== "string" ||
      typeof payload.nonce !== "string" ||
      typeof payload.codeVerifier !== "string" ||
      typeof payload.next !== "string"
    ) {
      return null;
    }
    return payload as OidcTransactionPayload;
  } catch {
    return null;
  }
}

export const OIDC_TXN_COOKIE_NAME = "platform_console_oidc_txn";

/**
 * New: mints this app's own session for a real, already-resolved API key
 * (lib/api-keys.ts's resolveApiKeyAuth -- called only after a real
 * SHA-256 hash match against the live platform-console-api-keys Secret
 * already succeeded, and the matched record was confirmed not revoked).
 * `boundRole` and `keyId` come straight from that real record, never
 * fabricated.
 */
export async function createApiKeySessionToken(
  identifier: string,
  boundRole: "viewer" | "member" | "owner",
  keyId: string,
  sessionId: string,
): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({
    sub: identifier,
    role: "api-key",
    authProvider: "api-key",
    boundRole,
    keyId,
    sessionId,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_TTL_SECONDS}s`)
    .sign(key);
}

export async function verifySessionToken(
  token: string,
): Promise<SessionPayload | null> {
  try {
    const key = getSecretKey();
    const { payload } = await jwtVerify(token, key, {
      algorithms: ["HS256"],
    });
    if (typeof payload.sub !== "string") {
      return null;
    }
    // sessionId is optional on the wire (see the type's own doc comment --
    // backward compatibility with pre-existing cookies), but if present it
    // must be a real string, never some other JSON type smuggled in.
    if (payload.sessionId !== undefined && typeof payload.sessionId !== "string") {
      return null;
    }
    if (payload.authProvider === "gotrue") {
      if (payload.role !== "authenticated" || typeof payload.email !== "string") {
        return null;
      }
      return payload as GoTrueSessionPayload;
    }
    if (payload.authProvider === "oidc-external") {
      if (
        payload.role !== "authenticated" ||
        typeof payload.email !== "string" ||
        typeof payload.idpIssuer !== "string"
      ) {
        return null;
      }
      return payload as OidcSessionPayload;
    }
    if (payload.authProvider === "api-key") {
      if (
        payload.role !== "api-key" ||
        typeof payload.keyId !== "string" ||
        (payload.boundRole !== "viewer" &&
          payload.boundRole !== "member" &&
          payload.boundRole !== "owner")
      ) {
        return null;
      }
      return payload as ApiKeySessionPayload;
    }
    // Default/legacy branch: the original local-admin shape. Also accepts a
    // session minted before this pass (no authProvider claim yet) so
    // existing valid cookies aren't force-logged-out by this change.
    if (payload.role !== "admin") {
      return null;
    }
    return { ...payload, authProvider: "local-admin" } as LocalAdminSessionPayload;
  } catch {
    return null;
  }
}

export const SESSION_COOKIE_NAME = COOKIE_NAME;
export const SESSION_MAX_AGE = SESSION_TTL_SECONDS;
