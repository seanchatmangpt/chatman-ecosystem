import { NextRequest, NextResponse } from "next/server";
import { signUpWithPassword } from "@/lib/gotrue-auth";
import {
  createGoTrueSessionToken,
  generateSessionId,
  SESSION_COOKIE_NAME,
  SESSION_MAX_AGE,
} from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { recordSessionLogin } from "@/lib/active-sessions";
import { clientIpFrom, isSecureRequest } from "@/lib/request-meta";

// Additive signup path: real account creation against the live GoTrue
// instance's /signup endpoint (see lib/gotrue-auth.ts). On success mints
// this app's own session, same as gotrue-login.
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  let email: string | undefined;
  let password: string | undefined;

  const contentType = request.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const body = await request.json().catch(() => ({}));
    email = body.email;
    password = body.password;
  } else {
    const form = await request.formData();
    email = String(form.get("email") ?? "");
    password = String(form.get("password") ?? "");
  }

  if (!email || !password) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "anonymous",
      method: "POST",
      path: "/api/auth/gotrue-signup",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "email and password are required" },
      { status: 400 },
    );
  }

  const result = await signUpWithPassword(email, password);

  if (!result.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: email,
      method: "POST",
      path: "/api/auth/gotrue-signup",
      status: result.status || 400,
      requestId,
    });
    return NextResponse.json(
      { error: result.message, errorCode: result.errorCode },
      { status: result.status || 400 },
    );
  }

  const sessionId = generateSessionId();
  const token = await createGoTrueSessionToken(result.user.id, result.user.email, sessionId);

  // Real Active Session Management registry entry -- see /api/login's own
  // identical comment for why this is awaited and never fails the signup.
  const registryResult = await recordSessionLogin({
    sessionId,
    identifier: result.user.email,
    authProvider: "gotrue",
    ip: clientIpFrom(request),
    userAgent: request.headers.get("user-agent"),
  });
  if (!registryResult.ok) {
    console.error(JSON.stringify({ activeSessionRecordError: registryResult.error }));
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: result.user.email,
    method: "POST",
    path: "/api/auth/gotrue-signup",
    status: 201,
    requestId,
  });

  const response = NextResponse.json(
    {
      ok: true,
      authProvider: "gotrue",
      user: { id: result.user.id, email: result.user.email },
    },
    { status: 201 },
  );
  response.cookies.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: isSecureRequest(request),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });
  return response;
}
