import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { createOrUpdateConfigMap, getConfigMap, getProject } from "@/lib/k8s";
import { requireRole } from "@/lib/authz";
import {
  isFlagEntitled,
  TIER_GATED_FLAGS,
  TIER_GATED_FLAG_OWNER_PROJECT,
  tierAtLeast,
  type ProjectTier,
} from "@/lib/tiers";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do. Same pattern as app/api/secrets/route.ts.

const FLAGS_NAMESPACE = "platform-console";
const FLAGS_CONFIGMAP = "platform-feature-flags";

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

  const result = await getConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/feature-flags",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  const rawFlags = result.data?.data ?? {};

  // Real per-flag entitlement metadata (isFlagEntitled, lib/tiers.ts):
  // the console UI's whole "render a locked padlock with an upgrade
  // prompt vs. a live toggle" decision, computed server-side so the UI
  // never has to make a second round trip (or reimplement the tier
  // comparison) just to know whether a flag is actually settable by
  // this org. Every distinct owner Project (TIER_GATED_FLAG_OWNER_PROJECT)
  // referenced by ANY gated flag is looked up at most once, not once per
  // flag -- same batching discipline as everywhere else in this route.
  const ownerProjectNames = Array.from(
    new Set(Object.values(TIER_GATED_FLAG_OWNER_PROJECT)),
  );
  const ownerTierByProject = new Map<string, ProjectTier>();
  for (const ownerProjectName of ownerProjectNames) {
    const ownerResult = await getProject(ownerProjectName);
    ownerTierByProject.set(
      ownerProjectName,
      ownerResult.ok ? ownerResult.data?.tier ?? "starter" : "starter",
    );
  }

  const flagKeys = new Set<string>([...Object.keys(rawFlags), ...Object.keys(TIER_GATED_FLAGS)]);
  const flags: Record<
    string,
    { enabled: boolean; requiredTier: ProjectTier; entitled: boolean }
  > = {};
  for (const key of flagKeys) {
    const requiredTier = TIER_GATED_FLAGS[key] ?? "starter";
    const ownerProjectName = TIER_GATED_FLAG_OWNER_PROJECT[key];
    const ownerTier = ownerProjectName ? ownerTierByProject.get(ownerProjectName) ?? "starter" : "starter";
    flags[key] = {
      enabled: rawFlags[key] === "true",
      requiredTier,
      entitled: isFlagEntitled(ownerTier, key),
    };
  }

  return NextResponse.json({ flags });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Real app-level RBAC boundary: toggling a feature flag needs at least
  // "member". See lib/authz.ts.
  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/feature-flags",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const key = typeof body?.key === "string" ? body.key.trim() : "";
  const value = typeof body?.value === "string" ? body.value : "";

  if (!key) {
    return NextResponse.json({ error: "key is required" }, { status: 400 });
  }

  // Real plan-tier gate (lib/tiers.ts): closes the "no feature-flagged
  // capability is Enterprise-only" half of the resource-quotas-enforced
  // gap. Only fires when this key is in TIER_GATED_FLAGS AND the caller is
  // turning it on ("true") -- turning a gated flag back OFF is always
  // allowed regardless of tier, same "downgrade never blocked" posture
  // lib/plan-state.ts's suspension logic uses. The gate reads the REAL,
  // live tier off the flag's owning Project CR (TIER_GATED_FLAG_OWNER_PROJECT)
  // via getProject -- never a cached or client-supplied tier value.
  const minimumTier = TIER_GATED_FLAGS[key];
  if (minimumTier && value === "true") {
    const ownerProjectName = TIER_GATED_FLAG_OWNER_PROJECT[key];
    const ownerResult = ownerProjectName ? await getProject(ownerProjectName) : { ok: true as const, data: null };
    if (!ownerResult.ok) {
      return NextResponse.json({ error: ownerResult.error }, { status: 502 });
    }
    const ownerTier = ownerResult.data?.tier ?? "starter";
    if (!tierAtLeast(ownerTier, minimumTier)) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/feature-flags",
        status: 403,
        requestId,
      });
      return NextResponse.json(
        {
          error:
            `flag '${key}' requires plan tier '${minimumTier}' or higher on Project ` +
            `'${ownerProjectName}' (currently '${ownerTier}')`,
        },
        { status: 403 },
      );
    }
  }

  // A real RFC 7386 merge patch (lib/k8s.ts's createOrUpdateConfigMap) --
  // sending only the one changed key leaves every other flag already in
  // the ConfigMap untouched.
  const result = await createOrUpdateConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP, { [key]: value });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/feature-flags",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ flags: result.data.data });
}
