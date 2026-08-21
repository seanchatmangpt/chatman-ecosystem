import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { discoverOcDfgLocal, type OcelLog } from "@/lib/ocel-log";

// Deliberately separate from /api/ocel-log: this route does not touch the
// deployed `ocel-accumulator` Service at all. It runs a real, local
// wasm4pm-cli (`wpm`) subprocess against the OCEL log supplied in the
// request body and returns the real discovered OC-DFG. Left unlinked from
// the existing UI -- a second, independently-comparable discovery path,
// not a replacement for the accumulator proxy.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
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

  let log: OcelLog;
  try {
    log = (await request.json()) as OcelLog;
  } catch {
    return NextResponse.json({ ok: false, error: "invalid JSON body" }, { status: 400 });
  }

  if (!log || !Array.isArray(log.events) || !Array.isArray(log.objects)) {
    return NextResponse.json(
      { ok: false, error: "body must be an OcelLog with events[] and objects[]" },
      { status: 400 },
    );
  }

  try {
    const ocdfg = discoverOcDfgLocal(log);
    return NextResponse.json(
      { ok: true, data: ocdfg },
      { headers: { "cache-control": "no-store" } },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: message }, { status: 502 });
  }
}
