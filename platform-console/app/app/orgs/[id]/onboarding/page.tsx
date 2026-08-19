import Link from "next/link";
import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import { runOnboardingChecks, type OnboardingStep } from "@/lib/onboarding";

export const dynamic = "force-dynamic";

// Real, per-org "time to first value" onboarding checklist -- the
// auditable artifact a CSM shows an exec sponsor mid-pilot, and sales/CS
// activation-rate dashboards can key off, without trusting a
// self-reported checkbox. Every row below is computed fresh on every
// render by lib/onboarding.ts's runOnboardingChecks straight off this
// org's real platform state; this page renders it and, for the steps
// still incomplete, links straight into the existing module that
// completes them (same "the real API/page decides, not this summary"
// discipline app/quickstart/page.tsx's header comment documents).

// Where each step's real underlying module already lives in this
// console, so an incomplete row can link straight to the page that
// completes it instead of just naming the gap.
const STEP_LINKS: Record<string, (orgId: string) => string> = {
  "api-key-created": (orgId) => `/orgs/${orgId}/api-keys`,
  "first-project-ready": () => `/projects`,
  "first-backup-run": (orgId) => `/orgs/${orgId}/backups`,
  "member-invited": (orgId) => `/orgs/${orgId}/invite`,
  "custom-role-assigned": (orgId) => `/orgs/${orgId}/roles`,
  "sla-or-region-set": (orgId) => `/orgs/${orgId}/sla`,
};

export default async function OrgOnboardingPage({
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
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Onboarding checklist</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real progress for <span className="text-gray-200">{org.name}</span>, computed straight
          off this org&apos;s live platform state (API keys, projects, backups, membership,
          roles, SLA/region) -- never a self-reported checkbox.
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
              Your role (<code>{access.role}</code>) does not meet the required minimum role
              (<code>viewer</code>) to view this org&apos;s onboarding progress.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && <OnboardingSection orgId={id} />}
      </main>
    </>
  );
}

async function OnboardingSection({ orgId }: { orgId: string }) {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok || !orgResult.data) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        {orgResult.ok ? "org not found" : orgResult.error}
      </p>
    );
  }

  const { steps, percentComplete } = await runOnboardingChecks(orgResult.data);

  return (
    <div>
      <div className="mb-6">
        <div className="mb-2 flex items-baseline justify-between">
          <span className="text-sm text-gray-400">Progress</span>
          <span className="text-sm font-medium text-white">{percentComplete}% complete</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all"
            style={{ width: `${percentComplete}%` }}
          />
        </div>
      </div>

      <ul className="divide-y divide-gray-800 rounded-md border border-gray-800">
        {steps.map((step) => (
          <StepRow key={step.id} step={step} orgId={orgId} />
        ))}
      </ul>
    </div>
  );
}

function StepRow({ step, orgId }: { step: OnboardingStep; orgId: string }) {
  const href = STEP_LINKS[step.id]?.(orgId);

  return (
    <li className="flex items-center justify-between gap-4 px-4 py-3">
      <div className="flex items-center gap-3">
        <span
          className={`flex h-5 w-5 flex-none items-center justify-center rounded-full text-xs ${
            step.done
              ? "bg-emerald-500/20 text-emerald-400"
              : "border border-gray-700 text-transparent"
          }`}
          aria-hidden
        >
          {step.done ? "✓" : ""}
        </span>
        <span className={step.done ? "text-sm text-gray-300 line-through" : "text-sm text-white"}>
          {step.label}
        </span>
      </div>
      {!step.done && href && (
        <Link href={href} className="flex-none text-xs text-blue-400 hover:text-blue-300">
          Go to step &rarr;
        </Link>
      )}
    </li>
  );
}
