import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { listJaegerServices, listRecentTraces, type TraceSummary } from "@/lib/tracing";

export const dynamic = "force-dynamic";

// Viewer-and-up page (matches /observability's read visibility, not /audit's
// owner-only boundary -- traces are operational telemetry, not an access
// record). Real hyperscaler equivalent: AWS X-Ray console / GCP Cloud Trace
// / Azure Application Insights "end-to-end transaction details" view.
//
// Backed by a real Jaeger all-in-one instance this cluster now runs
// (k8s/jaeger-tracing.yaml, istio-system namespace) that satisfies an
// extensionProvider named "jaeger" the mesh's own ConfigMap already
// declared (OpenTelemetry, port 4317, service
// jaeger-collector.istio-system.svc.cluster.local) before anything backed
// it. A mesh-wide Telemetry resource (100% sampling) makes every Envoy
// proxy in the mesh -- including istio-ingressgateway, which fronts this
// very console -- export real spans to it. lib/tracing.ts proxies Jaeger's
// own query API server-side; nothing here is synthesized.
export default async function TracingPage() {
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Distributed Tracing</h1>
        <p className="mb-8 max-w-3xl text-sm text-gray-400">
          Real hyperscaler AWS X-Ray / GCP Cloud Trace / Azure Application Insights
          equivalent: end-to-end request traces captured by this mesh&apos;s own Envoy
          sidecars (Istio <code>Telemetry</code> resource, <code>k8s/jaeger-tracing.yaml</code>
          ) and exported live to a real Jaeger instance in <code>istio-system</code>. Every row
          below is a real trace, queried server-side from Jaeger&apos;s own query API (
          <code>jaeger-query.istio-system.svc.cluster.local:16686</code>) -- nothing here is
          synthesized. Viewer-and-up read access, enforced server-side by{" "}
          <code>lib/authz.ts</code>&apos;s <code>requireRole</code>, same mechanism as{" "}
          <code>/audit</code>.
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

        {access.ok && <TracingPanelServerBoundary />}
      </main>
    </>
  );
}

async function TracingPanelServerBoundary() {
  const servicesResult = await listJaegerServices();

  if (!servicesResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {servicesResult.error}
      </p>
    );
  }

  const services = servicesResult.data;

  if (services.length === 0) {
    return (
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        Jaeger is reachable but has recorded no services yet. Traces appear here within
        seconds of any request through <code>istio-ingressgateway</code> (mesh-wide 100%
        sampling) -- generate one and reload.
      </div>
    );
  }

  const perService = await Promise.all(
    services.map(async (service) => ({ service, result: await listRecentTraces(service, 20) })),
  );

  return (
    <div className="space-y-6">
      {perService.map(({ service, result }) => (
        <div key={service} className="card p-6">
          <h2 className="mb-4 text-base font-medium text-white">
            <code>{service}</code>
          </h2>

          {!result.ok && (
            <div className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
              {result.error}
            </div>
          )}

          {result.ok && result.data.length === 0 && (
            <p className="text-sm text-gray-500">no traces in the last hour</p>
          )}

          {result.ok && result.data.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-gray-400">
                    <th className="py-2 pr-4 font-normal">trace ID</th>
                    <th className="py-2 pr-4 font-normal">operation</th>
                    <th className="py-2 pr-4 font-normal">start time</th>
                    <th className="py-2 pr-4 font-normal">duration</th>
                    <th className="py-2 pr-4 font-normal">spans</th>
                    <th className="py-2 font-normal">status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.map((trace: TraceSummary) => (
                    <tr key={trace.traceId} className="border-b border-border/50">
                      <td className="py-2 pr-4 font-mono text-xs text-gray-300">
                        {trace.traceId.slice(0, 16)}
                      </td>
                      <td className="py-2 pr-4 break-all text-gray-100">
                        {trace.rootOperation}
                      </td>
                      <td className="py-2 pr-4 text-gray-100">
                        {new Date(trace.startTime).toLocaleString()}
                      </td>
                      <td className="py-2 pr-4 text-gray-100">{trace.durationMs} ms</td>
                      <td className="py-2 pr-4 text-gray-100">{trace.spanCount}</td>
                      <td className="py-2">
                        {trace.hasError ? (
                          <span className="rounded border border-red-900 bg-red-950/40 px-2 py-0.5 text-xs text-red-300">
                            error
                          </span>
                        ) : (
                          <span className="rounded border border-green-900 bg-green-950/40 px-2 py-0.5 text-xs text-green-300">
                            ok
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
