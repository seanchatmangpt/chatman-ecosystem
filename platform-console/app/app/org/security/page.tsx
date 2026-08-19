import { cookies, headers } from "next/headers";
import Nav from "@/components/Nav";
import IpAllowlistPanel from "@/components/IpAllowlistPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { getIpAllowlist, IP_ALLOWLIST_NAMESPACE } from "@/lib/ip-allowlist";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Owner-only settings page for the real org-level IP allowlist / network
// access policy (lib/ip-allowlist.ts, enforced in middleware.ts). Same
// "server component gates rendering, the route is the real boundary"
// convention app/org/page.tsx already establishes for role management: a
// non-owner landing here directly sees a real 403 message, not the
// editing UI, and any PUT they attempted against
// /api/orgs/[id]/ip-allowlist would be rejected there regardless.
//
// Operates against IP_ALLOWLIST_NAMESPACE ("platform-console"), the same
// fixed namespace both lib/authz.ts's RBAC and middleware.ts's own
// enforcement already key off -- this deployment's one actual tenant (see
// lib/ip-allowlist.ts and the API route's own header comments for why).
export default async function OrgSecurityPage() {
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

  // Same real x-forwarded-for/x-real-ip resolution lib/request-meta.ts's
  // clientIpFrom uses on the actual NextRequest in middleware.ts/the API
  // route -- this server component only has the headers() API available
  // (no NextRequest here), so it re-derives the identical value from the
  // same two headers directly, rather than fabricating a client-only
  // guess.
  const headerStore = await headers();
  const forwardedFor = headerStore.get("x-forwarded-for");
  const yourIp = forwardedFor
    ? forwardedFor.split(",")[0]?.trim() ?? null
    : headerStore.get("x-real-ip");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Org network access policy</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real org-level IP allowlist (SOC2 / vendor-review checklist item: only corporate
          VPN/office CIDR ranges may reach the admin console). Backed by one real k8s{" "}
          <code>ConfigMap</code> (<code>platform-console-ip-allowlist</code>,{" "}
          <code>platform-console</code> namespace) and enforced in <code>middleware.ts</code> on
          every request, after the session resolves and before any route handler runs. Fail-open
          by default: an org with no CIDRs configured is unrestricted, so shipping this control
          never retroactively locks anyone out.
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
              <code>owner</code>) to manage this org&apos;s IP allowlist.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && (
          <SecurityPanelServerBoundary yourIp={yourIp} />
        )}
      </main>
    </>
  );
}

async function SecurityPanelServerBoundary({ yourIp }: { yourIp: string | null }) {
  const result = await getIpAllowlist(IP_ALLOWLIST_NAMESPACE);
  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read allowlist: {result.error}
      </p>
    );
  }
  return (
    <IpAllowlistPanel
      orgId={IP_ALLOWLIST_NAMESPACE}
      namespace={IP_ALLOWLIST_NAMESPACE}
      cidrs={result.data}
      yourIp={yourIp}
    />
  );
}
