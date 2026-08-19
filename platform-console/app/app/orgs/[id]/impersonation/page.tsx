import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import { listImpersonationSessionsForOrg } from "@/lib/impersonation";

export const dynamic = "force-dynamic";

// Real customer-facing "support access to your account" trust page --
// the disclosure half of the Admin Impersonation control described in
// lib/impersonation.ts's module doc: every session a platform-console
// admin has opened against THIS org, who opened it, why, when, and for
// how long. Server component gates rendering the same way
// app/org/compliance/page.tsx already does: a non-member sees a real 403
// message, not the table; the underlying data read (GET
// /api/orgs/[id]/impersonation-log) is re-checked by its own route
// handler regardless of what this page renders.

export default async function OrgImpersonationLogPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
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

  const orgResult = await getOrg(id);
  if (!orgResult.ok || !orgResult.data) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {orgResult.ok ? "org not found" : orgResult.error}
          </p>
        </main>
      </>
    );
  }

  const viewerAccess = await requireRoleIn(session, orgResult.data.namespace, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Support access log</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Every time platform-console staff opened a time-boxed (30-minute) support session
          against this org is recorded here -- who, when, why, and how long -- as it appears in
          the platform&apos;s own immutable, hash-chained audit trail.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only returns
            real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && !viewerAccess.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{viewerAccess.role}</code>) does not meet the required minimum role
              (<code>viewer</code>) to view this org&apos;s support access log.
            </p>
          </div>
        )}

        {clusterConfigured && viewerAccess.ok && (
          <ImpersonationLogTable orgId={id} />
        )}
      </main>
    </>
  );
}

async function ImpersonationLogTable({ orgId }: { orgId: string }) {
  const result = await listImpersonationSessionsForOrg(orgId);

  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read support access log: {result.error}
      </p>
    );
  }

  if (result.data.length === 0) {
    return (
      <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-400">
        No support sessions have ever been opened against this org.
      </p>
    );
  }

  const now = Date.now();

  return (
    <div className="overflow-x-auto rounded-md border border-gray-800">
      <table className="min-w-full divide-y divide-gray-800 text-sm">
        <thead className="bg-gray-900/60 text-left text-gray-400">
          <tr>
            <th className="px-4 py-2 font-medium">Admin</th>
            <th className="px-4 py-2 font-medium">Reason</th>
            <th className="px-4 py-2 font-medium">Started</th>
            <th className="px-4 py-2 font-medium">Ended</th>
            <th className="px-4 py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {result.data.map((s) => {
            const active = !s.endedAt && new Date(s.expiresAt).getTime() > now;
            return (
              <tr key={s.id} className="text-gray-200">
                <td className="px-4 py-2 font-mono text-xs">{s.adminUserId}</td>
                <td className="px-4 py-2">{s.reason}</td>
                <td className="px-4 py-2 text-gray-400">{new Date(s.startedAt).toLocaleString()}</td>
                <td className="px-4 py-2 text-gray-400">
                  {s.endedAt ? new Date(s.endedAt).toLocaleString() : "--"}
                </td>
                <td className="px-4 py-2">
                  {active ? (
                    <span className="rounded-full bg-amber-950/60 px-2 py-0.5 text-xs text-amber-300">
                      active
                    </span>
                  ) : (
                    <span className="rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-400">
                      ended ({s.endedReason ?? "expired"})
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
