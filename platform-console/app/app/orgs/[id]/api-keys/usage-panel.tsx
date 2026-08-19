"use client";

import { useEffect, useState } from "react";

// Customer-facing API key usage analytics panel -- the dashboard half of
// GET /api/orgs/[id]/api-keys/[keyId]/usage. Deliberately a standalone
// component (not a page) so it drops straight into the existing API Keys
// management UI as a per-key expansion, the same "own the aggregation +
// one focused view" split app/orgs/[id]/export-subscription/page.tsx uses
// for its own org-scoped API-backed panel. No chart library dependency --
// a real inline SVG bar/line combo, same "no new dependency, real
// numbers" convention as every other data view in this app.

interface ApiKeyUsageBucket {
  hour: string;
  calls: number;
  status2xx: number;
  status4xx: number;
  status5xx: number;
}

interface ApiKeyUsageResult {
  keyId: string;
  orgId: string;
  window: "1h" | "24h" | "7d" | "30d";
  windowHours: number;
  totalCalls: number;
  status2xx: number;
  status4xx: number;
  status5xx: number;
  errorRatePct: number;
  p50LatencyMs: number | null;
  p95LatencyMs: number | null;
  hourlyBuckets: ApiKeyUsageBucket[];
}

interface ApiKeySummary {
  id: string;
  prefix: string;
  name: string;
  revoked: boolean;
}

interface LoadedUsage {
  key: ApiKeySummary;
  usage: ApiKeyUsageResult;
}

const WINDOW_OPTIONS: { value: ApiKeyUsageResult["window"]; label: string }[] = [
  { value: "1h", label: "Last hour" },
  { value: "24h", label: "Last 24 hours" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
];

function StatTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "default" | "warn" | "bad";
}) {
  const toneClass =
    tone === "bad"
      ? "text-red-400"
      : tone === "warn"
        ? "text-amber-400"
        : "text-white";
  return (
    <div className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}

/** Real inline SVG stacked-bar time series -- no charting dependency. */
function UsageTimeSeries({ buckets }: { buckets: ApiKeyUsageBucket[] }) {
  if (buckets.length === 0) {
    return (
      <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-6 text-center text-sm text-gray-500">
        No calls recorded in this window.
      </p>
    );
  }

  const width = 720;
  const height = 160;
  const paddingLeft = 8;
  const paddingBottom = 8;
  const plotWidth = width - paddingLeft * 2;
  const plotHeight = height - paddingBottom;
  const maxCalls = Math.max(...buckets.map((b) => b.calls), 1);
  const barGap = 2;
  const barWidth = Math.max(1, plotWidth / buckets.length - barGap);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      role="img"
      aria-label={`Calls per hour, ${buckets.length} buckets, max ${maxCalls} calls`}
    >
      {buckets.map((b, i) => {
        const x = paddingLeft + i * (barWidth + barGap);
        const total = Math.max(b.calls, 1);
        const scale = plotHeight / maxCalls;
        const h2xx = (b.status2xx / total) * b.calls * scale;
        const h4xx = (b.status4xx / total) * b.calls * scale;
        const h5xx = (b.status5xx / total) * b.calls * scale;
        let yCursor = plotHeight;
        const segments: { height: number; className: string }[] = [
          { height: h5xx, className: "fill-red-500" },
          { height: h4xx, className: "fill-amber-500" },
          { height: h2xx, className: "fill-emerald-500" },
        ];
        return (
          <g key={b.hour}>
            {segments.map((seg, si) => {
              if (seg.height <= 0) return null;
              yCursor -= seg.height;
              return (
                <rect
                  key={si}
                  x={x}
                  y={yCursor}
                  width={barWidth}
                  height={seg.height}
                  className={seg.className}
                >
                  <title>
                    {new Date(b.hour).toLocaleString()} -- {b.calls} calls ({b.status2xx} 2xx, {b.status4xx}{" "}
                    4xx, {b.status5xx} 5xx)
                  </title>
                </rect>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

export default function ApiKeyUsagePanel({ orgId, keyId }: { orgId: string; keyId: string }) {
  const [window, setWindow] = useState<ApiKeyUsageResult["window"]>("24h");
  const [state, setState] = useState<LoadedUsage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orgId || !keyId) return;
    setLoading(true);
    setError(null);
    fetch(
      `/api/orgs/${encodeURIComponent(orgId)}/api-keys/${encodeURIComponent(keyId)}/usage?window=${window}`,
    )
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setState(body as LoadedUsage);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [orgId, keyId, window]);

  return (
    <div className="rounded-md border border-gray-800 bg-gray-900/20 p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">
            Usage {state?.key ? `-- ${state.key.name || state.key.prefix}` : ""}
          </h3>
          <p className="text-xs text-gray-500">Calls, status codes, and latency for this key.</p>
        </div>
        <select
          value={window}
          onChange={(e) => setWindow(e.target.value as ApiKeyUsageResult["window"])}
          className="rounded-md border border-gray-700 bg-gray-900 px-2 py-1 text-xs text-white"
        >
          {WINDOW_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="text-sm text-gray-400">loading...</p>}
      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {state && !loading && !error && (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Total calls" value={state.usage.totalCalls.toLocaleString()} />
            <StatTile
              label="Error rate"
              value={`${state.usage.errorRatePct.toFixed(2)}%`}
              tone={
                state.usage.errorRatePct >= 5 ? "bad" : state.usage.errorRatePct >= 1 ? "warn" : "default"
              }
            />
            <StatTile
              label="p50 latency"
              value={state.usage.p50LatencyMs != null ? `${state.usage.p50LatencyMs} ms` : "--"}
            />
            <StatTile
              label="p95 latency"
              value={state.usage.p95LatencyMs != null ? `${state.usage.p95LatencyMs} ms` : "--"}
            />
          </div>

          <div className="mb-2 flex gap-4 text-xs text-gray-400">
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-emerald-500" />
              2xx ({state.usage.status2xx.toLocaleString()})
            </span>
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-amber-500" />
              4xx ({state.usage.status4xx.toLocaleString()})
            </span>
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-red-500" />
              5xx ({state.usage.status5xx.toLocaleString()})
            </span>
          </div>

          <UsageTimeSeries buckets={state.usage.hourlyBuckets} />
        </>
      )}
    </div>
  );
}
