import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import CustomDomainsPanel from "@/components/CustomDomainsPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials, listAllServices } from "@/lib/k8s";
import { listCustomDomains } from "@/lib/custom-domains";

export const dynamic = "force-dynamic";

// Owner-only page: real Custom Domain self-service (AWS Certificate
// Manager + Route53 custom-domain binding / GCP Cloud Run custom-domain
// equivalent) -- generates a real TLS cert and binds a new PUBLIC
// hostname to one of the platform's own real Services through a real
// Istio Gateway/VirtualService pair (lib/custom-domains.ts). middleware.ts
// already guarantees a valid session reaches this page; the check below
// is this page's OWN role gate on top of that -- but the real enforcement
// boundary for every mutating action is /api/custom-domains's own
// server-side requireRole(session, "owner") call, not this page's
// rendering, same convention app/deployments/canary/page.tsx already
// documents.
export default async function CustomDomainsPage() {
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Custom Domains</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real Custom Domain self-service -- the AWS Certificate Manager + Route53 custom-domain
          binding / GCP Cloud Run custom-domain equivalent. Registering a hostname generates a
          real, freshly-issued X.509 certificate for that exact hostname (SAN independently
          re-verified before it is ever stored), stores it as a real{" "}
          <code>kubernetes.io/tls</code> Secret in <code>istio-system</code>, and creates a real{" "}
          <code>networking.istio.io/v1</code> <code>Gateway</code> + <code>VirtualService</code>{" "}
          pair binding that hostname to one of the platform&apos;s own real Services -- no
          hand-edited Istio YAML per domain. Every mutating action here is owner-only -- enforced
          server-side by <code>lib/authz.ts</code>&apos;s <code>requireRole</code>, not just
          hidden client-side.
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

        {clusterConfigured && access.ok && <CustomDomainsPanelServerBoundary />}
      </main>
    </>
  );
}

async function CustomDomainsPanelServerBoundary() {
  const [servicesResult, bindingsResult] = await Promise.all([
    listAllServices(),
    listCustomDomains(),
  ]);

  if (!servicesResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {servicesResult.error}
      </p>
    );
  }
  if (!bindingsResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {bindingsResult.error}
      </p>
    );
  }

  return (
    <CustomDomainsPanel services={servicesResult.data} initialBindings={bindingsResult.data} />
  );
}
