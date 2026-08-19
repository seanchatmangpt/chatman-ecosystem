import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, ROLES, roleIdentifierFor, type Role } from "@/lib/authz";
import { createApiKey, listApiKeys, revokeApiKey } from "@/lib/api-keys";
import { isApiKeyTier } from "@/lib/rate-limit";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Owner-gated on every verb (requireRole(session, "owner")), same
// boundary as /org and /webhooks: an API key inherits real, bound
// authority over this console, so minting/listing/revoking one is at
// least as sensitive as changing a role assignment or registering a
// webhook subscriber URL. The plaintext key itself passes through this
// route's POST response body exactly once -- lib/api-keys.ts never
// stores it, and no other verb here (or anywhere else in this app) can
// ever retrieve it again, matching every real provider's (AWS/GCP/
// Stripe) own "shown once at creation" UX.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/api-keys",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listApiKeys();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/api-keys",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ keys: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/api-keys",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const requestedRole =
    typeof body?.role === "string" && ROLES.includes(body.role as Role)
      ? (body.role as Role)
      : undefined;
  const name = typeof body?.name === "string" ? body.name : "";
  // Plan tier this key is rate-limited under (lib/rate-limit.ts) --
  // unlike `requestedRole` this is never clamped against the creator's
  // own role; it reflects the customer's paid plan, an orthogonal axis
  // from app-level RBAC. Falls back to "standard" for an omitted or
  // invalid value -- same default lib/api-keys.ts's createApiKey applies.
  const requestedTier = isApiKeyTier(body?.tier) ? body.tier : undefined;

  // A key is always minted FOR the creating owner's own identity -- never
  // an arbitrary other identity (that would be identity spoofing, not a
  // feature any real hyperscaler IAM console offers) -- with a role that
  // can only be <= the creator's own real, live role (access.role, just
  // resolved above via a real ConfigMap read), never escalated even if
  // the request body asks for more.
  const creatorRole = access.role;
  const identifier = roleIdentifierFor(session);

  const result = await createApiKey({
    identifier,
    creatorRole,
    createdBy: identifier,
    requestedRole,
    name,
    tier: requestedTier,
  });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/api-keys",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  // The ONLY response, ever, that carries the plaintext key. Not logged
  // (writeAuditLogEntry above records method/path/status only, same fixed
  // schema every other route uses), not persisted anywhere by
  // lib/api-keys.ts (only the SHA-256 hash is written to the Secret).
  return NextResponse.json(
    { plaintext: result.data.plaintext, key: result.data.key },
    { status: 201 },
  );
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/api-keys",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const id = request.nextUrl.searchParams.get("id") ?? "";
  if (!id) {
    return NextResponse.json({ error: "id query param is required" }, { status: 400 });
  }

  const result = await revokeApiKey(id);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/api-keys",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ key: result.data });
}
