import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import SessionsPanel from "@/components/SessionsPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { listActiveSessions } from "@/lib/active-sessions";

export const dynamic = "force-dynamic";

// Owner-only page, same convention app/audit/page.tsx and
// app/api-keys/page.tsx already establish: middleware.ts guarantees a
// valid session reaches this page at all (and, as of this pass, that the
// session itself hasn't been revoked in the real registry this page
// reads), the requireRole check below is this page's OWN role gate on top
// of that, but the real enforcement boundary for every mutating action is
// /api/sessions's own server-side requireRole(session, "owner") call, not
// this page's rendering.
export default async function SessionsPage() {
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

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Active Sessions</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real Active Session Management (AWS IAM Identity Center active-session view / GCP
          Console &quot;manage devices &amp; activity&quot; equivalent) -- backed by one real{" "}
          <code>platform_console.active_sessions</code> table on the live demo-project Postgres
          this cluster already runs. This is the one thing this console&apos;s stateless HS256
          session JWTs (<code>lib/session.ts</code>) could never do on their own: every
          authenticated request now checks this registry (<code>middleware.ts</code>), so
          revoking a row here rejects that exact session&apos;s cookie with a real{" "}
          <code>401</code> on its very next request -- before its own unexpired{" "}
          <code>exp</code> claim would have logged it out naturally. Owner-only, enforced
          server-side by <code>lib/authz.ts</code>&apos;s <code>requireRole</code>, same as{" "}
          <code>/audit</code> and <code>/api-keys</code>.
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

        {clusterConfigured && access.ok && <SessionsPanelServerBoundary currentSessionId={session.sessionId ?? null} />}
      </main>
    </>
  );
}

async function SessionsPanelServerBoundary({ currentSessionId }: { currentSessionId: string | null }) {
  const result = await listActiveSessions();
  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }
  return <SessionsPanel initialSessions={result.data} currentSessionId={currentSessionId} />;
}
