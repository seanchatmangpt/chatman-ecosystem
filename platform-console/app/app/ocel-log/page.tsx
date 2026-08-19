import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import OcelLogPanel from "./OcelLogPanel";

export const dynamic = "force-dynamic";

// Viewer-and-up page, same visibility as /tracing -- process-mining output
// is operational telemetry, not an access record. Real hyperscaler
// equivalent: no major PaaS ships a native OCEL/process-mining surface;
// this is genuinely new ground for the platform, not a parity feature.
//
// Backed by the OCEL accumulator (Plan step C,
// `~/.claude/plans/eager-forging-sparrow.md`) that receives OTLP spans from
// the real otel-collector in istio-system, calls the unmodified
// `otel_span_to_ocel_evidence()` transformer per span, and appends to a
// persistent OCEL v2 log. app/api/ocel-log/route.ts proxies the
// accumulator's own status endpoint server-side -- nothing here is
// synthesized. Fail-closed: { ok: false } from the accumulator (including
// "step C isn't deployed yet") renders as an explicit error, never a
// fabricated count.
export default async function OcelLogPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const access = await requireRole(session, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">OCEL Event Log</h1>
        <p className="mb-8 max-w-3xl text-sm text-gray-400">
          Real object-centric event log (OCEL v2) accumulated from this mesh&apos;s own
          OTel spans -- every span exported to <code>otel-collector.istio-system</code>{" "}
          is transformed one-for-one via <code>otel_span_to_ocel_evidence()</code> and
          appended by a standing accumulator. The event count below and the discovery
          result beneath it are queried live, server-side, from that accumulator&apos;s
          own status endpoint -- nothing here is synthesized, and a sparse or trivial
          discovery result against real (non-benchmark) telemetry is expected, not a bug.
        </p>

        {!access.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{access.role}</code>) does not meet the required minimum role (
              <code>viewer</code>) for this page.
            </p>
          </div>
        )}

        {access.ok && <OcelLogPanel />}
      </main>
    </>
  );
}
