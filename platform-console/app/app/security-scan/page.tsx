import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import VulnScanPanel from "@/components/VulnScanPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { IMAGES_TO_SCAN } from "@/lib/vuln-scan";

export const dynamic = "force-dynamic";

// Owner-only page: real Container Vulnerability Scanning (AWS ECR image
// scanning / GCP Artifact Registry vulnerability scanning / Azure Defender
// for Containers equivalent). Triggers a real k8s Indexed Job running the
// real, open-source `trivy` scanner against the platform's own real,
// currently-built images -- never a fabricated finding list -- plus one
// deliberate positive-control public image (an old, real, EOL image with
// well-known CVEs) proving the scan mechanism itself surfaces real findings
// when they exist. Same "owner" floor as Container Exec and Canary Deploy:
// this triggers a real workload with a real hostPath mount onto the
// cluster node's own container-runtime socket.
export default async function SecurityScanPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const clusterConfigured = hasClusterCredentials();

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const access = await requireRole(session, "owner");
  const currentIdentifier = roleIdentifierFor(session);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Container Vulnerability Scanning</h1>
        <p className="mb-8 max-w-3xl text-sm text-gray-400">
          Real Container Vulnerability Scanning (the AWS ECR image scanning / GCP Artifact
          Registry vulnerability scanning / Azure Defender for Containers equivalent) -- runs the
          real, open-source <code>trivy</code> scanner (Aqua Security) against a real,
          up-to-date vulnerability database (<code>mirror.gcr.io/aquasec/trivy-db</code>) inside a
          real Kubernetes Job, one pod per image, with a real <code>hostPath</code> mount onto this
          node&apos;s own containerd socket for this platform&apos;s own local-only images. Scans{" "}
          {IMAGES_TO_SCAN.filter((t) => !t.isControl).length} of the platform&apos;s own built
          images plus one deliberate positive-control public image (
          <code>{IMAGES_TO_SCAN.find((t) => t.isControl)?.ref}</code>, a real, old, EOL image with
          well-known CVEs) to prove the scan mechanism actually surfaces real findings when they
          exist, not only that the platform&apos;s own slim images happen to be clean.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page can only
            trigger a real scan when running as the platform-console pod.
          </div>
        )}

        {!access.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{access.role}</code>) does not meet the required minimum role (
              <code>owner</code>) for this page. Ask an existing owner to promote your account (
              <code>{currentIdentifier}</code>) via the <code>/org</code> page.
            </p>
          </div>
        )}

        {access.ok && (
          <VulnScanPanel
            images={IMAGES_TO_SCAN.map((t) => ({
              id: t.id,
              label: t.label,
              ref: t.ref,
              source: t.source,
              isControl: t.isControl,
            }))}
          />
        )}
      </main>
    </>
  );
}
