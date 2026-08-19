import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import CustomRolesPanel from "@/components/CustomRolesPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { listCustomRoles, listGrants, PERMISSIONS } from "@/lib/custom-roles";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

const DEFAULT_ORG_ID = "platform-console";

// Owner-only page: custom RBAC role definitions and fine-grained
// permission grants, additive to the fixed viewer/member/owner ladder
// app/org/page.tsx already manages. middleware.ts already guarantees a
// valid session reaches this page; the check below is this page's OWN
// role gate on top of that -- the real enforcement boundary for every
// mutating action is /api/roles's own server-side requireRole(session,
// "owner") call, not this page's rendering.
export default async function OrgCustomRolesPage() {
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
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Custom RBAC roles</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Fine-grained, least-privilege permission grants -- additive on top of, never a
          replacement for, the built-in <code>viewer</code> &lt; <code>member</code> &lt;{" "}
          <code>owner</code> ladder (see <code>/org</code>). Backed by one real k8s{" "}
          <code>ConfigMap</code> (<code>platform-console-custom-roles</code>,{" "}
          <code>platform-console</code> namespace). Define a role (e.g. &quot;billing-only
          admin&quot;, &quot;read-only auditor with DSAR export rights&quot;, &quot;on-call
          engineer who can run castle verbs but not change tiers&quot;) as a set of permissions,
          then assign it to any identifier. This page, and every mutating action it drives, is
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
              <code>{currentIdentifier}</code>) via <code>/org</code>.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && (
          <CustomRolesPanelServerBoundary currentIdentifier={currentIdentifier} />
        )}
      </main>
    </>
  );
}

async function CustomRolesPanelServerBoundary({
  currentIdentifier,
}: {
  currentIdentifier: string;
}) {
  const [rolesResult, grantsResult] = await Promise.all([
    listCustomRoles(DEFAULT_ORG_ID),
    listGrants(),
  ]);

  if (!rolesResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {rolesResult.error}
      </p>
    );
  }
  if (!grantsResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {grantsResult.error}
      </p>
    );
  }

  return (
    <CustomRolesPanel
      roles={rolesResult.data}
      grants={grantsResult.data}
      permissions={PERMISSIONS}
      currentIdentifier={currentIdentifier}
    />
  );
}
