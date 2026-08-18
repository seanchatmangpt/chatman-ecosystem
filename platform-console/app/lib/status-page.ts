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
import { queryPrometheus } from "@/lib/prometheus";

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
