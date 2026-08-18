import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import BudgetAlertsPanel from "@/components/BudgetAlertsPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { BUDGET_WINDOW_LABEL, listBudgetThresholds, listBudgetUsages } from "@/lib/budget-alerts";

export const dynamic = "force-dynamic";

// Same platform-namespace roster /api/budget-alerts, /api/billing, and
// app/billing/page.tsx already use.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

// Owner-only page, same convention app/webhooks/page.tsx and app/org/page.tsx
// already establish: middleware.ts guarantees a valid session reaches this
// page at all, the requireRole check below is this page's OWN role gate on
// top of that, but the real enforcement boundary for every mutating action
// is /api/budget-alerts's own server-side requireRole(session, "owner")
// call, not this page's rendering. Budget thresholds are gated at the same
// level webhooks are: a real financial-adjacent setting (it governs when
// this console fires a real webhook about namespace spend), even though no
// payment method or processor is ever involved anywhere in this platform.
export default async function BudgetAlertsPage() {
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Budget Alerts</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          AWS Budgets / GCP Billing Budgets equivalent: set a real per-namespace threshold on
          either <code>cpu-core-hours</code> or illustrative <code>cost-usd</code> (the same real
          Prometheus-derived figures <code>/usage</code> and <code>/billing</code> already
          compute, over the same trailing {BUDGET_WINDOW_LABEL} window) and get a real,
          HMAC-SHA256-signed <code>budget.threshold_crossed</code> webhook the moment real
          measured usage crosses it -- delivered through the exact same webhook mechanism as{" "}
          <code>project.created</code>/<code>backup.completed</code>/<code>alert.firing</code>,
          fired from the same 10-second poller (<code>lib/webhook-poller.ts</code>), deduped by a
          real ConfigMap-persisted &quot;already alerted&quot; marker so a sustained overage
          fires once, not once per poll. Owner-only: same boundary as <code>/webhooks</code> and{" "}
          <code>/org</code> -- a budget threshold is a real financial-adjacent setting.
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

        {clusterConfigured && access.ok && <BudgetAlertsPanelServerBoundary />}
      </main>
    </>
  );
}

async function BudgetAlertsPanelServerBoundary() {
  const [thresholdsResult, usagesResult] = await Promise.all([
    listBudgetThresholds(),
    listBudgetUsages(),
  ]);

  if (!thresholdsResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {thresholdsResult.error}
      </p>
    );
  }
  if (!usagesResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {usagesResult.error}
      </p>
    );
  }

  return (
    <BudgetAlertsPanel
      namespaces={PLATFORM_NAMESPACES}
      thresholds={thresholdsResult.data}
      usages={usagesResult.data}
      windowLabel={BUDGET_WINDOW_LABEL}
    />
  );
}
