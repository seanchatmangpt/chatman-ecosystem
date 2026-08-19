import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ApprovalsPanel from "@/components/ApprovalsPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { listApprovals } from "@/lib/approval-workflow";

export const dynamic = "force-dynamic";

// Real maker-checker approvals dashboard -- the human-facing side of
// lib/approval-workflow.ts's two-person-integrity control. Owner-only,
// same convention app/budget-alerts/page.tsx and app/org/page.tsx already
// establish: the real enforcement boundary for every decision is
// /api/approvals/[id]'s own server-side requireRole(session, "owner") +
// requester != approver check, not this page's rendering -- this page's
// own requireRole is a second, redundant fail-closed layer, not the
// authority.
export default async function ApprovalsPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const clusterConfigured = hasClusterCredentials();

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-4xl px-6 py-10">
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
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Approvals</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Role-based, multi-party (maker-checker) approval workflow for high-risk provisioning
          actions -- <code>org.delete</code>, <code>quota.override</code>, and{" "}
          <code>tier.downgrade</code> each require a real, distinct second owner-role approver
          before the underlying route will perform the action, enforced server-side (not just in
          this UI) by <code>lib/approval-workflow.ts</code>. A guarded route returns{" "}
          <code>202 Accepted</code> with a pending request instead of acting; retrying the
          original request only succeeds once a status here reads <code>approved</code> within
          the last 24 hours. The requester can never approve their own request.
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
              <code>owner</code>) for this page.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && (
          <ApprovalsPanelServerBoundary currentIdentifier={currentIdentifier} />
        )}
      </main>
    </>
  );
}

async function ApprovalsPanelServerBoundary({
  currentIdentifier,
}: {
  currentIdentifier: string;
}) {
  const result = await listApprovals();
  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }
  return <ApprovalsPanel approvals={result.data} currentIdentifier={currentIdentifier} />;
}
