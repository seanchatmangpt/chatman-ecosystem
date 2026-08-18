import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import CertificatesPanel from "@/components/CertificatesPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { listManagedCertificates } from "@/lib/cert-lifecycle";

export const dynamic = "force-dynamic";

// Owner-only page: real Certificate Lifecycle tracking (the AWS
// Certificate Manager auto-renewal / GCP-managed-certificate rotation
// equivalent) across every TLS Secret this platform manages
// (lib/cert-lifecycle.ts). middleware.ts already guarantees a valid
// session reaches this page; the check below is this page's OWN role gate
// on top of that -- but the real enforcement boundary for the rotation
// action is /api/certificates's own server-side requireRole(session,
// "owner") call, not this page's rendering, same convention
// app/custom-domains/page.tsx already documents.
export default async function CertificatesPage() {
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Certificates</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real Certificate Lifecycle tracking -- the AWS Certificate Manager auto-renewal / GCP
          managed-certificate rotation equivalent. Every TLS-bearing Secret this platform
          manages in <code>istio-system</code> (<code>platform-console-tls</code>,{" "}
          <code>platform-backups-mtls-credential</code>, and every custom-domain certificate
          registered via <code>/custom-domains</code>) is scanned live and its real{" "}
          <code>notAfter</code> field parsed with Node&apos;s own{" "}
          <code>crypto.X509Certificate</code> -- no side database, no simulated expiry. Custom
          -domain certificates can be rotated in place: a fresh cert is generated for the same
          hostname and written into the SAME Secret name, so Istio&apos;s SDS layer hot-reloads
          it with no Gateway/VirtualService churn and no traffic interruption. Rotation is
          owner-only -- enforced server-side by <code>lib/authz.ts</code>&apos;s{" "}
          <code>requireRole</code>, not just hidden client-side.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && !access.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{access.role}</code>) does not meet the required minimum role (
              <code>owner</code>) for this page. Ask an existing owner to promote your account (
              <code>{currentIdentifier}</code>) via the <code>/org</code> page.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && <CertificatesPanelServerBoundary />}
      </main>
    </>
  );
}

async function CertificatesPanelServerBoundary() {
  const result = await listManagedCertificates();

  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }

  return <CertificatesPanel initialCertificates={result.data} />;
}
