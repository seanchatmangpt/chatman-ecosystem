import { NextRequest, NextResponse } from "next/server";
import { verifyAdminCredentials } from "@/lib/credentials";
import {
  createSessionToken,
  generateSessionId,
  SESSION_COOKIE_NAME,
  SESSION_MAX_AGE,
} from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { recordSessionLogin } from "@/lib/active-sessions";
import { clientIpFrom } from "@/lib/request-meta";

// Runs on the Node.js runtime (the default for route handlers) because
// bcryptjs (via verifyAdminCredentials) needs Node crypto APIs that the
// edge runtime does not provide.
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  let username: string | undefined;
  let password: string | undefined;

  const contentType = request.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const body = await request.json().catch(() => ({}));
    username = body.username;
    password = body.password;
  } else {
    const form = await request.formData();
    username = String(form.get("username") ?? "");
    password = String(form.get("password") ?? "");
  }

  if (!username || !password) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "anonymous",
      method: "POST",
      path: "/api/login",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "username and password are required" },
      { status: 400 },
    );
  }

  const result = await verifyAdminCredentials(username, password);

  if (!result.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: username,
      method: "POST",
      path: "/api/login",
      status: 401,
      requestId,
    });
    return NextResponse.json({ error: "invalid credentials" }, { status: 401 });
  }

  const sessionId = generateSessionId();
  const token = await createSessionToken(username, sessionId);

  // Real Active Session Management registry entry (lib/active-sessions.ts).
  // Awaited (unlike the audit-db stdout+DB dual write) so the row is
  // guaranteed to already exist for a client that immediately follows this
  // 200 with a GET /api/sessions -- recordSessionLogin itself never
  // throws (every failure comes back as `{ok:false}`), and a registry
  // failure here is logged but never turned into a failed login: the
  // session cookie below is still issued either way.
  const registryResult = await recordSessionLogin({
    sessionId,
    identifier: username,
    authProvider: "local-admin",
    ip: clientIpFrom(request),
    userAgent: request.headers.get("user-agent"),
  });
  if (!registryResult.ok) {
    console.error(JSON.stringify({ activeSessionRecordError: registryResult.error }));
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: username,
    method: "POST",
    path: "/api/login",
    status: 200,
    requestId,
  });

  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });
  return response;
}
