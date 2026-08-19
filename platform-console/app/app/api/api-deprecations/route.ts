import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  activeApiDeprecations,
  appendApiDeprecation,
  listApiDeprecations,
  validateApiDeprecationInput,
  type ApiDeprecationMethod,
} from "@/lib/api-deprecations";

// Real customer-facing API deprecation-notice feed -- endpoint+method
// sunset schedule for THIS platform's own REST API (app/api/v1/*),
// distinct from lib/changelog.ts's tier-scoped product changelog (which
// covers UI/feature announcements, not API contract lifecycle). Standard
// enterprise-API-vendor surface this repo did not yet have (cf. Stripe's
// own API changelog/deprecation feed) -- see lib/api-deprecations.ts's
// own header comment for storage/shape details.
//
// Auth model:
//   - GET: deliberately no session check, same unauthenticated posture
//     as app/app/api/trust/route.ts and app/app/api/status/route.ts --
//     this backs external API clients and status-page widgets that have
//     no session of their own, listed in middleware.ts's PUBLIC_PATHS.
//     `?active=true` filters to notices whose sunsetDate is still in the
//     future and sorts by sunsetDate ascending.
//   - POST: platform-admin only (lib/authz.ts's requirePlatformAdmin --
//     same platform-level "owner" role app/api/admin/referrals/route.ts
//     already gates its POST on; this codebase has no separate "admin"
//     role, platform-owner is the top rank). Every write is audit-logged
//     the same as every other admin mutation in this tree.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const activeOnly = request.nextUrl.searchParams.get("active") === "true";

  const result = await listApiDeprecations();
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  const entries = activeOnly
    ? activeApiDeprecations(result.data)
    : [...result.data].sort((a, b) => a.sunsetDate.localeCompare(b.sunsetDate));

  return NextResponse.json(
    { entries },
    { headers: { "cache-control": "no-store" } },
  );
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    // org-agnostic: platform-level API-contract-lifecycle notice, no
    // per-tenant org boundary -- see scripts/check-audit-org-coverage.ts
    // allowlist (same convention as app/api/admin/referrals/route.ts).
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/api-deprecations",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const input = {
    endpointPattern: typeof body?.endpointPattern === "string" ? body.endpointPattern.trim() : "",
    method: typeof body?.method === "string" ? body.method.trim().toUpperCase() : "",
    announcedAt: typeof body?.announcedAt === "string" ? body.announcedAt.trim() : "",
    sunsetDate: typeof body?.sunsetDate === "string" ? body.sunsetDate.trim() : "",
    replacementEndpoint:
      typeof body?.replacementEndpoint === "string" && body.replacementEndpoint.trim().length > 0
        ? body.replacementEndpoint.trim()
        : null,
    migrationNote: typeof body?.migrationNote === "string" ? body.migrationNote.trim() : "",
    severity: typeof body?.severity === "string" ? body.severity.trim() : "",
  };

  const validationError = validateApiDeprecationInput(input);
  if (validationError) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/api-deprecations",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  // Shape already confirmed by validateApiDeprecationInput above.
  const result = await appendApiDeprecation({
    endpointPattern: input.endpointPattern,
    method: input.method as ApiDeprecationMethod,
    announcedAt: input.announcedAt,
    sunsetDate: input.sunsetDate,
    replacementEndpoint: input.replacementEndpoint,
    migrationNote: input.migrationNote,
    severity: input.severity as "info" | "breaking",
    createdBy: actor,
  });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/api-deprecations",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ entry: result.data }, { status: 201 });
}
