import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { getOcelAccumulatorStatus, getOcelDiscoveryResult } from "@/lib/ocel-log";

// Viewer-and-up, same read boundary as /api tracing consumers -- process-
// mining status is operational telemetry, not an access record.
// Server-side proxy to the OCEL accumulator's status endpoint (Plan step D,
// `~/.claude/plans/eager-forging-sparrow.md`), mirroring app/api/prometheus's
// and app/lib/tracing.ts's fail-closed convention exactly.
export const dynamic = "force-dynamic";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  if (!session) {
    return NextResponse.json({ ok: false, error: "unauthenticated" }, { status: 401 });
  }

  const access = await requireRole(session, "viewer");
  if (!access.ok) {
    return NextResponse.json({ ok: false, error: "forbidden" }, { status: 403 });
  }

  const [status, discovery] = await Promise.all([
    getOcelAccumulatorStatus(),
    getOcelDiscoveryResult(),
  ]);

  return NextResponse.json(
    { status, discovery },
    { headers: { "cache-control": "no-store" } },
  );
}
