import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { fetchOpenclawDomainSolverCatalog, fetchOpenclawToolCatalog } from "@/lib/openclaw";

// Real read against the autofde-lab-mcp sidecar (services/autofde-lab-mcp)
// -- the actual autofde_lab domain/solver registry, not the static
// facts.json snapshot lib/status.ts's fetchAutofdeLabStatus() serves.
// requireSession only (viewer-readable), matching CATEGORY_MIN_ROLE's
// "viewer" for the service/project categories in lib/global-search.ts --
// this is discovery-only (tools/list + catalog kind=all), never
// tools/call of `run`.

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

  const [tools, catalog] = await Promise.all([
    fetchOpenclawToolCatalog(),
    fetchOpenclawDomainSolverCatalog("all"),
  ]);

  const status = tools.ok && catalog.ok ? 200 : 502;
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/openclaw-catalog",
    status,
    requestId,
  });

  if (!tools.ok) {
    return NextResponse.json({ error: tools.error }, { status: 502 });
  }
  if (!catalog.ok) {
    return NextResponse.json({ error: catalog.error }, { status: 502 });
  }

  return NextResponse.json({
    tools: tools.data.tools,
    domains: catalog.data.domains ?? [],
    solvers: catalog.data.solvers ?? [],
  });
}
