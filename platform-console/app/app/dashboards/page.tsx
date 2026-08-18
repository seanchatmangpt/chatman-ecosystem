import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import DashboardsPanel from "@/components/DashboardsPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { hasClusterCredentials } from "@/lib/k8s";
import { getRoleFor, roleIdentifierFor, ROLES, type Role } from "@/lib/authz";
import {
  executeWidget,
  listWidgets,
  minRoleForCreating,
  minRoleForViewing,
  WIDGET_TYPES,
  type Widget,
} from "@/lib/dashboards";

export const dynamic = "force-dynamic";

function roleMeets(role: Role, minimum: Role): boolean {
  return ROLES.indexOf(role) >= ROLES.indexOf(minimum);
}

// Session-gated only, no whole-page requireRole -- same convention
// app/tags/page.tsx documents: browsing here is a personal collection of
// saved queries, each of which is only ever executed if the viewing
// session's role already meets that widget TYPE's own access level
// (lib/dashboards.ts's minRoleForViewing, matching /observability and
// /audit exactly). The real mutating/executing boundaries are
// /api/dashboards's own per-action checks -- this page's rendering never
// bypasses them, it just performs the identical checks server-side so the
// initial render already reflects them.
export default async function DashboardsPage() {
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

  const identifier = roleIdentifierFor(session);
  const role = await getRoleFor(session);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Custom Dashboards</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          AWS CloudWatch custom dashboards / GCP Monitoring custom dashboards equivalent: save a
          real query as a named widget and arrange several into your own personal dashboard.
          Every widget is re-run against the real backend on every load -- a PromQL query against
          the same allowlisted <code>/observability</code> Prometheus proxy, or a filtered lookup
          against the same durable <code>/audit</code> log -- never a cached or frozen snapshot.
          promql widgets need whatever <code>/observability</code> already requires (any
          authenticated session); audit-query widgets need whatever <code>/audit</code> already
          requires (<code>owner</code>) -- a widget is just a saved lens onto data you could
          already query directly.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && (
          <DashboardsPanelServerBoundary identifier={identifier} role={role} />
        )}
      </main>
    </>
  );
}

async function DashboardsPanelServerBoundary({ identifier, role }: { identifier: string; role: Role }) {
  const listed = await listWidgets(identifier);
  if (!listed.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {listed.error}
      </p>
    );
  }

  const widgets = await Promise.all(
    listed.data.map(async (widget: Widget) => {
      if (!roleMeets(role, minRoleForViewing(widget.type))) {
        return {
          ...widget,
          result: {
            ok: false as const,
            error: `role '${role}' does not meet the required minimum role '${minRoleForViewing(widget.type)}' to view a '${widget.type}' widget`,
          },
        };
      }
      return { ...widget, result: await executeWidget(widget) };
    }),
  );

  const creatableTypes = WIDGET_TYPES.filter((t) => roleMeets(role, minRoleForCreating(t)));

  return <DashboardsPanel initialWidgets={widgets} creatableTypes={creatableTypes} />;
}
