import Nav from "@/components/Nav";
import {
  hasClusterCredentials,
  listNetworkPolicies,
  listRoleBindings,
  listRoles,
  type IamNetworkPolicy,
  type RbacRole,
} from "@/lib/k8s";

export const dynamic = "force-dynamic";

function groupByNamespace<T extends { namespace: string }>(items: T[]): Map<string, T[]> {
  const map = new Map<string, T[]>();
  for (const item of items) {
    const list = map.get(item.namespace) ?? [];
    list.push(item);
    map.set(item.namespace, list);
  }
  return map;
}

export default async function IamPage() {
  const clusterConfigured = hasClusterCredentials();
  const [rolesResult, roleBindingsResult, networkPoliciesResult] = await Promise.all([
    listRoles(),
    listRoleBindings(),
    listNetworkPolicies(),
  ]);

  const roles = rolesResult.ok ? rolesResult.data : [];
  const roleBindings = roleBindingsResult.ok ? roleBindingsResult.data : [];
  const networkPolicies = networkPoliciesResult.ok ? networkPoliciesResult.data : [];

  const namespaces = Array.from(
    new Set([
      ...roles.map((r) => r.namespace),
      ...roleBindings.map((r) => r.namespace),
      ...networkPolicies.map((n) => n.namespace),
    ]),
  ).sort();

  const rolesByNs = groupByNamespace(roles);
  const bindingsByNs = groupByNamespace(roleBindings);
  const policiesByNs = groupByNamespace(networkPolicies);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">IAM</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real RBAC <code>Role</code>/<code>RoleBinding</code> and{" "}
          <code>NetworkPolicy</code> objects, read cluster-wide and grouped
          by namespace -- the same objects created by the Manifests phase
          (<code>k8s/rbac.yaml</code>, <code>k8s/network-policies.yaml</code>).
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
          </div>
        )}

        {clusterConfigured && (!rolesResult.ok || !roleBindingsResult.ok || !networkPoliciesResult.ok) && (
          <div className="mb-6 space-y-2">
            {!rolesResult.ok && (
              <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                roles: {rolesResult.error}
              </p>
            )}
            {!roleBindingsResult.ok && (
              <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                rolebindings: {roleBindingsResult.error}
              </p>
            )}
            {!networkPoliciesResult.ok && (
              <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                networkpolicies: {networkPoliciesResult.error}
              </p>
            )}
          </div>
        )}

        {namespaces.length === 0 && clusterConfigured && (
          <p className="text-sm text-gray-400">No RBAC or NetworkPolicy objects found.</p>
        )}

        <div className="space-y-6">
          {namespaces.map((ns) => (
            <div key={ns} className="card p-6">
              <h2 className="mb-4 text-base font-medium text-white">
                <code>{ns}</code>
              </h2>

              <Section title="Roles" items={rolesByNs.get(ns) ?? []} />
              <Section title="RoleBindings" items={bindingsByNs.get(ns) ?? []} />

              <div className="mt-4">
                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
                  NetworkPolicies
                </h3>
                {(policiesByNs.get(ns) ?? []).length === 0 && (
                  <p className="text-sm text-gray-500">none</p>
                )}
                <ul className="space-y-1">
                  {(policiesByNs.get(ns) ?? []).map((p) => (
                    <li key={p.name} className="text-sm text-gray-100">
                      {p.name}{" "}
                      <span className="text-xs text-gray-500">
                        ({p.policyTypes.join(", ") || "no policyTypes"})
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </main>
    </>
  );
}

function Section({ title, items }: { title: string; items: RbacRole[] | IamNetworkPolicy[] }) {
  const roleItems = items as RbacRole[];
  return (
    <div className="mb-4">
      <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">{title}</h3>
      {roleItems.length === 0 && <p className="text-sm text-gray-500">none</p>}
      <ul className="space-y-1">
        {roleItems.map((item) => (
          <li key={item.name} className="text-sm text-gray-100">
            {item.name} <span className="text-xs text-gray-500">({item.detail})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
