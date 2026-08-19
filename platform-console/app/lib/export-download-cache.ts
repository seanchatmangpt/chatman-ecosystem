import crypto from "node:crypto";

/**
 * Server-side, in-process cache + signed-token pair for the export-all
 * archive (POST /api/projects/[name]/export-all builds a real zip once,
 * this hands the caller back one signed download link for it -- the same
 * "possession of a valid, unexpired token IS the authorization" bearer
 * convention lib/storage-signed-url.ts already established for object
 * downloads). Different from that module in one real way: a signed
 * storage-object token is stateless (bucket+path both live durably in the
 * real Storage API, so the token alone is enough to re-fetch them later);
 * an export-all archive is a one-off multi-artifact bundle assembled at
 * request time with no natural persistent home, so the token here signs
 * an opaque id and the actual bytes are held in this module's own Map
 * until downloaded or expired. Same AUTH_SECRET-backed HMAC, same
 * clamped-TTL discipline, same constant-time verification.
 */

export const MIN_TTL_SECONDS = 30;
export const MAX_TTL_SECONDS = 60 * 60; // 1h ceiling -- long enough for a real download, short enough that an unclaimed archive doesn't sit in memory indefinitely
export const DEFAULT_TTL_SECONDS = 15 * 60;

interface CachedArchive {
  buffer: Buffer;
  filename: string;
  expiresAt: number;
}

const archives = new Map<string, CachedArchive>();

function getSecretKey(): Buffer {
  const secret = process.env.AUTH_SECRET;
  if (!secret || secret.length < 16) {
    throw new Error(
      "AUTH_SECRET is not set (or too short). Set a real random secret " +
        "in the environment before starting the app.",
    );
  }
  return Buffer.from(secret, "utf8");
}

function sign(payload: string): string {
  return crypto.createHmac("sha256", getSecretKey()).update(payload).digest("hex");
}

function evictExpired(): void {
  const now = Date.now();
  for (const [id, entry] of archives) {
    if (entry.expiresAt <= now) archives.delete(id);
  }
}

export interface SignedExportToken {
  token: string;
  expiresAt: string; // RFC3339
}

/**
 * Stores a real archive Buffer under a fresh random id and mints a signed
 * token for it, clamping the TTL the same way signStorageDownloadToken
 * does. Called exactly once per successful POST /export-all.
 */
export function storeExportArchive(
  buffer: Buffer,
  filename: string,
  identifier: string,
  requestedTtlSeconds: number,
): SignedExportToken {
  evictExpired();
  const ttl = Math.min(
    MAX_TTL_SECONDS,
    Math.max(MIN_TTL_SECONDS, Math.floor(requestedTtlSeconds) || DEFAULT_TTL_SECONDS),
  );
  const exp = Date.now() + ttl * 1000;
  const id = crypto.randomUUID();
  archives.set(id, { buffer, filename, expiresAt: exp });

  const payload = [id, String(exp), identifier].join("\n");
  const payloadB64 = Buffer.from(payload, "utf8").toString("base64url");
  const signature = sign(payloadB64);
  return { token: `${payloadB64}.${signature}`, expiresAt: new Date(exp).toISOString() };
}

export type VerifyExportTokenResult =
  | { ok: true; id: string; identifier: string; expiresAt: string }
  | { ok: false; reason: "malformed" | "bad-signature" | "expired" };

export function verifyExportToken(token: string): VerifyExportTokenResult {
  const dotIndex = token.lastIndexOf(".");
  if (dotIndex <= 0 || dotIndex === token.length - 1) {
    return { ok: false, reason: "malformed" };
  }
  const payloadB64 = token.slice(0, dotIndex);
  const presentedSignature = token.slice(dotIndex + 1);

  const expectedSignature = sign(payloadB64);
  const expectedBuf = Buffer.from(expectedSignature, "hex");
  const presentedBuf = Buffer.from(presentedSignature, "hex");
  if (
    expectedBuf.length !== presentedBuf.length ||
    !crypto.timingSafeEqual(expectedBuf, presentedBuf)
  ) {
    return { ok: false, reason: "bad-signature" };
  }

  let payload: string;
  try {
    payload = Buffer.from(payloadB64, "base64url").toString("utf8");
  } catch {
    return { ok: false, reason: "malformed" };
  }
  const parts = payload.split("\n");
  if (parts.length !== 3) {
    return { ok: false, reason: "malformed" };
  }
  const [id, expRaw, identifier] = parts;
  const exp = Number(expRaw);
  if (!id || !Number.isFinite(exp)) {
    return { ok: false, reason: "malformed" };
  }
  if (Date.now() > exp) {
    return { ok: false, reason: "expired" };
  }
  return { ok: true, id, identifier, expiresAt: new Date(exp).toISOString() };
}

/**
 * Reads back a real, previously-stored archive by id -- returns null if
 * it was never stored, already expired, or (this console runs as a
 * single Next.js process, no external session store) the process
 * restarted since it was minted. Does NOT evict on read: a signed link
 * may legitimately be reused (retried download, opened in two tabs)
 * until its own expiry, matching the storage-signed-url download route's
 * own re-fetchable-until-expiry contract.
 */
export function readExportArchive(id: string): { buffer: Buffer; filename: string } | null {
  evictExpired();
  const entry = archives.get(id);
  if (!entry) return null;
  return { buffer: entry.buffer, filename: entry.filename };
}
