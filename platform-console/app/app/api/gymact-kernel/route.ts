import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  fetchKernelEvidence,
  fetchKernelHealth,
  fetchKernelProviders,
  probeKernelEpisode,
} from "@/lib/gymact-kernel";

// Proxies to the real gymact FastAPI kernel (gymact-kernel.gymact.svc.cluster.local,
// see lib/gymact-kernel.ts's header) -- distinct from GYMACT_STATUS_URL's static
// facts.json exporter. Read-only, any authenticated role (same boundary as
// /api/prometheus): this route only ever triggers a real `memory`-provider
// episode materialize + verify, never a consequential/DO-path capability
// invocation against a real external provider (kubernetes-reconciliation,
// terraform-plan, etc.) -- exercising those from an unauthenticated-by-role
// console GET would be the actual actuation path this route must not become.
//
// ?probe=1 additionally materializes+verifies one real memory-provider episode
// (see lib/gymact-kernel.ts's probeKernelEpisode) so the panel can show a live
// receipt, not just static /health and /providers facts.
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const wantsProbe = request.nextUrl.searchParams.get("probe") === "1";

  const [health, providers, evidence, probe] = await Promise.all([
    fetchKernelHealth(),
    fetchKernelProviders(),
    fetchKernelEvidence(),
    wantsProbe ? probeKernelEpisode() : Promise.resolve(null),
  ]);

  const status = health.ok && providers.ok && evidence.ok ? 200 : 502;
  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/gymact-kernel",
    status,
    requestId,
  });

  return NextResponse.json({ health, providers, evidence, probe }, { status });
}
