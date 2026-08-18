import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ExecPanel from "@/components/ExecPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { EXEC_NAMESPACES } from "@/lib/container-exec";

export const dynamic = "force-dynamic";

// Owner-only page: real Container Exec (AWS Systems Manager Session
// Manager / GCP Cloud Shell / Azure Cloud Shell "run a command in a
// running instance/pod" equivalent) over the k8s exec subresource's real
// WebSocket upgrade. This is real command execution -- the most sensitive
// capability in the whole console -- so it gets the same "owner" floor as
// Canary Deploy and Audit Log, enforced independently by THREE layers:
// this page's own gate (below), GET /api/exec's own requireRole, and
// server.js's `/ws/exec` upgrade handler's own role check (the one that
// actually matters, since that is the code path that opens a real k8s
// connection).
export default async function ExecPage() {
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Container Exec</h1>
        <p className="mb-8 max-w-3xl text-sm text-gray-400">
          Real Container Exec / browser-based shell access -- the AWS Systems Manager Session
          Manager / GCP Cloud Shell / Azure Cloud Shell equivalent -- runs one fixed, allowlisted
          command inside a real running pod, over the k8s API&apos;s real exec subresource (
          <code>GET /api/v1/namespaces/&#123;ns&#125;/pods/&#123;pod&#125;/exec</code>, upgraded to
          a real WebSocket -- the same mechanism <code>kubectl exec</code> itself uses). Every
          real stdout/stderr byte streams back through <code>/ws/exec</code> (
          <code>server.js</code>&apos;s relay) as it arrives. There is no free-text command field
          anywhere on this page or in its API -- the command dropdown only ever lists the
          server-side allowlist (<code>lib/container-exec.ts</code>&apos;s{" "}
          <code>ALLOWED_EXEC_COMMANDS</code>), and an unrecognized command id is rejected before
          any connection to the k8s API is attempted.
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

        {clusterConfigured && access.ok && <ExecPanel namespaces={[...EXEC_NAMESPACES]} />}
      </main>
    </>
  );
}
