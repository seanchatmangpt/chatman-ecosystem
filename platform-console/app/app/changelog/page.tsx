import { cookies } from "next/headers";
import Link from "next/link";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg, listOrgs } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import { getOrgProjectTier } from "@/lib/orgs";
import { tierAtLeast, type ProjectTier } from "@/lib/tiers";
import { CHANGELOG_ENTRIES } from "@/lib/changelog";

export const dynamic = "force-dynamic";

// Real in-app changelog / release-notes feed: turns the existing,
// already-enforced TIER_GATED_FLAGS / setOrgRegion / TIER_RESOURCE_QUOTAS
// tier ceilings (lib/tiers.ts, lib/orgs.ts) into a visible self-serve
// upsell surface, so a Fortune-5 buyer capped on `pro` sees a concrete,
// always-visible "here's what enterprise unlocks" reason to ask their AE
// -- instead of a tier gap that only a human noticing a 403 would ever
// surface to Sales. Same underlying computation as
// GET /api/orgs/[id]/changelog (tierAtLeast(org tier, entry.minimumTier))
// -- this page renders it server-side rather than round-tripping to that
// route from the client.
//
// Org-scoped (an org's own tier decides what's locked), but reached at a
// single top-level /changelog path rather than /orgs/[id]/changelog:
// `?org=<id>` selects which org's tier to render against, defaulting to
// the first org this session has at least viewer access to -- mirroring
// how /billing (app/billing/page.tsx) renders across every platform
// namespace without requiring an org id in its own URL.

const TIER_LABEL: Record<ProjectTier, string> = {
  starter: "Starter",
  pro: "Pro",
  enterprise: "Enterprise",
};

export default async function ChangelogPage({
  searchParams,
}: {
  searchParams: Promise<{ org?: string }>;
}) {
  const { org: requestedOrgId } = await searchParams;
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

  if (!clusterConfigured) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        </main>
      </>
    );
  }

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {orgsResult.error}
          </p>
        </main>
      </>
    );
  }

  const orgs = orgsResult.data;
  const orgId = requestedOrgId ?? orgs[0]?.id;

  if (!orgId) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <h1 className="mb-2 text-2xl font-semibold text-white">Changelog</h1>
          <p className="text-sm text-gray-400">No orgs exist yet.</p>
        </main>
      </>
    );
  }

  const orgResult = await getOrg(orgId);
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
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <div className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{access.role}</code>) does not meet the required minimum role (
              <code>viewer</code>) to view this org&apos;s changelog.
            </p>
          </div>
        </main>
      </>
    );
  }

  const tierResult = await getOrgProjectTier(org.namespace);
  if (!tierResult.ok) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            failed to read org tier: {tierResult.error}
          </p>
        </main>
      </>
    );
  }
  const tier = tierResult.data;

  const entries = CHANGELOG_ENTRIES.map((entry) => ({
    ...entry,
    unlocked: tierAtLeast(tier, entry.minimumTier),
  }));

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-2 flex items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold text-white">Changelog</h1>
          {orgs.length > 1 && (
            <div className="flex flex-wrap gap-2 text-xs">
              {orgs.map((o) => (
                <Link
                  key={o.id}
                  href={`/changelog?org=${encodeURIComponent(o.id)}`}
                  className={`rounded-md border px-2 py-1 ${
                    o.id === org.id
                      ? "border-white/40 text-white"
                      : "border-white/10 text-gray-400 hover:text-white"
                  }`}
                >
                  {o.name}
                </Link>
              ))}
            </div>
          )}
        </div>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          What&apos;s new for <span className="text-white">{org.name}</span>, currently on the{" "}
          <span className="text-white">{TIER_LABEL[tier]}</span> Project tier. Entries this org
          hasn&apos;t unlocked yet stay visible below with a &quot;requires&quot; badge, rather
          than being hidden -- ask your account executive to upgrade to unlock them.
        </p>

        <ol className="space-y-4">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className={`card p-5 ${entry.unlocked ? "" : "border-amber-900/60 bg-amber-950/10"}`}
            >
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="text-xs text-gray-500">{entry.date}</span>
                {entry.unlocked ? (
                  <span className="rounded-full border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 text-xs text-emerald-300">
                    available on your plan
                  </span>
                ) : (
                  <span className="rounded-full border border-amber-800 bg-amber-950/60 px-2 py-0.5 text-xs font-medium text-amber-300">
                    requires {TIER_LABEL[entry.minimumTier]}
                  </span>
                )}
              </div>
              <h2 className="text-base font-medium text-white">{entry.title}</h2>
              <p className="mt-1 text-sm text-gray-400">{entry.body}</p>
            </li>
          ))}
        </ol>
      </main>
    </>
  );
}
