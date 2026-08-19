import { getTrustPageData } from "@/lib/trust-page";
import type { Severity } from "@/lib/vuln-scan";

// Public Trust / Security Posture page -- no session check, no Nav, same
// "reachable with no login" convention app/app/status/page.tsx already
// establishes (listed alongside it in middleware.ts's PUBLIC_PATHS). This
// is the artifact enterprise security-review teams ask vendors for during
// procurement: real patch cadence (last scan timestamp), real open-CVE
// counts by severity, real cert-expiry posture, real uptime -- aggregated
// from lib/status-page.ts / lib/vuln-scan.ts / lib/cert-lifecycle.ts, the
// same live sources the authenticated dashboards already use, never a
// static claim. force-dynamic so every render re-runs the real queries.
export const dynamic = "force-dynamic";

const SEVERITY_ORDER: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"];
const SEVERITY_COLOR: Record<Severity, string> = {
  CRITICAL: "text-red-400 border-red-900 bg-red-950/40",
  HIGH: "text-orange-400 border-orange-900 bg-orange-950/40",
  MEDIUM: "text-amber-400 border-amber-900 bg-amber-950/40",
  LOW: "text-sky-400 border-sky-900 bg-sky-950/40",
  UNKNOWN: "text-gray-400 border-gray-800 bg-gray-950/40",
};

function formatPercent(v: number | null): string {
  if (v === null) return "no data";
  return `${v.toFixed(2)}%`;
}

export default async function TrustPage() {
  const data = await getTrustPageData();
  const uptime = data.uptime;
  const vuln = data.vulnPosture;
  const cert = data.certPosture;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white">Trust &amp; Security Posture</h1>
        <p className="mt-2 text-sm text-gray-400">
          Real, live security posture -- patch cadence, open CVE counts by
          severity, TLS certificate expiry, and uptime -- computed from this
          platform&apos;s own running scan, certificate, and monitoring data
          on every load. No manually-entered claims. See also the{" "}
          <a href="/status" className="underline">
            public status page
          </a>
          .
        </p>
      </div>

      {/* Uptime */}
      <section className="mb-6">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-gray-500">Uptime</h2>
        {!uptime || !uptime.reachable ? (
          <div className="card rounded-md border border-amber-900 bg-amber-950/30 px-4 py-3 text-sm text-amber-300">
            Uptime data is not available right now
            {uptime?.prometheusError ? ` (${uptime.prometheusError})` : ""}. No uptime figure is
            shown rather than a fabricated one.
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-gray-400">
                  <th className="px-6 py-3 font-normal">Component</th>
                  <th className="px-6 py-3 font-normal">State</th>
                  <th className="px-6 py-3 font-normal">Uptime (24h)</th>
                </tr>
              </thead>
              <tbody>
                {uptime.components.map((c) => (
                  <tr key={c.id} className="border-b border-border/50">
                    <td className="px-6 py-4 text-gray-100">{c.label}</td>
                    <td className="px-6 py-4 text-gray-300">{c.state}</td>
                    <td className="px-6 py-4 text-gray-100">{formatPercent(c.uptimePercentDay)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Vulnerability posture */}
      <section className="mb-6">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-gray-500">
          Open Vulnerabilities (Container Images)
        </h2>
        {!vuln || !vuln.reachable ? (
          <div className="card rounded-md border border-amber-900 bg-amber-950/30 px-4 py-3 text-sm text-amber-300">
            Vulnerability scan data is not available right now
            {vuln?.error ? ` (${vuln.error})` : ""}. No CVE count is shown rather than a
            fabricated one.
          </div>
        ) : vuln.scannedAt === null ? (
          <div className="card rounded-md border border-border px-4 py-3 text-sm text-gray-400">
            No vulnerability scan has run yet in this environment.
          </div>
        ) : (
          <div className="card p-6">
            <p className="mb-4 text-sm text-gray-400">
              Last scan: {vuln.scannedAt} · {vuln.imagesScanned} image
              {vuln.imagesScanned === 1 ? "" : "s"} · {vuln.complete ? "complete" : "in progress"}
            </p>
            <div className="flex flex-wrap gap-3">
              {SEVERITY_ORDER.map((sev) => (
                <div
                  key={sev}
                  className={`min-w-[7rem] rounded-md border px-4 py-3 text-center ${SEVERITY_COLOR[sev]}`}
                >
                  <div className="text-2xl font-semibold">{vuln.severityCounts[sev]}</div>
                  <div className="text-xs uppercase tracking-wide">{sev}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Certificate posture */}
      <section className="mb-6">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-gray-500">
          TLS Certificate Posture
        </h2>
        {!cert || !cert.reachable ? (
          <div className="card rounded-md border border-amber-900 bg-amber-950/30 px-4 py-3 text-sm text-amber-300">
            Certificate posture is not available right now
            {cert?.error ? ` (${cert.error})` : ""}. No expiry figure is shown rather than a
            fabricated one.
          </div>
        ) : (
          <div className="card grid grid-cols-2 gap-4 p-6 sm:grid-cols-4">
            <div>
              <div className="text-2xl font-semibold text-white">{cert.totalCertificates}</div>
              <div className="text-xs text-gray-500">Managed certificates</div>
            </div>
            <div>
              <div className="text-2xl font-semibold text-white">
                {cert.minDaysUntilExpiry === null ? "--" : cert.minDaysUntilExpiry}
              </div>
              <div className="text-xs text-gray-500">Days to soonest expiry</div>
            </div>
            <div>
              <div className="text-2xl font-semibold text-amber-300">{cert.expiringSoonCount}</div>
              <div className="text-xs text-gray-500">
                Expiring within {cert.expiryWarningThresholdDays}d
              </div>
            </div>
            <div>
              <div className="text-2xl font-semibold text-red-400">{cert.expiredCount}</div>
              <div className="text-xs text-gray-500">Expired</div>
            </div>
          </div>
        )}
      </section>

      <p className="mt-6 text-xs text-gray-500">
        Generated {data.generatedAt} · JSON at{" "}
        <a href="/api/trust" className="underline">
          /api/trust
        </a>
      </p>
    </main>
  );
}
