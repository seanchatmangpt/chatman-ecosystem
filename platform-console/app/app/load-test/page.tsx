import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import LoadTestPanel from "@/components/LoadTestPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { LOAD_TEST_TARGETS } from "@/lib/load-test";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Member+-gated page: real Load Testing / performance benchmarking
// self-service (AWS Distributed Load Testing solution / GCP's own
// load-testing guidance tooling equivalent) -- see lib/load-test.ts. This
// page's own gate mirrors the real enforcement boundary, which is
// /api/load-test's own server-side requireRole(session, "member") call, not
// this page's rendering: running a real concurrent-request benchmark
// against a live internal service is a genuinely consequential action, same
// class as /scheduled-jobs or /secrets.
export default async function LoadTestPage() {
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

  const access = await requireRole(session, "member");
  const currentIdentifier = roleIdentifierFor(session);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Load Testing</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real Load Testing / performance benchmarking self-service (the AWS Distributed Load
          Testing solution / GCP load-testing guidance tooling equivalent) -- fires real
          concurrent HTTP requests (Node <code>fetch</code>, a <code>Promise.all</code>-based
          worker pool, no new dependency) against one of this platform&apos;s own status
          services and measures real p50/p95/p99 latency and real success/error counts from the
          actual responses received. Scoped to a fixed allowlist of this platform&apos;s own
          internal Service DNS names -- never an arbitrary user-supplied URL.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page still runs
            real HTTP load, but the target services (cluster-internal DNS names) are only
            reachable when running as the platform-console pod.
          </div>
        )}

        {!access.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{access.role}</code>) does not meet the required minimum role (
              <code>member</code>) for this page. Ask an existing owner to promote your account (
              <code>{currentIdentifier}</code>) via the <code>/org</code> page.
            </p>
          </div>
        )}

        {access.ok && (
          <LoadTestPanel targets={LOAD_TEST_TARGETS.map((t) => ({ id: t.id, label: t.label }))} />
        )}
      </main>
    </>
  );
}
