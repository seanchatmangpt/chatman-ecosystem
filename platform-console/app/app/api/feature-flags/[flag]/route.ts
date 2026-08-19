import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { createOrUpdateConfigMap, getConfigMap, getProject } from "@/lib/k8s";
import { requireRole } from "@/lib/authz";
import {
  isFlagEntitled,
  TIER_GATED_FLAGS,
  TIER_GATED_FLAG_OWNER_PROJECT,
  type ProjectTier,
} from "@/lib/tiers";

// Real customer-facing, self-service counterpart to POST /api/feature-flags
// (that route remains the internal/back-office toggle): this route is the
// concrete "an org admin clicks a locked flag and sees 'Upgrade to Pro to
// enable'" upsell surface named in the capability's rationale. Same
// runtime/auth posture as /api/feature-flags/route.ts -- Node.js runtime
// (lib/k8s.ts reads the ServiceAccount token/CA from disk, which the edge
// runtime cannot do), session-cookie auth, "member" as the minimum app-role
// to flip a flag.

const FLAGS_NAMESPACE = "platform-console";
const FLAGS_CONFIGMAP = "platform-feature-flags";

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ flag: string }> },
) {
  const { flag } = await params;
  const requestId = newRequestId();
  const path = `/api/feature-flags/${flag}`;

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Real app-level RBAC boundary, same minimum role POST /api/feature-flags
  // already requires -- self-service toggling is at least as sensitive as
  // the internal one, never less.
  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const enabled = body?.enabled;
  if (typeof enabled !== "boolean") {
    return NextResponse.json({ error: "enabled (boolean) is required" }, { status: 400 });
  }
  const value = enabled ? "true" : "false";

  // Real, live tier read off the flag's owning Project CR (never a
  // cached or client-supplied tier value) -- same TIER_GATED_FLAG_OWNER_PROJECT
  // lookup POST /api/feature-flags already performs. A flag with no
  // registered owner project (or one this ConfigMap has no entry for)
  // defaults to "starter", matching isFlagEntitled's own "ungated flag ->
  // always entitled" default.
  const requiredTier: ProjectTier = TIER_GATED_FLAGS[flag] ?? "starter";
  const ownerProjectName = TIER_GATED_FLAG_OWNER_PROJECT[flag];
  const ownerResult = ownerProjectName ? await getProject(ownerProjectName) : { ok: true as const, data: null };
  if (!ownerResult.ok) {
    return NextResponse.json({ error: ownerResult.error }, { status: 502 });
  }
  const currentTier: ProjectTier = ownerResult.data?.tier ?? "starter";

  // Turning a gated flag OFF is always allowed regardless of tier -- same
  // "downgrade never blocked" posture POST /api/feature-flags already
  // uses (the tier gate only fires when the caller is turning a flag ON).
  const entitled = !enabled || isFlagEntitled(currentTier, flag);

  if (!entitled) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path,
      status: 403,
      requestId,
    });
    return NextResponse.json(
      {
        error: "upgrade_required",
        requiredTier,
        currentTier,
      },
      { status: 403 },
    );
  }

  const existing = await getConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP);
  if (!existing.ok) {
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }

  // Real RFC 7386 merge patch (lib/k8s.ts's createOrUpdateConfigMap) --
  // sending only the one changed key leaves every other flag already in
  // the ConfigMap untouched, same one-key-at-a-time convention
  // POST /api/feature-flags already establishes.
  const result = await createOrUpdateConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP, { [flag]: value });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  return NextResponse.json({
    flag,
    enabled,
    requiredTier,
    currentTier,
    flags: result.data.data,
  });
}
