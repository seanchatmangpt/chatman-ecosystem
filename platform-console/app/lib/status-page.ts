/**
 * Real public status-page data: uptime% and current up/down state for every
 * platform component, computed with genuine PromQL over the real `up`
 * time series that services/platform-prober writes into the cluster's real
 * Prometheus (see that service's module docstring for why a purpose-built
 * exporter, not the 4 status services' own /status endpoints, is the data
 * source here -- two of these 8 components are third-party images with no
 * /metrics endpoint we can add, and one is Postgres, which isn't HTTP at
 * all).
 *
 * Every number this module returns comes from queryPrometheus (lib/
 * prometheus.ts) -- a real HTTP call to the real in-cluster Prometheus. No
 * value here is a literal/fallback percentage: if Prometheus is
 * unreachable, or a component has no samples in a window yet, this reports
 * that honestly (`reachable: false`, or `uptimePercent: null`) rather than
 * fabricating "100%" or "all systems operational".
 */
import { queryPrometheus, queryPrometheusRange } from "@/lib/prometheus";

export interface StatusComponent {
  id: string;
  label: string;
  namespace: string;
  /** null when Prometheus has no current sample for this component at all. */
  up: boolean | null;
  /** null when there are zero samples for this component in the window (not "0%" -- genuinely unknown). */
  uptimePercentWindow: number | null;
  uptimePercentDay: number | null;
  state: "operational" | "degraded" | "down" | "unknown";
}

export interface StatusPageData {
  generatedAt: string;
  windowLabel: string;
  windowSeconds: number;
  reachable: boolean;
  prometheusError: string | null;
  components: StatusComponent[];
  overall: "operational" | "degraded" | "down" | "unknown";
}

// Real component roster: the 4 status services, platform-console-gateway
// itself, and demo-project's postgres/auth/rest -- the same 8 targets
// services/platform-prober/app.py actually probes on every scrape. Kept in
// sync manually (both lists are short and change rarely); a component id
// here with no matching `up{component=...}` series in Prometheus renders as
// "unknown", not fabricated -- see toComponent() below.
const COMPONENT_ROSTER: Array<{ id: string; label: string; namespace: string }> = [
  { id: "autofde-lab-status", label: "autofde-lab status service", namespace: "autofde-lab" },
  { id: "gymact-status", label: "gymact status service", namespace: "gymact" },
  { id: "ggen-status", label: "ggen status service", namespace: "ggen" },
  {
    id: "ggen-marketplace-status",
    label: "ggen-marketplace status service",
    namespace: "ggen-marketplace",
  },
  {
    id: "platform-console-gateway",
    label: "Platform Console (this app)",
    namespace: "platform-console",
  },
  { id: "demo-project-postgres", label: "demo-project Postgres", namespace: "supabase-demo" },
  { id: "demo-project-auth", label: "demo-project Auth (GoTrue)", namespace: "supabase-demo" },
  { id: "demo-project-rest", label: "demo-project REST (PostgREST)", namespace: "supabase-demo" },
];

// Thresholds mirror the real hyperscaler-status-page convention: 100% (or
// no incident) is "operational", a real-but-small dip is "degraded", and a
// current outage is "down" regardless of the historical percentage.
const DEGRADED_BELOW_PERCENT = 99.9;

function extractByComponent(
  result: Awaited<ReturnType<typeof queryPrometheus>>,
): Map<string, number> {
  const out = new Map<string, number>();
  if (!result.ok) return out;
  for (const series of result.data.data?.result ?? []) {
    const component = series.metric.component;
    if (!component) continue;
    const value = Number(series.value[1]);
    if (Number.isFinite(value)) out.set(component, value);
  }
  return out;
}

function classify(up: boolean | null, uptimeWindow: number | null): StatusComponent["state"] {
  if (up === null) return "unknown";
  if (!up) return "down";
  if (uptimeWindow !== null && uptimeWindow < DEGRADED_BELOW_PERCENT) return "degraded";
  return "operational";
}

function overallOf(components: StatusComponent[]): StatusPageData["overall"] {
  if (components.every((c) => c.state === "unknown")) return "unknown";
  if (components.some((c) => c.state === "down")) return "down";
  if (components.some((c) => c.state === "degraded")) return "degraded";
  return "operational";
}

/**
 * Real query, one round trip per metric: current instant value of `up`,
 * plus avg_over_time(up[...]) over a short window (matches the platform
 * prober's own 15s scrape interval -- see k8s/status-page.yaml) and a
 * 24h window. Genuine PromQL executed against the real Prometheus every
 * call (`dynamic = "force-dynamic"` in the pages/routes that call this) --
 * nothing here is memoized or cached across requests.
 */
export async function getStatusPageData(
  windowSeconds = 3600,
): Promise<StatusPageData> {
  const windowLabel = windowSeconds >= 3600 ? `${Math.round(windowSeconds / 3600)}h` : `${Math.round(windowSeconds / 60)}m`;

  const [currentResult, windowResult, dayResult] = await Promise.all([
    queryPrometheus('up{component!=""}'),
    queryPrometheus(`avg_over_time(up{component!=""}[${windowLabel}]) * 100`),
    queryPrometheus('avg_over_time(up{component!=""}[24h]) * 100'),
  ]);

  const reachable = currentResult.ok && windowResult.ok && dayResult.ok;
  const prometheusError = !currentResult.ok
    ? currentResult.error
    : !windowResult.ok
      ? windowResult.error
      : !dayResult.ok
        ? dayResult.error
        : null;

  const current = extractByComponent(currentResult);
  const windowUptime = extractByComponent(windowResult);
  const dayUptime = extractByComponent(dayResult);

  const components: StatusComponent[] = COMPONENT_ROSTER.map((roster) => {
    const rawUp = current.get(roster.id);
    const up = rawUp === undefined ? null : rawUp === 1;
    const uptimePercentWindow = windowUptime.has(roster.id) ? windowUptime.get(roster.id)! : null;
    const uptimePercentDay = dayUptime.has(roster.id) ? dayUptime.get(roster.id)! : null;
    return {
      id: roster.id,
      label: roster.label,
      namespace: roster.namespace,
      up,
      uptimePercentWindow,
      uptimePercentDay,
      state: classify(up, uptimePercentWindow),
    };
  });

  return {
    generatedAt: new Date().toISOString(),
    windowLabel,
    windowSeconds,
    reachable,
    prometheusError,
    components,
    overall: overallOf(components),
  };
}

export interface ComponentDownWindow {
  componentId: string;
  /** RFC3339 -- the first sampled timestamp `up == 0` was observed for this contiguous span. */
  startedAt: string;
  /** RFC3339 -- the first sampled timestamp AFTER the span where `up` was seen back at 1
   * (i.e. the span is known to have ended by this time). Undefined when the span is still
   * open at `end` (the component was still down at the last sample in the queried range). */
  resolvedAt?: string;
}

export type ComponentDownWindowsResult =
  | { ok: true; data: ComponentDownWindow[] }
  | { ok: false; error: string };

/**
 * Real derivation of contiguous `up{component=...} == 0` spans between
 * `start` and `end`, one PromQL `query_range` round trip over the exact
 * same `up` series getStatusPageData reads instant/windowed values from --
 * the source-of-truth this repo's platform-prober exporter writes, never a
 * hand-entered value. Used by lib/incidents.ts's reconciler to auto-open/
 * close Incident rows from real observed downtime rather than manual entry.
 *
 * A span is "contiguous" at the query's own step resolution: consecutive
 * samples of `up == 0` for one component id are one span; a sample of
 * `up == 1` (or a gap -- no sample at all, e.g. scrape target briefly
 * unreachable at the Prometheus level itself) closes the current span.
 * `stepSeconds` defaults to platform-prober's own 15s scrape interval
 * (k8s/status-page.yaml) so no real down sample is missed between steps.
 */
export async function getComponentDownWindows(
  start: Date,
  end: Date,
  stepSeconds = 15,
): Promise<ComponentDownWindowsResult> {
  const result = await queryPrometheusRange(
    'up{component!=""}',
    Math.floor(start.getTime() / 1000),
    Math.floor(end.getTime() / 1000),
    stepSeconds,
  );
  if (!result.ok) return { ok: false, error: result.error };

  const windows: ComponentDownWindow[] = [];
  for (const series of result.data.data?.result ?? []) {
    const componentId = series.metric.component;
    if (!componentId) continue;
    let openStart: number | null = null;
    for (const [ts, rawValue] of series.values) {
      const isDown = Number(rawValue) === 0;
      if (isDown) {
        if (openStart === null) openStart = ts;
      } else if (openStart !== null) {
        windows.push({
          componentId,
          startedAt: new Date(openStart * 1000).toISOString(),
          resolvedAt: new Date(ts * 1000).toISOString(),
        });
        openStart = null;
      }
    }
    // Span still open at the end of the queried range -- report it without
    // a resolvedAt (the reconciler leaves the matching Incident row open).
    if (openStart !== null) {
      windows.push({
        componentId,
        startedAt: new Date(openStart * 1000).toISOString(),
      });
    }
  }
  return { ok: true, data: windows };
}
