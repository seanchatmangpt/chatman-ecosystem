import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { clientIpFrom } from "@/lib/request-meta";
import { getIpAllowlist, isValidCidr, setIpAllowlist } from "@/lib/ip-allowlist";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Real GET/PUT for one org's IP allowlist (lib/ip-allowlist.ts), keyed by
// the org's own real namespace (lib/orgs.ts's `Org.namespace` -- no
// schema change to orgs.ts needed, the allowlist ConfigMap is already
// keyed by namespace). `id` is first resolved against the real
// `platform-console-orgs` registry (getOrg); when it resolves, that org's
// own `namespace` is used. When it does NOT resolve, `id` is used
// directly as the namespace instead of 404ing -- this deployment's own
// single-tenant namespace ("platform-console", the exact
// IP_ALLOWLIST_NAMESPACE middleware.ts enforces against) has no
// corresponding registry row (lib/orgs.ts's own header comment: this app
// has no per-session org concept beyond that one namespace yet), so
// `/api/orgs/platform-console/ip-allowlist` is how this app's one actual
// enforced tenant manages its own allowlist today -- same
// "operate directly on the fixed namespace, no org abstraction required"
// convention lib/authz.ts's own org-roles ConfigMap already uses.
//
// PUT is owner-only (requireRole(session, "owner")) -- same discipline
// every other mutating, security-relevant route in this app uses
// (lib/authz.ts's own /api/org/roles, lib/quota-enforcement.ts's routes).
// GET is any authenticated session -- a member/viewer reading the
// currently-configured allowlist (and their own request IP, via the
// `yourIp` field) is not itself a privileged action, only changing it is.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const { id } = await params;

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : id;

  const result = await getIpAllowlist(namespace);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/ip-allowlist`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    namespace,
    cidrs: result.data,
    yourIp: clientIpFrom(request),
  });
}

export async function PUT(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const { id } = await params;

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : id;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/ip-allowlist`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const rawCidrs = body?.cidrs;
  if (!Array.isArray(rawCidrs) || !rawCidrs.every((v) => typeof v === "string")) {
    return NextResponse.json({ error: "cidrs must be an array of strings" }, { status: 400 });
  }
  const cidrs = rawCidrs.map((v: string) => v.trim()).filter((v: string) => v.length > 0);

  // Same "validate every entry is a real parseable CIDR before storing,
  // reject and 400 otherwise" discipline lib/custom-domains.ts uses for
  // its own SAN validation -- a malformed entry never reaches the
  // ConfigMap, so it can never silently fail to match at enforcement time
  // in middleware.ts.
  const invalid = cidrs.filter((v: string) => !isValidCidr(v));
  if (invalid.length > 0) {
    return NextResponse.json(
      { error: `invalid CIDR(s): ${invalid.join(", ")}` },
      { status: 400 },
    );
  }

  const result = await setIpAllowlist(namespace, cidrs);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/ip-allowlist`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    namespace,
    cidrs: result.data,
    yourIp: clientIpFrom(request),
  });
}
