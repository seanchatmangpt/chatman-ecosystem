"use client";

import { useState } from "react";
import Nav from "@/components/Nav";

// Real, on-demand hash-chain integrity attestation UI -- calls
// GET /api/audit/integrity-report?orgId=&from=&to= (lib/audit-integrity.ts's
// verifyHashChain), the tamper-evidence PROOF a Fortune-5 SOC2/forensic-
// readiness reviewer asks for ("prove your audit log has not been
// tampered with"), distinct from the raw SIEM export at /audit's own
// export flow. This page is a thin client -- no server-fetched initial
// state, because the report is always requested fresh, org- and
// period-scoped, never rendered from a cached/default query the way
// /audit's own page pre-loads the first 50 rows. Auth is enforced
// server-side by the route handler's own requireRoleIn(session, orgNs,
// "owner") check; a caller without access simply gets a real 401/403/404
// rendered from the JSON body below, same "the page renders the API's own
// error, it does not duplicate the authorization decision" discipline
// app/audit/page.tsx already documents for GET /api/audit.

interface IntegrityReport {
  orgId: string;
  from: string | null;
  to: string | null;
  verified: boolean;
  rowsChecked: number;
  firstBreakAt: string | null;
  generatedAt: string;
}

export default function AuditIntegrityPage() {
  const [orgId, setOrgId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<IntegrityReport | null>(null);

  async function runAttestation(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId.trim()) {
      setError("orgId is required");
      return;
    }
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const search = new URLSearchParams({ orgId: orgId.trim() });
      if (from.trim()) search.set("from", from.trim());
      if (to.trim()) search.set("to", to.trim());
      const res = await fetch(`/api/audit/integrity-report?${search.toString()}`, {
        method: "GET",
        cache: "no-store",
      });
      const body = await res.json();
      if (!res.ok) {
        setError(typeof body?.error === "string" ? body.error : `request failed (${res.status})`);
        return;
      }
      setReport(body as IntegrityReport);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Audit Log Integrity Attestation</h1>
        <p className="mb-8 max-w-3xl text-sm text-gray-400">
          Real, on-demand tamper-evidence proof for one org&apos;s slice of{" "}
          <code>platform_console.audit_log</code> -- distinct from the raw SIEM export. Each run
          re-derives the hash chain live against the current table (
          <code>lib/audit-integrity.ts</code>&apos;s <code>verifyHashChain</code>) and reports a
          computed verification result, not the raw chain to re-derive yourself. Nothing here is
          cached or pre-computed: every attestation reflects the table as it is at the moment you
          run it. Owner-only for the org you query, enforced server-side by{" "}
          <code>GET /api/audit/integrity-report</code>.
        </p>

        <form onSubmit={runAttestation} className="mb-8 space-y-4 rounded-md border border-gray-800 p-5">
          <div>
            <label htmlFor="orgId" className="mb-1 block text-sm font-medium text-gray-300">
              Org ID
            </label>
            <input
              id="orgId"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              placeholder="org-acme"
              required
              className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="from" className="mb-1 block text-sm font-medium text-gray-300">
                From (RFC3339, optional)
              </label>
              <input
                id="from"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                placeholder="2026-07-01T00:00:00Z"
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label htmlFor="to" className="mb-1 block text-sm font-medium text-gray-300">
                To (RFC3339, optional)
              </label>
              <input
                id="to"
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="2026-08-01T00:00:00Z"
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
          >
            {loading ? "Verifying..." : "Run attestation"}
          </button>
        </form>

        {error && (
          <p className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        )}

        {report && (
          <div
            className={`rounded-md border px-5 py-4 text-sm ${
              report.verified
                ? "border-emerald-900 bg-emerald-950/40 text-emerald-300"
                : "border-red-900 bg-red-950/40 text-red-300"
            }`}
          >
            <p className="text-base font-semibold">
              {report.verified ? "Chain verified -- no tampering detected" : "Chain integrity FAILED"}
            </p>
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-gray-300">
              <dt className="text-gray-500">Org</dt>
              <dd>
                <code>{report.orgId}</code>
              </dd>
              <dt className="text-gray-500">Period</dt>
              <dd>
                {report.from ?? "(beginning)"} -&gt; {report.to ?? "(now)"}
              </dd>
              <dt className="text-gray-500">Rows checked</dt>
              <dd>{report.rowsChecked}</dd>
              <dt className="text-gray-500">First break</dt>
              <dd>{report.firstBreakAt ?? "none"}</dd>
              <dt className="text-gray-500">Generated at</dt>
              <dd>{report.generatedAt}</dd>
            </dl>
          </div>
        )}
      </main>
    </>
  );
}
