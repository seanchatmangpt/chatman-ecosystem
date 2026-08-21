"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";

type IncidentSeverity = "minor" | "major" | "critical";
type IncidentStatus = "open" | "resolved";

interface Incident {
  id: string;
  orgId: string | null;
  componentId: string;
  startedAt: string;
  resolvedAt: string | null;
  severity: IncidentSeverity;
  rootCause: string | null;
  status: IncidentStatus;
}

interface MonthlyUptimeReport {
  orgId: string;
  month: string;
  slaTier: string;
  slaUptimeTargetPct: number;
  totalMinutesInMonth: number;
  downtimeMinutes: number;
  actualUptimePct: number;
  metTarget: boolean;
  incidentCount: number;
}

interface CreditResult {
  owed: boolean;
  shortfallPct: number;
  creditPctOfMonthlySpend: number;
  illustrative: true;
}

function currentMonth(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

const SEVERITY_COLOR: Record<IncidentSeverity, string> = {
  minor: "bg-amber-500",
  major: "bg-orange-500",
  critical: "bg-red-500",
};

// Real incident timeline + monthly SLA-compliance card: closes the gap
// GET /api/orgs/[id]/sla's own page (app/org/sla/page.tsx) leaves open --
// that page can only ever show "no incident/downtime tracking wired up
// yet". This page reads the two new endpoints (lib/incidents.ts's Postgres
// ledger, itself derived from real Prometheus down spans) that give an
// enterprise buyer's procurement/legal review a real, auditable number
// instead of an always-compliant placeholder.
function OrgIncidentsPageInner() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";

  const [month, setMonth] = useState(currentMonth());
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [report, setReport] = useState<MonthlyUptimeReport | null>(null);
  const [credit, setCredit] = useState<CreditResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      fetch(`/api/incidents?orgId=${encodeURIComponent(orgId)}&limit=100`).then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `incidents request failed (${res.status})`);
        return body.rows as Incident[];
      }),
      fetch(
        `/api/orgs/${encodeURIComponent(orgId)}/sla-credits?month=${encodeURIComponent(month)}`,
      ).then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `sla-credits request failed (${res.status})`);
        return body as { report: MonthlyUptimeReport; credit: CreditResult };
      }),
    ])
      .then(([rows, slaCredits]) => {
        setIncidents(rows);
        setReport(slaCredits.report);
        setCredit(slaCredits.credit);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [orgId, month]);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">SLA Incidents &amp; Credits</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real incident timeline derived from Prometheus <code>up</code> spans
          (<code>lib/status-page.ts</code>), and the monthly uptime% actually observed against
          this org&apos;s contracted SLA target. The credit figure is explicitly illustrative --
          see the schedule note below.
        </p>

        {!orgId && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Append <code>?orgId=&lt;org id&gt;</code> to this page&apos;s URL to view that
            org&apos;s incident timeline and SLA credit report.
          </div>
        )}

        {orgId && (
          <>
            <div className="mb-6 flex items-center gap-3">
              <label className="text-sm text-gray-400" htmlFor="month">
                Month
              </label>
              <input
                id="month"
                type="month"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                className="rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm text-white"
              />
            </div>

            {loading && <p className="mb-4 text-sm text-gray-400">loading...</p>}
            {error && (
              <p className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                {error}
              </p>
            )}

            {report && credit && (
              <div className="mb-8 rounded-md border border-gray-800 bg-gray-950 px-5 py-4">
                <p className="mb-3 text-sm font-medium text-gray-300">
                  {report.month} compliance -- {report.slaTier} tier
                </p>
                <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Target</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {report.slaUptimeTargetPct}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Actual</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {report.actualUptimePct.toFixed(4)}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Downtime</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {report.downtimeMinutes.toFixed(1)} min
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Incidents</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {report.incidentCount}
                    </dd>
                  </div>
                </dl>
                <div className="mt-4 flex items-center gap-2">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      report.metTarget ? "bg-emerald-500" : "bg-red-500"
                    }`}
                  />
                  <span className="text-sm text-gray-300">
                    {report.metTarget ? "SLA target met" : "SLA target missed"}
                  </span>
                </div>
                {credit.owed && (
                  <p className="mt-3 rounded-md border border-red-900 bg-red-950/30 px-3 py-2 text-sm text-red-300">
                    Illustrative credit owed: {credit.creditPctOfMonthlySpend.toFixed(1)}% of
                    monthly spend (shortfall {credit.shortfallPct.toFixed(4)} pts below target).
                    Illustrative percentage-of-spend schedule, not a real contracted refund --
                    see <code>lib/incidents.ts</code>&apos;s <code>ILLUSTRATIVE_CREDIT_SCHEDULE</code>.
                  </p>
                )}
              </div>
            )}

            <h2 className="mb-3 text-lg font-semibold text-white">Incident timeline</h2>
            {incidents.length === 0 && !loading ? (
              <p className="text-sm text-gray-500">No incidents recorded for this org yet.</p>
            ) : (
              <ul className="space-y-2">
                {incidents.map((inc) => (
                  <li
                    key={inc.id}
                    className="rounded-md border border-gray-800 bg-gray-950 px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-block h-2 w-2 rounded-full ${SEVERITY_COLOR[inc.severity]}`}
                      />
                      <span className="text-sm font-medium text-white">{inc.componentId}</span>
                      <span className="text-xs uppercase tracking-wide text-gray-500">
                        {inc.severity} / {inc.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">
                      {new Date(inc.startedAt).toLocaleString()} -&gt;{" "}
                      {inc.resolvedAt ? new Date(inc.resolvedAt).toLocaleString() : "ongoing"}
                    </p>
                    {inc.rootCause && (
                      <p className="mt-1 text-xs text-gray-500">Root cause: {inc.rootCause}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </main>
    </>
  );
}

export default function OrgIncidentsPage() {
  return (
    <Suspense fallback={null}>
      <OrgIncidentsPageInner />
    </Suspense>
  );
}
