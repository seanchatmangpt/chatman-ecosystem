import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ApiKeysPanel from "@/components/ApiKeysPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { listApiKeys } from "@/lib/api-keys";
import { listOrgs } from "@/lib/orgs";

export const dynamic = "force-dynamic";

// Owner-only page, same convention app/org/page.tsx and app/webhooks/page.tsx
// already establish: middleware.ts guarantees a valid session reaches this
// page at all, the requireRole check below is this page's OWN role gate on
// top of that, but the real enforcement boundary for every mutating action
// is /api/api-keys's own server-side requireRole(session, "owner") call,
// not this page's rendering.
export default async function ApiKeysPage() {
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
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">API Keys</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Programmatic access (AWS IAM access keys / GCP service account keys / Stripe API keys
          equivalent): a real, cryptographically random <code>pk_live_...</code> token, stored
          only as a SHA-256 hash in a real k8s <code>Secret</code> (
          <code>platform-console-api-keys</code>, <code>platform-console</code> namespace) --
          never in plaintext, anywhere, past the one response that creates it. Present it as{" "}
          <code>Authorization: Bearer pk_live_...</code> on any <code>/api/*</code> request in
          place of a browser session cookie; the bound role (fixed at creation, at most your own
          current role) flows through the exact same <code>requireRole()</code> gate every
          session already uses. Owner-only: an API key is real, bound authority over this
          console.
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
          <ApiKeysPanelServerBoundary creatorRole={access.role} />
        )}
      </main>
    </>
  );
}

async function ApiKeysPanelServerBoundary({ creatorRole }: { creatorRole: string }) {
  const [result, orgsResult] = await Promise.all([listApiKeys(), listOrgs()]);
  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }
  const orgs = orgsResult.ok ? orgsResult.data.map((o) => ({ id: o.id, name: o.name })) : [];
  return <ApiKeysPanel keys={result.data} creatorRole={creatorRole} orgs={orgs} />;
}
