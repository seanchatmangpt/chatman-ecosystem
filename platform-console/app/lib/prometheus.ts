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
