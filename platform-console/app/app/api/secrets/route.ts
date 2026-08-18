import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import { createSecret, deleteSecret, listSecrets } from "@/lib/k8s";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Secret VALUES pass through this route's request body only on POST, and
// are forwarded straight into lib/k8s.ts's createSecret -- never logged.
// The audit-log entries below record method/path/status only, same as
// every other route in this file tree; no request body is ever logged.

async function requireActor(request: NextRequest): Promise<string | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  return session?.sub ?? null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  if (!namespace) {
    return NextResponse.json({ error: "namespace query param is required" }, { status: 400 });
  }

  const result = await listSecrets(namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/secrets",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ secrets: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const name = typeof body?.name === "string" ? body.name.trim() : "";
  const data = body?.data && typeof body.data === "object" ? (body.data as Record<string, unknown>) : {};

  const entries: Record<string, string> = {};
  for (const [key, value] of Object.entries(data)) {
    if (typeof key === "string" && key.trim() && typeof value === "string") {
      entries[key.trim()] = value;
    }
  }

  if (!namespace || !name || Object.keys(entries).length === 0) {
    return NextResponse.json(
      { error: "namespace, name, and at least one key/value pair are required" },
      { status: 400 },
    );
  }

  const result = await createSecret(namespace, name, entries);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/secrets",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ secret: result.data }, { status: 201 });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  const name = request.nextUrl.searchParams.get("name") ?? "";
  if (!namespace || !name) {
    return NextResponse.json(
      { error: "namespace and name query params are required" },
      { status: 400 },
    );
  }

  const result = await deleteSecret(namespace, name);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/secrets",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
