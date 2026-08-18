import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import TagsBrowser from "@/components/TagsBrowser";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Any authenticated role may reach this page and browse -- exactly the
// same "session-gated, no requireRole" convention app/api/search/route.ts
// documents for Global Search, since browsing here is read-only
// aggregation of things the session already has read access to (per-
// category role gating happens inside lib/tags.ts's listResourcesByTag,
// the same CATEGORY_MIN_ROLE-driven fan-out searchPlatform already uses).
// The real mutating boundary is /api/tags's own requireRole call
// (lib/tags.ts's minRoleForTagging) -- this page's rendering never
// bypasses it.
export default async function TagsPage() {
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

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Resource Tagging</h1>
        <p className="mb-8 max-w-2xl text-sm text-muted-foreground">
          Real hyperscaler-PaaS-style Resource Tagging &amp; Organization (AWS Resource Groups
          &amp; Tag Editor / GCP Labels / Azure Tags equivalent): a tag is a real Kubernetes{" "}
          <code>metadata.labels</code> entry (
          <code>platform-console.io/tag-&lt;key&gt;: &lt;value&gt;</code>) on the real object --
          never a separate tags table. Reuses Global Search&apos;s cross-resource-category
          pattern: Services, Projects, Scheduled Jobs, and the platform&apos;s Feature Flags /
          Webhooks ConfigMaps.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && <TagsBrowser />}
      </main>
    </>
  );
}
