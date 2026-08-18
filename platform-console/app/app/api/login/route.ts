import { NextRequest, NextResponse } from "next/server";
import { verifyAdminCredentials } from "@/lib/credentials";
import { createSessionToken, SESSION_COOKIE_NAME, SESSION_MAX_AGE } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

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

  const token = await createSessionToken(username);

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
