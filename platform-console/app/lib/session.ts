/**
 * Hand-rolled session handling using `jose` (HS256 JWT), edge-runtime safe so
 * it can run inside middleware.ts without pulling in Node-only crypto APIs.
 *
 * There is exactly one seeded account (the admin), whose bcrypt password hash
 * comes from the ADMIN_PASSWORD_HASH env var -- never a plaintext secret in
 * source. See lib/credentials.ts for the password check (bcryptjs, which
 * needs the Node.js runtime, so that check happens only in the login route
 * handler, not in middleware).
 */
import { SignJWT, jwtVerify, type JWTPayload } from "jose";

const COOKIE_NAME = "platform_console_session";
const SESSION_TTL_SECONDS = 60 * 60 * 8; // 8 hours

export interface SessionPayload extends JWTPayload {
  sub: string; // username
  role: "admin";
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

export async function createSessionToken(username: string): Promise<string> {
  const key = getSecretKey();
  return await new SignJWT({ sub: username, role: "admin" })
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
    if (typeof payload.sub !== "string" || payload.role !== "admin") {
      return null;
    }
    return payload as SessionPayload;
  } catch {
    return null;
  }
}

export const SESSION_COOKIE_NAME = COOKIE_NAME;
export const SESSION_MAX_AGE = SESSION_TTL_SECONDS;
