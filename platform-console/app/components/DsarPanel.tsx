"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

// Re-declared here as a plain local type, not `import type` from
// lib/dsar.ts -- lib/dsar.ts pulls in lib/audit-db.ts (the `pg` driver)
// and lib/k8s.ts (fs/https), neither of which must ever end up in the
// client bundle. Same discipline components/ApprovalsPanel.tsx already
// documents for lib/approval-workflow.ts.
interface DsarRequest {
  requestId: string;
  orgId: string;
  subjectEmail: string;
  kind: "export" | "erasure";
  status: "pending" | "processing" | "complete" | "failed";
  requestedBy: string;
  requestedAt: string;
  completedAt?: string;
  error?: string;
  downloadToken?: string;
  downloadExpiresAt?: string;
  bundleFilename?: string;
  bundleRowCount?: number;
  redactedAuditRowCount?: number;
  redactedMembership?: boolean;
}

function statusBadgeClass(status: DsarRequest["status"]): string {
  if (status === "complete") return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
  if (status === "failed") return "border-red-900 bg-red-950/40 text-red-300";
  return "border-amber-900 bg-amber-950/40 text-amber-300";
}

/**
 * Real per-org DSAR (GDPR Art.15/17 / CCPA) request panel for org owners
 * -- files a real access-export request (POST /api/privacy/request-export,
 * processed by lib/dsar.ts's real background poller) or a real
 * maker-checker-gated erasure request (POST /api/privacy/request-erasure,
 * reusing the exact same /approvals workflow ApprovalsPanel already
 * surfaces), then polls GET /api/privacy/status for real progress.
 */
export default function DsarPanel({ orgId }: { orgId: string }) {
  const [subjectEmail, setSubjectEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [requests, setRequests] = useState<DsarRequest[]>([]);

  async function refresh() {
    try {
      const res = await fetch(`/api/privacy/status?orgId=${encodeURIComponent(orgId)}`);
      const body = await res.json();
      if (res.ok) setRequests(body.requests ?? []);
    } catch {
      // best-effort refresh -- the explicit action buttons below already
      // surface real errors for the action that actually failed
    }
  }

  async function submit(kind: "export" | "erasure") {
    if (!subjectEmail.trim()) {
      setError("subjectEmail is required");
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const path = kind === "export" ? "/api/privacy/request-export" : "/api/privacy/request-erasure";
      const res = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ orgId, subjectEmail: subjectEmail.trim() }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      if (body.status === "pending_approval") {
        setNotice(
          `Erasure requires a second, distinct owner to approve request ${body.approval.requestId} ` +
            "in the Approvals panel before it will run.",
        );
      } else {
        setNotice(kind === "export" ? "Export request filed -- refresh below for progress." : "Erasure complete.");
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400" htmlFor="dsar-subject-email">
            Subject email
          </label>
          <input
            id="dsar-subject-email"
            type="email"
            value={subjectEmail}
            onChange={(e) => setSubjectEmail(e.target.value)}
            placeholder="person@example.com"
            className="w-64 rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </div>
        <Button type="button" onClick={() => submit("export")} disabled={busy}>
          {busy ? "Working..." : "Request data export (Art.15)"}
        </Button>
        <Button
          type="button"
          onClick={() => submit("erasure")}
          disabled={busy}
          className="border border-red-900 bg-red-950/40 text-red-200 hover:bg-red-950/60"
        >
          {busy ? "Working..." : "Request erasure (Art.17)"}
        </Button>
        <Button type="button" onClick={refresh} disabled={busy}>
          Refresh requests
        </Button>
      </div>

      {error && (
        <p className="max-w-xl break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
      {notice && (
        <p className="max-w-xl break-all rounded-md border border-amber-900 bg-amber-950/40 px-3 py-2 text-xs text-amber-200">
          {notice}
        </p>
      )}

      {requests.length > 0 && (
        <table className="w-full max-w-2xl text-xs text-gray-300">
          <thead>
            <tr className="text-left text-gray-500">
              <th className="pb-1 pr-3">Subject</th>
              <th className="pb-1 pr-3">Kind</th>
              <th className="pb-1 pr-3">Status</th>
              <th className="pb-1 pr-3">Requested</th>
              <th className="pb-1">Result</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.requestId} className="border-t border-border/60">
                <td className="py-1 pr-3 font-mono">{r.subjectEmail}</td>
                <td className="py-1 pr-3">{r.kind}</td>
                <td className="py-1 pr-3">
                  <span className={`rounded-md border px-2 py-0.5 ${statusBadgeClass(r.status)}`}>{r.status}</span>
                </td>
                <td className="py-1 pr-3">{new Date(r.requestedAt).toLocaleString()}</td>
                <td className="py-1">
                  {r.status === "complete" && r.kind === "export" && r.downloadToken && (
                    <a
                      className="break-all text-white underline"
                      href={`/api/privacy/download?token=${encodeURIComponent(r.downloadToken)}`}
                    >
                      Download {r.bundleFilename} ({r.bundleRowCount} rows)
                    </a>
                  )}
                  {r.status === "complete" && r.kind === "erasure" && (
                    <span>
                      redacted {r.redactedAuditRowCount ?? 0} audit rows
                      {r.redactedMembership ? ", removed membership" : ""}
                    </span>
                  )}
                  {r.status === "failed" && <span className="text-red-300">{r.error}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
