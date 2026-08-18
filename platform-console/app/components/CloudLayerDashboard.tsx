import Link from "next/link";

export type DashboardStanding = "ALIVE" | "PARTIAL_ALIVE" | "UNKNOWN" | "BLOCKED";

export interface DashboardMetric {
  label: string;
  value: string;
  detail: string;
  tone?: "good" | "warn" | "neutral";
}

export interface DashboardResource {
  kind: string;
  name: string;
  namespace?: string;
  state: string;
  detail: string;
  href?: string;
}

export interface DashboardCapability {
  name: string;
  href: string;
  state: string;
  description: string;
  evidence: string;
}

export interface DashboardModel {
  layer: "IaaS" | "PaaS" | "SaaS";
  title: string;
  subtitle: string;
  scope: string;
  standing: DashboardStanding;
  capturedAt: string;
  metrics: DashboardMetric[];
  resources: DashboardResource[];
  capabilities: DashboardCapability[];
  flow: string[];
  errors: string[];
}

function standingClass(standing: DashboardStanding): string {
  switch (standing) {
    case "ALIVE":
      return "border-emerald-800 bg-emerald-950/40 text-emerald-300";
    case "PARTIAL_ALIVE":
      return "border-amber-800 bg-amber-950/40 text-amber-300";
    case "BLOCKED":
      return "border-red-900 bg-red-950/40 text-red-300";
    default:
      return "border-border bg-bg text-gray-300";
  }
}

function metricClass(tone: DashboardMetric["tone"]): string {
  if (tone === "good") return "text-emerald-300";
  if (tone === "warn") return "text-amber-300";
  return "text-white";
}

function stateClass(state: string): string {
  const normalized = state.toUpperCase();
  if (["READY", "RUNNING", "COMPLETE", "LIVE", "ALIVE"].includes(normalized)) {
    return "text-emerald-300";
  }
  if (["FAILED", "BLOCKED", "UNHEALTHY"].includes(normalized)) {
    return "text-red-300";
  }
  if (["PENDING", "DEGRADED", "PARTIAL_ALIVE"].includes(normalized)) {
    return "text-amber-300";
  }
  return "text-gray-300";
}

export default function CloudLayerDashboard({ model }: { model: DashboardModel }) {
  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <section className="mb-8 overflow-hidden rounded-2xl border border-border bg-panel">
        <div className="border-b border-border bg-gradient-to-r from-blue-950/60 via-panel to-panel px-6 py-7">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-blue-800 bg-blue-950/50 px-3 py-1 text-xs font-semibold tracking-[0.2em] text-blue-300">
              {model.layer}
            </span>
            <span className={`rounded-full border px-3 py-1 text-xs font-medium ${standingClass(model.standing)}`}>
              VIEW STANDING: {model.standing}
            </span>
            <span className="text-xs text-gray-500">captured {model.capturedAt}</span>
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-white">{model.title}</h1>
          <p className="mt-3 max-w-4xl text-sm leading-6 text-gray-300">{model.subtitle}</p>
          <p className="mt-3 text-xs text-gray-500">
            Observation boundary: <code>{model.scope}</code>. Standing applies to this dashboard&apos;s observation surface only; it does not crown unrelated ecosystem claims.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-px bg-border sm:grid-cols-2 xl:grid-cols-4">
          {model.metrics.map((metric) => (
            <div key={metric.label} className="bg-panel px-5 py-5">
              <div className="text-xs font-medium uppercase tracking-[0.12em] text-gray-500">{metric.label}</div>
              <div className={`mt-2 text-2xl font-semibold ${metricClass(metric.tone)}`}>{metric.value}</div>
              <div className="mt-1 text-xs leading-5 text-gray-500">{metric.detail}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_1fr]">
        <div className="card p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-white">Control-plane geometry</h2>
              <p className="mt-1 text-xs text-gray-500">Observable transitions, not decorative architecture.</p>
            </div>
            <span className="rounded-md border border-border bg-bg px-2.5 py-1 font-mono text-[11px] text-gray-400">
              SELECT → CONSTRUCT → DO → RECEIPT
            </span>
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-3 xl:grid-cols-6">
            {model.flow.map((step, index) => (
              <div key={`${step}-${index}`} className="relative rounded-lg border border-border bg-bg px-3 py-4 text-center">
                <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-blue-400">{String(index + 1).padStart(2, "0")}</div>
                <div className="mt-2 text-xs font-medium text-gray-200">{step}</div>
                {index < model.flow.length - 1 && (
                  <span className="absolute -right-2 top-1/2 hidden -translate-y-1/2 text-gray-600 xl:block">→</span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-base font-semibold text-white">Evidence boundary</h2>
          <p className="mt-1 text-xs leading-5 text-gray-500">
            Failed or unreachable observations are surfaced as typed uncertainty. No synthetic fallback data is inserted.
          </p>
          {model.errors.length === 0 ? (
            <div className="mt-5 rounded-lg border border-emerald-900 bg-emerald-950/30 px-4 py-4 text-sm text-emerald-300">
              All required observations for this view resolved from live control-plane sources.
            </div>
          ) : (
            <div className="mt-5 space-y-2">
              {model.errors.map((error) => (
                <div key={error} className="rounded-lg border border-amber-900 bg-amber-950/25 px-3 py-2 text-xs leading-5 text-amber-200">
                  {error}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="mb-8">
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-white">Capability surface</h2>
            <p className="mt-1 text-xs text-gray-500">Existing platform primitives composed into this layer.</p>
          </div>
          <span className="text-xs text-gray-500">{model.capabilities.length} capabilities</span>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {model.capabilities.map((capability) => (
            <Link key={`${capability.name}-${capability.href}`} href={capability.href} className="card group block p-5 transition hover:border-accent">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-white group-hover:text-blue-300">{capability.name}</h3>
                  <p className="mt-2 text-xs leading-5 text-gray-400">{capability.description}</p>
                </div>
                <span className={`text-[11px] font-semibold ${stateClass(capability.state)}`}>{capability.state}</span>
              </div>
              <div className="mt-4 border-t border-border pt-3 font-mono text-[10px] leading-4 text-gray-600">{capability.evidence}</div>
            </Link>
          ))}
        </div>
      </section>

      <section className="card overflow-hidden">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border px-6 py-5">
          <div>
            <h2 className="text-base font-semibold text-white">Observed resource inventory</h2>
            <p className="mt-1 text-xs text-gray-500">Directly derived from the live APIs used by this view.</p>
          </div>
          <span className="text-xs text-gray-500">{model.resources.length} resources</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border bg-bg/60 text-xs text-gray-500">
                <th className="px-6 py-3 font-normal">kind</th>
                <th className="px-6 py-3 font-normal">name</th>
                <th className="px-6 py-3 font-normal">namespace</th>
                <th className="px-6 py-3 font-normal">state</th>
                <th className="px-6 py-3 font-normal">evidence</th>
              </tr>
            </thead>
            <tbody>
              {model.resources.map((resource, index) => (
                <tr key={`${resource.kind}-${resource.namespace ?? "global"}-${resource.name}-${index}`} className="border-b border-border/60 last:border-b-0">
                  <td className="px-6 py-3 font-mono text-xs text-blue-300">{resource.kind}</td>
                  <td className="px-6 py-3 text-gray-100">
                    {resource.href ? (
                      <Link href={resource.href} className="hover:text-blue-300 hover:underline">{resource.name}</Link>
                    ) : (
                      resource.name
                    )}
                  </td>
                  <td className="px-6 py-3 font-mono text-xs text-gray-500">{resource.namespace ?? "—"}</td>
                  <td className={`px-6 py-3 text-xs font-semibold ${stateClass(resource.state)}`}>{resource.state}</td>
                  <td className="max-w-xl px-6 py-3 text-xs leading-5 text-gray-400">{resource.detail}</td>
                </tr>
              ))}
              {model.resources.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">No resources could be observed for this layer.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
