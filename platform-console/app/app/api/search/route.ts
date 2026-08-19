import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getRoleFor } from "@/lib/authz";
import { searchPlatform } from "@/lib/global-search";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Session-gated, any authenticated role -- this is read-only aggregation
// of things the session already has read access to. Per-category RBAC is
// enforced inside lib/global-search.ts's searchPlatform (CATEGORY_MIN_ROLE),
// the same requireRole minimums each category's own page/route already
// applies -- this route never bypasses that, it just resolves the
// session's real role once (getRoleFor, lib/authz.ts) and lets
// searchPlatform filter categories by it.

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

  const query = (request.nextUrl.searchParams.get("q") ?? "").trim();

  // Below 2 characters, every category degenerates into "everything" --
  // return an empty result set rather than pay the fan-out cost for a
  // query too short to be a real lookup.
  if (query.length < 2) {
    return NextResponse.json({ results: [] });
  }

  const role = await getRoleFor(session);
  const results = await searchPlatform(query, role);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/search",
    status: 200,
    requestId,
  });

  return NextResponse.json({ results });
}
