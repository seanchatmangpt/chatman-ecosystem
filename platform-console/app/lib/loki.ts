/**
 * Server-side proxy to the real Loki HTTP API this cluster now runs
 * (k8s/loki-log-aggregation.yaml: loki.monitoring.svc.cluster.local:3100),
 * the centralized cross-pod/cross-namespace log-search control every
 * hyperscaler PaaS ships (AWS CloudWatch Logs, GCP Cloud Logging, Azure Log
 * Analytics) that this platform previously had no equivalent for -- the
 * existing /logs page (lib/k8s.ts's getPodLogs/listPods) is a per-pod
 * `kubectl logs`-subresource tail only, with no cross-pod search. Same
 * fail-closed convention as lib/prometheus.ts and lib/tracing.ts: on any
 * error this returns { ok: false }, never a fabricated log line.
 *
 * A Promtail DaemonSet (same manifest) tails every container log file on
 * the node (/var/log/pods) and ships it into Loki, labeled with
 * namespace/pod/container/node -- nothing here is synthesized.
 */

export type LokiResult<T> = { ok: true; data: T } | { ok: false; error: string };

export interface LokiStreamResult {
  stream: Record<string, string>;
  values: Array<[string, string]>; // [unixNanoTimestamp, line]
}

interface LokiQueryResponse {
  status: "success" | "error";
  data?: {
    resultType: string;
    result: LokiStreamResult[];
  };
  error?: string;
}

/** One log line flattened to what the /log-search page's table renders. */
export interface LogEntry {
  timestamp: string; // ISO
  namespace: string;
  pod: string;
  container: string;
  line: string;
}

const FETCH_TIMEOUT_MS = 8000;

function baseUrl(): string {
  return process.env.LOKI_URL ?? "http://loki.monitoring.svc.cluster.local:3100";
}

async function lokiFetch(path: string): Promise<LokiResult<LokiQueryResponse>> {
  const url = `${baseUrl()}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = (await res.json().catch(() => null)) as LokiQueryResponse | null;
    if (!res.ok || !body) {
      return { ok: false, error: `HTTP ${res.status} from ${url}` };
    }
    if (body.status === "error") {
      return { ok: false, error: body.error ?? "unknown Loki error" };
    }
    return { ok: true, data: body };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Runs a real LogQL query against Loki's range-query endpoint, most-recent
 * lines first. `logql` is caller-constructed (see buildLogQL below) --
 * never raw client-supplied text passed straight through, same
 * defense-in-depth precedent as lib/prometheus.ts's PromQL allowlist,
 * except LogQL's label-matcher grammar is bounded here by construction
 * (buildLogQL only ever emits `{label="value", ...} |= "search text"`)
 * rather than a fixed query allowlist -- free-text search across the
 * platform's own logs is exactly what this page exists to do.
 */
export async function queryLoki(
  logql: string,
  limit = 200,
  sinceHours = 1,
): Promise<LokiResult<LogEntry[]>> {
  const oneMillionNs = BigInt(1_000_000);
  const endNs = BigInt(Date.now()) * oneMillionNs;
  const startNs = endNs - BigInt(sinceHours * 60 * 60 * 1000) * oneMillionNs;
  const params = new URLSearchParams({
    query: logql,
    limit: String(limit),
    start: startNs.toString(),
    end: endNs.toString(),
    direction: "backward",
  });

  const result = await lokiFetch(`/loki/api/v1/query_range?${params}`);
  if (!result.ok) return result;

  const streams = result.data.data?.result ?? [];
  const entries: LogEntry[] = [];
  for (const stream of streams) {
    for (const [tsNano, line] of stream.values) {
      entries.push({
        timestamp: new Date(Number(BigInt(tsNano) / oneMillionNs)).toISOString(),
        namespace: stream.stream.namespace ?? "-",
        pod: stream.stream.pod ?? "-",
        container: stream.stream.container ?? "-",
        line,
      });
    }
  }
  entries.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1));
  return { ok: true, data: entries.slice(0, limit) };
}

/**
 * Builds a real LogQL query from structured, individually-escaped inputs --
 * never string-concatenates caller text directly into the query. Every
 * label matcher and the free-text filter are double-quoted with internal
 * `"` and `\` backslash-escaped, matching LogQL's own string-literal
 * escaping rules, so a value like `foo" or 1=1` cannot break out of its
 * matcher.
 */
export function buildLogQL(params: {
  namespace?: string;
  pod?: string;
  container?: string;
  search?: string;
}): string {
  const escape = (s: string) => s.replace(/\\/g, "\\\\").replace(/"/g, '\\"');

  const matchers: string[] = [];
  if (params.namespace) matchers.push(`namespace="${escape(params.namespace)}"`);
  if (params.pod) matchers.push(`pod=~".*${escape(params.pod)}.*"`);
  if (params.container) matchers.push(`container="${escape(params.container)}"`);

  // A LogQL stream selector must never be empty -- fall back to matching
  // every stream this deployment ships (job="kubernetes-pods", set by
  // Promtail's own scrape_config in k8s/loki-log-aggregation.yaml) rather
  // than an unconstrained `{}` which Loki itself rejects.
  const selector = matchers.length > 0 ? matchers.join(", ") : `job="kubernetes-pods"`;

  let query = `{${selector}}`;
  if (params.search) {
    query += ` |= "${escape(params.search)}"`;
  }
  return query;
}

export async function listLokiNamespaces(): Promise<LokiResult<string[]>> {
  const result = await lokiFetchLabelValues("namespace");
  return result;
}

export async function listLokiPods(namespace?: string): Promise<LokiResult<string[]>> {
  if (!namespace) return lokiFetchLabelValues("pod");
  const params = new URLSearchParams({ query: `{namespace="${namespace}"}` });
  const result = await lokiFetch(`/loki/api/v1/series?${params}`);
  if (!result.ok) return result;
  const pods = new Set<string>();
  for (const stream of result.data.data?.result ?? []) {
    const p = (stream as unknown as { pod?: string }).pod;
    if (p) pods.add(p);
  }
  return { ok: true, data: Array.from(pods).sort() };
}

async function lokiFetchLabelValues(label: string): Promise<LokiResult<string[]>> {
  const url = `${baseUrl()}/loki/api/v1/label/${label}/values`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = (await res.json().catch(() => null)) as
      | { status: string; data?: string[] }
      | null;
    if (!res.ok || !body) {
      return { ok: false, error: `HTTP ${res.status} from ${url}` };
    }
    return { ok: true, data: (body.data ?? []).sort() };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}
