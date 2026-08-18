import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import WebhooksPanel from "@/components/WebhooksPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { listWebhookSubscriptions } from "@/lib/webhooks";

export const dynamic = "force-dynamic";

// Owner-only page, same convention app/org/page.tsx already establishes:
// middleware.ts guarantees a valid session reaches this page at all, the
// requireRole check below is this page's OWN role gate on top of that,
// but the real enforcement boundary for every mutating action is
// /api/webhooks's own server-side requireRole(session, "owner") call,
// not this page's rendering.
export default async function WebhooksPage() {
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Outbound Webhooks</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Event Notifications (AWS EventBridge / GCP Eventarc / Azure Event Grid equivalent):
          register a URL to receive a real HTTP POST -- with a real HMAC-SHA256 signature -- the
          moment a real platform event happens: <code>project.created</code> (fires from the real
          Create Project success path), <code>backup.completed</code> (fires when a real backup{" "}
          <code>Job</code> reaches <code>Complete</code>), or <code>alert.firing</code> (fires when
          a new Alertmanager alert appears). Owner-only: a subscriber URL is a real exfiltration
          vector for every payload delivered here, so this page and its API are gated the same way{" "}
          <code>/org</code> is.
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

        {clusterConfigured && access.ok && <WebhooksPanelServerBoundary />}
      </main>
    </>
  );
}

async function WebhooksPanelServerBoundary() {
  const result = await listWebhookSubscriptions();
  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }
  return <WebhooksPanel subscriptions={result.data} />;
}
