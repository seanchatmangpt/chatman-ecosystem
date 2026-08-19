/**
 * Server-side proxy to the real in-cluster Prometheus instance deployed by
 * the monitoring stack (monitoring-kube-prometheus-prometheus.monitoring
 * .svc.cluster.local:9090). Same fail-closed convention as lib/status.ts:
 * on any error this returns { ok: false }, never a fabricated series.
 */

export type PrometheusResult =
  | { ok: true; data: PrometheusQueryResponse }
  | { ok: false; error: string };

export interface PrometheusQueryResponse {
  status: "success" | "error";
  data?: {
    resultType: string;
    result: Array<{
      metric: Record<string, string>;
      value: [number, string];
    }>;
  };
  error?: string;
}

const FETCH_TIMEOUT_MS = 5000;

/**
 * A fixed allowlist of PromQL queries, not an open passthrough -- this is
 * the single source of truth both app/api/prometheus/route.ts (the direct
 * /observability query) and lib/dashboards.ts (a saved promql widget's
 * query, validated at creation time) enforce against. Prometheus's query
 * language can be used for extraction/DoS-shaped abuse if fully open, and
 * a saved dashboard widget must never be a way to run a query the
 * /observability page itself would refuse -- "a dashboard widget is just
 * a saved lens onto data the viewer could already query directly" only
 * holds if both call sites share the exact same allowlist. Extend
 * deliberately, not by accepting arbitrary client-supplied PromQL.
 */
export const ALLOWED_PROMETHEUS_QUERIES = new Set([
  "up",
  "kube_pod_status_ready",
  "container_memory_working_set_bytes",
]);

export type PrometheusRangeResult =
  | { ok: true; data: PrometheusRangeResponse }
  | { ok: false; error: string };

export interface PrometheusRangeResponse {
  status: "success" | "error";
  data?: {
    resultType: string;
    result: Array<{
      metric: Record<string, string>;
      values: Array<[number, string]>;
    }>;
  };
  error?: string;
}

/**
 * `/api/v1/query_range` counterpart to queryPrometheus above -- same fixed-
 * timeout, fail-closed convention, but returns a real time series of
 * `[timestamp, value]` samples over `[start, end]` at `stepSeconds`
 * resolution instead of one instant value. Used by lib/incidents.ts's
 * reconciler to find real contiguous `up == 0` spans per component (an
 * instant query can only ever say "is it down right now", never "when did
 * it go down and come back") -- no other call site needs range data today,
 * so this stays a thin, general primitive rather than baking in any
 * incident-specific logic.
 */
export async function queryPrometheusRange(
  query: string,
  startUnixSeconds: number,
  endUnixSeconds: number,
  stepSeconds: number,
): Promise<PrometheusRangeResult> {
  const base =
    process.env.PROMETHEUS_URL ??
    "http://monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090";
  const url = `${base}/api/v1/query_range?${new URLSearchParams({
    query,
    start: String(startUnixSeconds),
    end: String(endUnixSeconds),
    step: String(stepSeconds),
  })}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = (await res.json().catch(() => null)) as PrometheusRangeResponse | null;
    if (!res.ok || !body) {
      return { ok: false, error: `HTTP ${res.status} from ${url}` };
    }
    if (body.status !== "success") {
      return { ok: false, error: body.error ?? "prometheus returned status=error" };
    }
    return { ok: true, data: body };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

export async function queryPrometheus(query: string): Promise<PrometheusResult> {
  const base =
    process.env.PROMETHEUS_URL ??
    "http://monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090";
  const url = `${base}/api/v1/query?${new URLSearchParams({ query })}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = (await res.json().catch(() => null)) as PrometheusQueryResponse | null;
    if (!res.ok || !body) {
      return { ok: false, error: `HTTP ${res.status} from ${url}` };
    }
    if (body.status !== "success") {
      return { ok: false, error: body.error ?? "prometheus returned status=error" };
    }
    return { ok: true, data: body };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}
