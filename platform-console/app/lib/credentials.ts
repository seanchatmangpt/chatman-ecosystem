/**
 * Password verification against the seeded admin account. Uses bcryptjs,
 * which relies on Node.js APIs -- keep this import out of middleware.ts
 * (edge runtime); it is only ever called from the /api/login route handler,
 * which runs on the Node.js runtime by default.
 */
import bcrypt from "bcryptjs";

export interface CredentialCheckResult {
  ok: boolean;
  reason?: string;
}

export async function verifyAdminCredentials(
  username: string,
  password: string,
): Promise<CredentialCheckResult> {
  const expectedUsername = process.env.ADMIN_USERNAME ?? "admin";
  const passwordHash = process.env.ADMIN_PASSWORD_HASH;

  if (!passwordHash) {
    return {
      ok: false,
      reason: "ADMIN_PASSWORD_HASH is not configured on the server",
    };
  }
  if (username !== expectedUsername) {
    return { ok: false, reason: "invalid username or password" };
  }

  const matches = await bcrypt.compare(password, passwordHash);
  if (!matches) {
    return { ok: false, reason: "invalid username or password" };
  }
  return { ok: true };
}
