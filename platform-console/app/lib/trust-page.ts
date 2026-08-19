/**
 * Real Public Trust / Security Posture page data -- the single artifact
 * enterprise security-review teams actually ask vendors for during
 * procurement (SOC2-adjacent "show me your patch cadence, open CVE count
 * by severity, cert expiry posture, and uptime" ask), assembled from three
 * data sources this repo already computes for real, nothing new:
 *
 *   - `getStatusPageData()` (lib/status-page.ts) -- real Prometheus-backed
 *     uptime per component, the same data app/status already shows.
 *   - `getLatestVulnScanRun()` (lib/vuln-scan.ts) -- the most recent real
 *     `trivy` Indexed-Job scan of this platform's own built images,
 *     aggregated here into a single CRITICAL/HIGH/MEDIUM/LOW/UNKNOWN
 *     count across every scanned image, plus the scan's own timestamp.
 *   - `listManagedCertificates()` (lib/cert-lifecycle.ts) -- real
 *     `X509Certificate`-parsed TLS Secrets, reduced here to aggregate
 *     expiry posture only (soonest-expiry days + a count of certs inside
 *     `EXPIRY_WARNING_DAYS`) -- never the per-cert `secretName`/`hostname`/
 *     `subject`/`issuer` fields those real records carry, since this
 *     surface is PUBLIC and unauthenticated (see module doc comments on
 *     app/app/trust/page.tsx and app/app/api/trust/route.ts): no internal
 *     hostname, Secret name, or namespace ever appears in this module's
 *     output, only aggregate counts.
 *
 * Same no-fabrication discipline as lib/status-page.ts: a source that is
 * genuinely unreachable (Prometheus down, in-cluster k8s credentials
 * absent outside the pod, a scan that has never run) reports an honest
 * `null`/`reachable: false` on that section, never a fabricated "0 open
 * CVEs" or "100% uptime". Each of the three sources is fetched
 * independently (`Promise.allSettled`) so one source being down never
 * blanks out the other two.
 */
import { getStatusPageData, type StatusPageData } from "@/lib/status-page";
import { getLatestVulnScanRun, type Severity, type VulnScanRun } from "@/lib/vuln-scan";
import { listManagedCertificates, EXPIRY_WARNING_DAYS } from "@/lib/cert-lifecycle";
import { getEgressIpAllowlist, type EgressIpAllowlist } from "@/lib/egress-ips";

export interface VulnPostureSummary {
  reachable: boolean;
  error: string | null;
  /** Null when no scan has ever been run in this cluster -- distinct from
   * a real, confirmed all-zero scan (which has non-null counts and a real
   * scannedAt). */
  scannedAt: string | null;
  /** True once every image's completion index has terminated -- an
   * in-flight scan's counts below are partial, not a final posture. */
  complete: boolean;
  imagesScanned: number;
  severityCounts: Record<Severity, number>;
  totalFindings: number;
}

export interface CertPostureSummary {
  reachable: boolean;
  error: string | null;
  totalCertificates: number;
  /** Count of managed certificates with `daysUntilExpiry < EXPIRY_WARNING_DAYS`
   * (lib/cert-lifecycle.ts), including any already expired. */
  expiringSoonCount: number;
  expiredCount: number;
  /** Days until the single soonest-to-expire managed certificate expires;
   * null only when there are zero managed certificates to report on. */
  minDaysUntilExpiry: number | null;
  expiryWarningThresholdDays: number;
}

export interface EgressIpPostureSummary {
  reachable: boolean;
  error: string | null;
  allowlist: EgressIpAllowlist | null;
}

export interface TrustPageData {
  generatedAt: string;
  uptime: StatusPageData | null;
  uptimeError: string | null;
  vulnPosture: VulnPostureSummary | null;
  certPosture: CertPostureSummary | null;
  /** Static outbound IP ranges this platform delivers webhooks from --
   * see lib/egress-ips.ts for why this is a static, versioned constant
   * rather than a live-polled value. Enterprise buyers' InfoSec teams
   * whitelist these CIDRs in their own inbound firewall to receive this
   * platform's webhook deliveries. */
  egressIpPosture: EgressIpPostureSummary | null;
}

function emptySeverityCounts(): Record<Severity, number> {
  return { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, UNKNOWN: 0 };
}

function summarizeVulnRun(run: VulnScanRun): VulnPostureSummary {
  const severityCounts = emptySeverityCounts();
  let totalFindings = 0;
  for (const image of run.images) {
    for (const severity of Object.keys(severityCounts) as Severity[]) {
      severityCounts[severity] += image.severityCounts[severity] ?? 0;
    }
    totalFindings += image.findings.length;
  }
  return {
    reachable: true,
    error: null,
    scannedAt: run.createdAt,
    complete: run.complete,
    imagesScanned: run.images.length,
    severityCounts,
    totalFindings,
  };
}

async function getVulnPosture(): Promise<VulnPostureSummary> {
  const result = await getLatestVulnScanRun();
  if (!result.ok) {
    return {
      reachable: false,
      error: result.error,
      scannedAt: null,
      complete: false,
      imagesScanned: 0,
      severityCounts: emptySeverityCounts(),
      totalFindings: 0,
    };
  }
  if (!result.data) {
    // Reachable, but genuinely no scan has ever run -- honest "no data",
    // not "reachable: false" (the k8s API itself answered fine).
    return {
      reachable: true,
      error: null,
      scannedAt: null,
      complete: false,
      imagesScanned: 0,
      severityCounts: emptySeverityCounts(),
      totalFindings: 0,
    };
  }
  return summarizeVulnRun(result.data);
}

async function getCertPosture(): Promise<CertPostureSummary> {
  const result = await listManagedCertificates();
  if (!result.ok) {
    return {
      reachable: false,
      error: result.error,
      totalCertificates: 0,
      expiringSoonCount: 0,
      expiredCount: 0,
      minDaysUntilExpiry: null,
      expiryWarningThresholdDays: EXPIRY_WARNING_DAYS,
    };
  }
  const certs = result.data;
  const minDaysUntilExpiry = certs.length > 0
    ? Math.min(...certs.map((c) => c.daysUntilExpiry))
    : null;
  return {
    reachable: true,
    error: null,
    totalCertificates: certs.length,
    expiringSoonCount: certs.filter((c) => c.expiringSoon).length,
    expiredCount: certs.filter((c) => c.expired).length,
    minDaysUntilExpiry,
    expiryWarningThresholdDays: EXPIRY_WARNING_DAYS,
  };
}

/**
 * Aggregates the three real sources described in this module's doc
 * comment into one `TrustPageData` object. Every field with a source that
 * failed to load honestly reports `reachable: false` (uptime's own
 * `StatusPageData.reachable` for that source) rather than a fabricated
 * healthy value -- callers (app/app/trust/page.tsx, app/app/api/trust/
 * route.ts) render each section's own unreachable state independently.
 */
async function getEgressIpPosture(): Promise<EgressIpPostureSummary> {
  const result = await getEgressIpAllowlist();
  if (!result.ok) {
    return { reachable: false, error: result.error, allowlist: null };
  }
  return { reachable: true, error: null, allowlist: result.data };
}

export async function getTrustPageData(): Promise<TrustPageData> {
  const [uptimeResult, vulnPosture, certPosture, egressIpPosture] = await Promise.allSettled([
    getStatusPageData(),
    getVulnPosture(),
    getCertPosture(),
    getEgressIpPosture(),
  ]);

  return {
    generatedAt: new Date().toISOString(),
    uptime: uptimeResult.status === "fulfilled" ? uptimeResult.value : null,
    uptimeError: uptimeResult.status === "rejected" ? String(uptimeResult.reason) : null,
    vulnPosture: vulnPosture.status === "fulfilled" ? vulnPosture.value : null,
    certPosture: certPosture.status === "fulfilled" ? certPosture.value : null,
    egressIpPosture: egressIpPosture.status === "fulfilled" ? egressIpPosture.value : null,
  };
}
