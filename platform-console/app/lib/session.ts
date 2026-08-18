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
 *
 * Both paths mint the exact same kind of app-local HS256 JWT, signed with
 * this app's own AUTH_SECRET -- this app's session cookie is never a GoTrue
 * access token passed through, so every existing session consumer
 * (middleware.ts, the various /api/* route handlers' requireActor helpers)
 * keeps working unchanged: they all only ever read `session.sub`.
 */
import { SignJWT, jwtVerify, type JWTPayload } from "jose";

const COOKIE_NAME = "platform_console_session";
const SESSION_TTL_SECONDS = 60 * 60 * 8; // 8 hours

export interface LocalAdminSessionPayload extends JWTPayload {
  sub: string; // username
  role: "admin";
  authProvider: "local-admin";
}

export interface GoTrueSessionPayload extends JWTPayload {
  sub: string; // real GoTrue user id (uuid)
  role: "authenticated";
  authProvider: "gotrue";
  email: string;
}

export type SessionPayload = LocalAdminSessionPayload | GoTrueSessionPayload;

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
export async function createSessionToken(username: string): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({
    sub: username,
    role: "admin",
    authProvider: "local-admin",
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
): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({
    sub: userId,
    role: "authenticated",
    authProvider: "gotrue",
    email,
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
    if (payload.authProvider === "gotrue") {
      if (payload.role !== "authenticated" || typeof payload.email !== "string") {
        return null;
      }
      return payload as GoTrueSessionPayload;
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
