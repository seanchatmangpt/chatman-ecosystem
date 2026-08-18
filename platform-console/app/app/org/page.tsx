import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import OrgRolesPanel from "@/components/OrgRolesPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { getOrgRoleAssignments, requireRole, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Owner-only page (requirement 4): lists the real role assignments from
// the platform-console-org-roles ConfigMap and lets an owner change one.
// middleware.ts already guarantees a valid session reaches this page (no
// session -> redirected to /login before this ever renders); the check
// below is this page's OWN role gate on top of that -- but the real
// enforcement boundary for every mutating action is /api/org/roles's own
// server-side requireRole(session, "owner") call, not this page's
// rendering. A non-owner landing here directly (e.g. by URL) sees a real
// 403 message, not the role-management UI, and any POST they attempted
// against /api/org/roles would be rejected there regardless.
export default async function OrgPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const clusterConfigured = hasClusterCredentials();

  if (!session) {
    // middleware.ts should have already redirected an unauthenticated
    // request to /login before this ever renders; this is a real
    // fail-closed fallback, not reachable in normal operation.
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Organization roles</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real application-level RBAC (AWS IAM Identity Center permission sets / GCP Org Policy /
          Azure AD role assignments equivalent), layered on top of -- not replacing -- the
          console&apos;s own k8s ServiceAccount RBAC. Backed by one real k8s{" "}
          <code>ConfigMap</code> (<code>platform-console-org-roles</code>,{" "}
          <code>platform-console</code> namespace): identifier (email for gotrue users,{" "}
          <code>admin</code> for local-admin) maps to a role. Roles, lowest to highest:{" "}
          <code>viewer</code> &lt; <code>member</code> &lt; <code>owner</code>. This page, and
          every mutating action it drives, is owner-only -- enforced server-side by{" "}
          <code>lib/authz.ts</code>&apos;s <code>requireRole</code>, not just hidden client-side.
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
              <code>{currentIdentifier}</code>) via this same page.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && (
          <OrgRolesPanelServerBoundary currentIdentifier={currentIdentifier} />
        )}
      </main>
    </>
  );
}

async function OrgRolesPanelServerBoundary({ currentIdentifier }: { currentIdentifier: string }) {
  const result = await getOrgRoleAssignments();

  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }

  return <OrgRolesPanel assignments={result.data} currentIdentifier={currentIdentifier} />;
}
