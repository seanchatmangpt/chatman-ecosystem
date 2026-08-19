"use client";

import { useEffect, useState } from "react";

// Historical spend/usage chart -- the exportable, multi-month
// counterpart to app/orgs/[id]/billing/page.tsx's point-in-time overage
// estimate widget. Fetches GET /api/orgs/[id]/billing/spend-history
// itself (same standalone-panel convention as
// app/orgs/[id]/api-keys/usage-panel.tsx) and renders a real inline SVG
// stacked-bar (cost by line item) + line (call volume) combo, plus a
// month-over-month delta annotation on the total-cost line -- no new
// chart library dependency.

type Granularity = "daily" | "monthly";

interface SpendHistoryBucket {
  periodStart: string;
  baseTierCostUsd: number;
  overageCostUsd: number;
  rateLimitAddonCostUsd: number;
  totalCostUsd: number;
  callVolume: number;
}

interface SpendHistoryResult {
  orgId: string;
  granularity: Granularity;
  from: string;
  to: string;
  buckets: SpendHistoryBucket[];
  totalCostUsd: number;
  hasStripeBilling: boolean;
}

const GRANULARITY_OPTIONS: { value: Granularity; label: string }[] = [
  { value: "monthly", label: "Monthly" },
  { value: "daily", label: "Daily" },
];

const MONTHS_OPTIONS = [3, 6, 12, 24];

function formatUsd(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

function formatPeriodLabel(periodStart: string, granularity: Granularity): string {
  const d = new Date(periodStart);
  return granularity === "monthly"
    ? d.toLocaleDateString(undefined, { month: "short", year: "2-digit" })
    : d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** Real inline SVG stacked-bar (cost line items) + line overlay (call
 * volume) combo -- no charting dependency, mirrors the SVG approach
 * app/orgs/[id]/api-keys/usage-panel.tsx already established for this
 * app's per-key usage chart. */
function SpendChart({ buckets, granularity }: { buckets: SpendHistoryBucket[]; granularity: Granularity }) {
  if (buckets.length === 0) {
    return (
      <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-6 text-center text-sm text-gray-500">
        No spend data in this window.
      </p>
    );
  }

  const width = 900;
  const height = 220;
  const paddingLeft = 8;
  const paddingBottom = 22;
  const plotWidth = width - paddingLeft * 2;
  const plotHeight = height - paddingBottom;
  const maxCost = Math.max(...buckets.map((b) => b.totalCostUsd), 0.01);
  const maxCalls = Math.max(...buckets.map((b) => b.callVolume), 1);
  const barGap = 2;
  const barWidth = Math.max(1, plotWidth / buckets.length - barGap);
  const costScale = plotHeight / maxCost;
  const callScale = plotHeight / maxCalls;

  // Real month-over-(or day-over-)prior-bucket delta line: for each
  // bucket after the first, `(cur - prev) / prev * 100`, null when the
  // prior bucket had zero cost (a %-of-zero delta is not a meaningful
  // number, so it is omitted rather than rendered as +Infinity/NaN).
  const deltas: (number | null)[] = buckets.map((b, i) => {
    if (i === 0) return null;
    const prev = buckets[i - 1].totalCostUsd;
    if (prev <= 0) return null;
    return ((b.totalCostUsd - prev) / prev) * 100;
  });

  const linePoints = buckets
    .map((b, i) => {
      const x = paddingLeft + i * (barWidth + barGap) + barWidth / 2;
      const y = plotHeight - b.callVolume * callScale;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      role="img"
      aria-label={`Spend history, ${buckets.length} ${granularity} buckets, total ${formatUsd(
        buckets.reduce((s, b) => s + b.totalCostUsd, 0),
      )}`}
    >
      {buckets.map((b, i) => {
        const x = paddingLeft + i * (barWidth + barGap);
        const segments: { value: number; className: string; label: string }[] = [
          { value: b.baseTierCostUsd, className: "fill-sky-500", label: "Base tier" },
          { value: b.overageCostUsd, className: "fill-amber-500", label: "Overage" },
          { value: b.rateLimitAddonCostUsd, className: "fill-purple-500", label: "Rate-limit add-on" },
        ];
        let yCursor = plotHeight;
        const delta = deltas[i];
        return (
          <g key={b.periodStart}>
            {segments.map((seg, si) => {
              const h = seg.value * costScale;
              if (h <= 0) return null;
              yCursor -= h;
              return (
                <rect key={si} x={x} y={yCursor} width={barWidth} height={h} className={seg.className}>
                  <title>
                    {formatPeriodLabel(b.periodStart, granularity)} -- {seg.label}: {formatUsd(seg.value)}
                    {delta != null ? ` (${delta >= 0 ? "+" : ""}${delta.toFixed(1)}% vs prior)` : ""}
                  </title>
                </rect>
              );
            })}
            {delta != null && Math.abs(delta) >= 1 && (
              <text
                x={x + barWidth / 2}
                y={Math.max(10, yCursor - 4)}
                textAnchor="middle"
                className={delta >= 0 ? "fill-red-400" : "fill-emerald-400"}
                fontSize="9"
              >
                {delta >= 0 ? "+" : ""}
                {delta.toFixed(0)}%
              </text>
            )}
            <text
              x={x + barWidth / 2}
              y={height - 6}
              textAnchor="middle"
              className="fill-gray-500"
              fontSize="9"
            >
              {buckets.length <= 24 || i % Math.ceil(buckets.length / 24) === 0
                ? formatPeriodLabel(b.periodStart, granularity)
                : ""}
            </text>
          </g>
        );
      })}
      <polyline points={linePoints} fill="none" stroke="currentColor" className="text-emerald-400" strokeWidth={1.5} />
      {buckets.map((b, i) => {
        const x = paddingLeft + i * (barWidth + barGap) + barWidth / 2;
        const y = plotHeight - b.callVolume * callScale;
        return (
          <circle key={`pt-${b.periodStart}`} cx={x} cy={y} r={2} className="fill-emerald-400">
            <title>
              {formatPeriodLabel(b.periodStart, granularity)} -- {b.callVolume.toLocaleString()} calls
            </title>
          </circle>
        );
      })}
    </svg>
  );
}

export default function SpendHistoryChart({ orgId }: { orgId: string }) {
  const [granularity, setGranularity] = useState<Granularity>("monthly");
  const [months, setMonths] = useState(12);
  const [state, setState] = useState<SpendHistoryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(
      `/api/orgs/${encodeURIComponent(orgId)}/billing/spend-history?granularity=${granularity}&months=${months}`,
    )
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setState(body as SpendHistoryResult);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [orgId, granularity, months]);

  const csvHref = `/api/orgs/${encodeURIComponent(orgId)}/billing/spend-history?granularity=${granularity}&months=${months}&format=csv`;

  return (
    <div className="rounded-md border border-gray-800 bg-gray-900/20 p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-white">Spend history</h3>
          <p className="text-xs text-gray-500">
            Historical spend by usage dimension, reconciled against real Stripe invoice history.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={granularity}
            onChange={(e) => setGranularity(e.target.value as Granularity)}
            className="rounded-md border border-gray-700 bg-gray-900 px-2 py-1 text-xs text-white"
          >
            {GRANULARITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <select
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
            className="rounded-md border border-gray-700 bg-gray-900 px-2 py-1 text-xs text-white"
          >
            {MONTHS_OPTIONS.map((m) => (
              <option key={m} value={m}>
                Last {m} mo
              </option>
            ))}
          </select>
          <a
            href={csvHref}
            className="rounded-md border border-gray-700 bg-gray-900 px-2 py-1 text-xs text-white hover:bg-gray-800"
          >
            Export CSV
          </a>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-400">loading...</p>}
      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">{error}</p>
      )}

      {state && !loading && !error && (
        <>
          {!state.hasStripeBilling && (
            <p className="mb-3 rounded-md border border-amber-900 bg-amber-950/30 px-3 py-2 text-xs text-amber-300">
              No Stripe customer/subscription on file for this org yet -- dollar figures below are
              honestly zero, not fabricated. Call-volume (green line) is real regardless.
            </p>
          )}

          <div className="mb-4 flex flex-wrap gap-4 text-xs text-gray-400">
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-sky-500" />
              Base tier
            </span>
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-amber-500" />
              Overage
            </span>
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-purple-500" />
              Rate-limit add-on
            </span>
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-400" />
              Call volume (right axis)
            </span>
          </div>

          <SpendChart buckets={state.buckets} granularity={state.granularity} />

          <p className="mt-3 text-sm text-white">
            Total spend, last {months} mo: <span className="font-semibold">{formatUsd(state.totalCostUsd)}</span>
          </p>
        </>
      )}
    </div>
  );
}
