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

/**
 * Read-only summary of this org's most recent Workforce Security-
 * Training & Background-Check Attestation (lib/personnel-attestation.ts,
 * GET/POST /api/compliance/personnel-attestation) -- passed in
 * pre-fetched by the server page, same "already-fetched data as a plain
 * prop, this panel never re-fetches read data itself" convention
 * `reports`/`cadence` above already establish. `null` when this org has
 * never had an attestation recorded, or when the current session lacks
 * the platform-owner rank that endpoint requires (a per-org "owner"
 * alone cannot self-attest this control -- see that route's own header
 * comment) -- the page passes `null` in either case rather than this
 * component making its own auth decision.
 */
export interface CompliancePanelPersonnelAttestationSummary {
  attestedAt: string;
  attesterIdentifier: string;
  trainingCompletionPercent: number;
  privilegedBackgroundCheckClearedPercent: number;
  rosterSize: number;
}

/**
 * Third-Party Penetration-Test Attestation Register
 * (lib/pentest-attestation.ts): one real filed engagement plus its
 * real filed findings, server-fetched and passed as a prop -- same
 * "read data always arrives as a prop, this panel never re-fetches read
 * data itself" convention `reports`/`personnelAttestation` above already
 * establish.
 */
export interface CompliancePanelPentestFindingSummary {
  id: string;
  severity: string;
  title: string;
  status: string;
  filedAt: string;
  resolvedAt: string | null;
}

export interface CompliancePanelPentestEngagementSummary {
  id: string;
  testerFirm: string;
  scope: string;
  engagementType: string;
  startedAt: string;
  completedAt: string | null;
  nextDueDate: string;
  overdue: boolean;
  findings: CompliancePanelPentestFindingSummary[];
}

export interface CompliancePanelProps {
  orgId: string;
  namespace: string;
  cadence: ComplianceCadence | null;
  cronSchedule: string | null;
  reports: CompliancePanelReportSummary[];
  canManageCadence: boolean;
  canGenerate: boolean;
  personnelAttestation?: CompliancePanelPersonnelAttestationSummary | null;
  pentestEngagements?: CompliancePanelPentestEngagementSummary[];
  canFilePentest?: boolean;
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
  personnelAttestation = null,
  pentestEngagements = [],
  canFilePentest = false,
}: CompliancePanelProps) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interval, setInterval] = useState<ComplianceCadenceInterval>(cadence?.interval ?? "weekly");
  const [pentestError, setPentestError] = useState<string | null>(null);
  const [pentestBusy, setPentestBusy] = useState(false);
  const [newEngagement, setNewEngagement] = useState({
    testerFirm: "",
    scope: "",
    engagementType: "web_app",
    startedAt: "",
    nextDueDate: "",
  });

  async function fileEngagement() {
    setPentestBusy(true);
    setPentestError(null);
    try {
      const res = await fetch("/api/compliance/pentest", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          kind: "engagement",
          orgId,
          testerFirm: newEngagement.testerFirm,
          scope: newEngagement.scope,
          engagementType: newEngagement.engagementType,
          startedAt: newEngagement.startedAt ? new Date(newEngagement.startedAt).toISOString() : "",
          nextDueDate: newEngagement.nextDueDate ? new Date(newEngagement.nextDueDate).toISOString() : "",
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setPentestError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setNewEngagement({ testerFirm: "", scope: "", engagementType: "web_app", startedAt: "", nextDueDate: "" });
      router.refresh();
    } catch (err) {
      setPentestError(err instanceof Error ? err.message : String(err));
    } finally {
      setPentestBusy(false);
    }
  }

  async function markInProgress(findingId: string) {
    setPentestBusy(true);
    setPentestError(null);
    try {
      const res = await fetch(`/api/compliance/pentest/${findingId}`, { method: "PATCH" });
      const body = await res.json();
      if (!res.ok) {
        setPentestError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setPentestError(err instanceof Error ? err.message : String(err));
    } finally {
      setPentestBusy(false);
    }
  }

  async function requestResolve(findingId: string, resolution: "resolved" | "accepted_risk") {
    const resolutionNotes = window.prompt(
      `Resolution notes for marking this finding "${resolution}" (a second, distinct owner must still approve):`,
    );
    if (!resolutionNotes) return;
    setPentestBusy(true);
    setPentestError(null);
    try {
      const res = await fetch(`/api/compliance/pentest/${findingId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ resolution, resolutionNotes }),
      });
      const body = await res.json();
      if (!res.ok) {
        setPentestError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setPentestError(err instanceof Error ? err.message : String(err));
    } finally {
      setPentestBusy(false);
    }
  }

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
        <h2 className="mb-4 text-base font-medium text-white">
          Workforce security-training &amp; background-check attestation
        </h2>
        {!personnelAttestation && (
          <p className="text-sm text-gray-500">
            No attestation on file for this org yet, or the current session does not hold the
            platform-owner rank GET /api/compliance/personnel-attestation requires.
          </p>
        )}
        {personnelAttestation && (
          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-xs text-gray-500">Training completion</dt>
              <dd className="font-mono text-white">
                {personnelAttestation.trainingCompletionPercent}%
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Privileged background checks cleared</dt>
              <dd className="font-mono text-white">
                {personnelAttestation.privilegedBackgroundCheckClearedPercent}%
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Roster size</dt>
              <dd className="font-mono text-white">{personnelAttestation.rosterSize}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Attested</dt>
              <dd className="font-mono text-white">
                {personnelAttestation.attestedAt} by {personnelAttestation.attesterIdentifier}
              </dd>
            </div>
          </dl>
        )}
      </div>

      <div className="card p-6">
        <h2 className="mb-1 text-base font-medium text-white">
          Third-party penetration-test attestation register
        </h2>
        <p className="mb-4 text-xs text-gray-500">
          Real Postgres-backed ledger of every filed engagement and finding for this org. Closing
          a finding (<code>resolved</code>/<code>accepted_risk</code>) requires a second, distinct
          owner-role approver via <code>POST /api/approvals/[id]</code> -- see the Approvals panel.
        </p>

        {canFilePentest && (
          <div className="mb-6 flex flex-wrap items-end gap-3 rounded-md border border-border p-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">Tester firm</label>
              <input
                value={newEngagement.testerFirm}
                onChange={(e) => setNewEngagement({ ...newEngagement, testerFirm: e.target.value })}
                className="w-40 rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Scope</label>
              <input
                value={newEngagement.scope}
                onChange={(e) => setNewEngagement({ ...newEngagement, scope: e.target.value })}
                className="w-48 rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Type</label>
              <select
                value={newEngagement.engagementType}
                onChange={(e) => setNewEngagement({ ...newEngagement, engagementType: e.target.value })}
                className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-white"
              >
                <option value="network">network</option>
                <option value="web_app">web_app</option>
                <option value="mobile_app">mobile_app</option>
                <option value="cloud_config">cloud_config</option>
                <option value="red_team">red_team</option>
                <option value="social_engineering">social_engineering</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Started</label>
              <input
                type="date"
                value={newEngagement.startedAt}
                onChange={(e) => setNewEngagement({ ...newEngagement, startedAt: e.target.value })}
                className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Next due</label>
              <input
                type="date"
                value={newEngagement.nextDueDate}
                onChange={(e) => setNewEngagement({ ...newEngagement, nextDueDate: e.target.value })}
                className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-white"
              />
            </div>
            <button
              type="button"
              disabled={pentestBusy}
              onClick={() => void fileEngagement()}
              className="rounded-md border border-border bg-panel px-4 py-2 text-sm text-white hover:bg-bg disabled:opacity-50"
            >
              File engagement
            </button>
          </div>
        )}
        {pentestError && <p className="mb-3 text-sm text-red-400">{pentestError}</p>}

        {pentestEngagements.length === 0 && (
          <p className="text-sm text-gray-500">No pentest engagements filed for this org yet.</p>
        )}
        {pentestEngagements.length > 0 && (
          <div className="space-y-4">
            {pentestEngagements.map((e) => (
              <div key={e.id} className="rounded-md border border-border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm text-white">
                    <span className="font-medium">{e.testerFirm}</span> &middot; {e.engagementType} &middot;{" "}
                    {e.scope}
                  </p>
                  {e.overdue && (
                    <span className="rounded-full border border-red-900 bg-red-950/40 px-2 py-0.5 text-xs text-red-300">
                      overdue
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  started {e.startedAt} &middot; next due {e.nextDueDate}
                  {e.completedAt ? ` · completed ${e.completedAt}` : ""}
                </p>
                {e.findings.length > 0 && (
                  <div className="mt-3 divide-y divide-border">
                    {e.findings.map((f) => (
                      <div key={f.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                        <div>
                          <p className="text-sm text-white">
                            [{f.severity}] {f.title}{" "}
                            <span className="font-mono text-xs text-gray-500">({f.status})</span>
                          </p>
                          <p className="text-xs text-gray-500">filed {f.filedAt}</p>
                        </div>
                        {canFilePentest && (f.status === "open" || f.status === "remediation_in_progress") && (
                          <div className="flex gap-2">
                            {f.status === "open" && (
                              <button
                                type="button"
                                disabled={pentestBusy}
                                onClick={() => void markInProgress(f.id)}
                                className="rounded-md border border-border bg-panel px-2 py-1 text-xs text-white hover:bg-bg disabled:opacity-50"
                              >
                                Mark in progress
                              </button>
                            )}
                            <button
                              type="button"
                              disabled={pentestBusy}
                              onClick={() => void requestResolve(f.id, "resolved")}
                              className="rounded-md border border-border bg-panel px-2 py-1 text-xs text-white hover:bg-bg disabled:opacity-50"
                            >
                              Request resolve
                            </button>
                            <button
                              type="button"
                              disabled={pentestBusy}
                              onClick={() => void requestResolve(f.id, "accepted_risk")}
                              className="rounded-md border border-border bg-panel px-2 py-1 text-xs text-white hover:bg-bg disabled:opacity-50"
                            >
                              Request accept-risk
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

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
