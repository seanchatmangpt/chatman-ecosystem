"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type {
  ComplianceCadence,
  ComplianceCadenceInterval,
  ComplianceReport,
} from "@/lib/compliance-report";

export interface CompliancePanelReportSummary {
  reportId: string;
  periodStart: string;
  periodEnd: string;
  generatedAt: string;
  generatedBy: string;
  sections: ComplianceReport["sections"];
  downloadUrl: string;
  csvUrl: string;
  ndjsonUrl: string;
}

export interface CompliancePanelProps {
  orgId: string;
  namespace: string;
  cadence: ComplianceCadence | null;
  cronSchedule: string | null;
  reports: CompliancePanelReportSummary[];
  canManageCadence: boolean;
  canGenerate: boolean;
}

/**
 * Real GET/POST/PUT `/api/orgs/[id]/compliance-reports` client -> lib/
 * compliance-report.ts. Same "no optimistic UI, `router.refresh()` re-
 * reads the live ConfigMap server-side after a real 2xx" convention
 * IpAllowlistPanel already follows -- a report only appears in the list
 * after a real POST has actually stored it.
 */
export default function CompliancePanel({
  orgId,
  namespace,
  cadence,
  cronSchedule,
  reports,
  canManageCadence,
  canGenerate,
}: CompliancePanelProps) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interval, setInterval] = useState<ComplianceCadenceInterval>(cadence?.interval ?? "weekly");

  const mostRecent = reports[0] ?? null;

  async function saveCadence() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/compliance-reports`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ interval }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function generateNow() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/compliance-reports`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({}),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-1 text-base font-medium text-white">Report cadence -- {namespace}</h2>
        <p className="mb-4 text-xs text-gray-500">
          Determines the k8s CronJob schedule (<code>weekly</code> = Monday 06:00 UTC,{" "}
          <code>monthly</code> = 1st of the month 06:00 UTC) and the default trailing period an
          on-demand generation covers when no explicit period is given.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={interval}
            disabled={!canManageCadence || busy}
            onChange={(e) => setInterval(e.target.value as ComplianceCadenceInterval)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            <option value="weekly">weekly</option>
            <option value="monthly">monthly</option>
          </select>
          {canManageCadence && (
            <button
              type="button"
              disabled={busy}
              onClick={() => void saveCadence()}
              className="rounded-md border border-border bg-panel px-4 py-2 text-sm text-white hover:bg-bg disabled:opacity-50"
            >
              Save cadence
            </button>
          )}
          {canGenerate && (
            <button
              type="button"
              disabled={busy}
              onClick={() => void generateNow()}
              className="rounded-md border border-border bg-panel px-4 py-2 text-sm text-white hover:bg-bg disabled:opacity-50"
            >
              Generate now
            </button>
          )}
        </div>
        {cadence && (
          <p className="mt-3 text-xs text-gray-500">
            currently set: <code>{cadence.interval}</code> (cron <code>{cronSchedule}</code>) by{" "}
            {cadence.setBy} at {cadence.setAt}
          </p>
        )}
        {!cadence && <p className="mt-3 text-xs text-gray-500">no cadence set yet</p>}
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      </div>

      {mostRecent && (
        <div className="card p-6">
          <h2 className="mb-4 text-base font-medium text-white">Most recent report summary</h2>
          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-xs text-gray-500">Audit events</dt>
              <dd className="font-mono text-white">{mostRecent.sections.auditEventCount}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">IP allowlist entries</dt>
              <dd className="font-mono text-white">{mostRecent.sections.ipAllowlistSnapshot.length}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Cost anomalies in period</dt>
              <dd className="font-mono text-white">{mostRecent.sections.costAnomaliesInPeriod.length}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Active policy bindings</dt>
              <dd className="font-mono text-white">
                {mostRecent.sections.activePolicyBindings.bindings.length}
              </dd>
            </div>
          </dl>
          <p className="mt-3 text-xs text-gray-500">
            period {mostRecent.periodStart} &rarr; {mostRecent.periodEnd}, generated{" "}
            {mostRecent.generatedAt} by {mostRecent.generatedBy}
          </p>
        </div>
      )}

      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Generated reports</h2>
        {reports.length === 0 && <p className="text-sm text-gray-500">No reports generated yet.</p>}
        {reports.length > 0 && (
          <div className="divide-y divide-border">
            {reports.map((r) => (
              <div key={r.reportId} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-mono text-sm text-white">{r.reportId}</p>
                  <p className="text-xs text-gray-500">
                    {r.periodStart} &rarr; {r.periodEnd} &middot; {r.sections.auditEventCount} audit
                    events &middot; generated {r.generatedAt} by {r.generatedBy}
                  </p>
                </div>
                <div className="flex gap-2">
                  <a
                    href={r.downloadUrl}
                    className="rounded-md border border-border bg-panel px-3 py-1 text-xs text-white hover:bg-bg"
                  >
                    JSON
                  </a>
                  <a
                    href={r.csvUrl}
                    className="rounded-md border border-border bg-panel px-3 py-1 text-xs text-white hover:bg-bg"
                  >
                    CSV
                  </a>
                  <a
                    href={r.ndjsonUrl}
                    className="rounded-md border border-border bg-panel px-3 py-1 text-xs text-white hover:bg-bg"
                  >
                    NDJSON
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
