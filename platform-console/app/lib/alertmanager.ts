/**
 * Server-side proxy to the real in-cluster Alertmanager deployed by the
 * monitoring stack (monitoring-kube-prometheus-alertmanager.monitoring
 * .svc.cluster.local:9093). Same fail-closed convention as lib/prometheus.ts
 * and lib/status.ts: on any error this returns { ok: false }, never a
 * fabricated alert list.
 */

export type AlertmanagerResult =
  | { ok: true; data: AlertmanagerAlert[] }
  | { ok: false; error: string };

// Subset of the Alertmanager v2 API's gettableAlert schema
// (https://github.com/prometheus/alertmanager/blob/main/api/v2/openapi.yaml)
// -- only the fields the console actually renders.
export interface AlertmanagerAlert {
  labels: Record<string, string>;
  annotations: Record<string, string>;
  startsAt: string;
  endsAt: string;
  updatedAt: string;
  fingerprint: string;
  status: {
    state: "unprocessed" | "active" | "suppressed";
    silencedBy: string[];
    inhibitedBy: string[];
  };
  receivers: Array<{ name: string }>;
}

const FETCH_TIMEOUT_MS = 5000;

export async function queryAlerts(): Promise<AlertmanagerResult> {
  const base =
    process.env.ALERTMANAGER_URL ??
    "http://monitoring-kube-prometheus-alertmanager.monitoring.svc.cluster.local:9093";
  const url = `${base}/api/v2/alerts`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = (await res.json().catch(() => null)) as AlertmanagerAlert[] | null;
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

/** Derive the same firing/pending/resolved vocabulary CloudWatch/GCP
 * Alerting/Azure Monitor use from Alertmanager's real status.state +
 * endsAt, so the console's table reads the same way those consoles do. */
export function alertState(alert: AlertmanagerAlert): "firing" | "suppressed" | "resolved" {
  if (new Date(alert.endsAt).getTime() <= Date.now() && alert.endsAt !== "0001-01-01T00:00:00Z") {
    return "resolved";
  }
  if (alert.status.state === "suppressed") {
    return "suppressed";
  }
  return "firing";
}
