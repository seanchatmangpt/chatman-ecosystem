/**
 * Server-side proxy to the real Jaeger query API this cluster now runs
 * (k8s/jaeger-tracing.yaml: jaeger-query.istio-system.svc.cluster.local:16686),
 * the distributed-tracing control every hyperscaler PaaS ships (AWS X-Ray,
 * GCP Cloud Trace, Azure Application Insights) that this platform previously
 * had no equivalent for. Same fail-closed convention as lib/prometheus.ts:
 * on any error this returns { ok: false }, never a fabricated trace.
 *
 * Istio's mesh config already declared an unused "jaeger" extensionProvider
 * (OpenTelemetry, port 4317, service jaeger-collector.istio-system) before
 * this file existed -- nothing in the cluster satisfied it. k8s/jaeger-tracing.yaml
 * deploys the Jaeger all-in-one pod that IS that service, and a mesh-wide
 * Telemetry resource (100% sampling) routes every proxy's spans to it.
 */

export type TracingResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

export interface JaegerSpan {
  traceID: string;
  spanID: string;
  operationName: string;
  startTime: number; // microseconds since epoch
  duration: number; // microseconds
  tags: Array<{ key: string; type: string; value: unknown }>;
  process?: { serviceName: string };
}

export interface JaegerTrace {
  traceID: string;
  spans: JaegerSpan[];
  processes: Record<string, { serviceName: string; tags?: unknown[] }>;
}

interface JaegerTracesResponse {
  data: JaegerTrace[] | null;
  total: number;
  limit: number;
  offset: number;
  errors: Array<{ code: number; msg: string }> | null;
}

interface JaegerServicesResponse {
  data: string[] | null;
  errors: Array<{ code: number; msg: string }> | null;
}

/** A trace flattened to what the console table needs to render one row per trace. */
export interface TraceSummary {
  traceId: string;
  rootService: string;
  rootOperation: string;
  startTime: string; // ISO
  durationMs: number;
  spanCount: number;
  hasError: boolean;
}

const FETCH_TIMEOUT_MS = 5000;

function baseUrl(): string {
  return (
    process.env.JAEGER_QUERY_URL ??
    "http://jaeger-query.istio-system.svc.cluster.local:16686"
  );
}

async function jaegerFetch<T>(path: string): Promise<TracingResult<T>> {
  const url = `${baseUrl()}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = (await res.json().catch(() => null)) as T | null;
    if (!res.ok || !body) {
      return { ok: false, error: `HTTP ${res.status} from ${url}` };
    }
    return { ok: true, data: body };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

export async function listJaegerServices(): Promise<TracingResult<string[]>> {
  const result = await jaegerFetch<JaegerServicesResponse>("/api/services");
  if (!result.ok) return result;
  if (result.data.errors && result.data.errors.length > 0) {
    return { ok: false, error: result.data.errors.map((e) => e.msg).join("; ") };
  }
  return { ok: true, data: result.data.data ?? [] };
}

/**
 * Recent traces for one service, newest first, summarized to exactly what
 * /tracing's table renders. `service` must come from listJaegerServices()'s
 * own result, never client-supplied free text -- same allowlist-by-construction
 * pattern lib/prometheus.ts uses for PromQL.
 */
export async function listRecentTraces(
  service: string,
  limit = 20,
): Promise<TracingResult<TraceSummary[]>> {
  const params = new URLSearchParams({
    service,
    limit: String(limit),
    lookback: "1h",
  });
  const result = await jaegerFetch<JaegerTracesResponse>(`/api/traces?${params}`);
  if (!result.ok) return result;
  if (result.data.errors && result.data.errors.length > 0) {
    return { ok: false, error: result.data.errors.map((e) => e.msg).join("; ") };
  }

  const traces = result.data.data ?? [];
  const summaries: TraceSummary[] = traces.map((trace) => {
    const spans = trace.spans ?? [];
    const rootSpan =
      spans.find((s) => !spans.some((other) => other.spanID !== s.spanID)) ?? spans[0];
    const earliestStart = spans.length
      ? Math.min(...spans.map((s) => s.startTime))
      : 0;
    const latestEnd = spans.length
      ? Math.max(...spans.map((s) => s.startTime + s.duration))
      : 0;
    const hasError = spans.some((s) =>
      s.tags.some(
        (t) => (t.key === "error" || t.key === "otel.status_code") &&
          (t.value === true || t.value === "ERROR" || t.value === "true"),
      ) ||
      s.tags.some((t) => t.key === "http.status_code" && Number(t.value) >= 400),
    );
    const rootServiceName =
      rootSpan?.process?.serviceName ??
      trace.processes?.[Object.keys(trace.processes ?? {})[0]]?.serviceName ??
      "unknown";

    return {
      traceId: trace.traceID,
      rootService: rootServiceName,
      rootOperation: rootSpan?.operationName ?? "-",
      startTime: new Date(earliestStart / 1000).toISOString(),
      durationMs: Math.round((latestEnd - earliestStart) / 1000),
      spanCount: spans.length,
      hasError,
    };
  });

  summaries.sort((a, b) => (a.startTime < b.startTime ? 1 : -1));
  return { ok: true, data: summaries };
}
