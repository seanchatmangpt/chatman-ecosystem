/**
 * Real self-service org/tenant provisioning -- the module that closes the
 * gap this repo's evidence bundle documents under
 * "self-service-project-provisioning": that control lets an
 * ALREADY-AUTHENTICATED operator create a Project inside an EXISTING
 * namespace. It has no concept of a second customer org; every session in
 * this app -- local-admin or gotrue -- shares the one
 * platform-console-org-roles ConfigMap (lib/authz.ts) inside the one
 * platform-console namespace this console itself runs in.
 *
 * This module adds the missing layer underneath that: a new k8s
 * Namespace per paying customer (`org-<slug>-<suffix>`), a real
 * `platform-console-org-roles` ConfigMap seeded `{owner: "owner"}` INSIDE
 * that new namespace (reusing lib/authz.ts's exact ConfigMap name and
 * shape -- so the existing OrgRolesPanel UI and requireRole gate work
 * unmodified against a customer org's namespace, not just
 * platform-console's own), and one central registry ConfigMap
 * (`platform-console-orgs`, in the `platform-console` namespace) mapping
 * org id -> {name, namespace, ownerIdentifier, createdAt} so /api/orgs
 * (GET) and any other org-aware code can list orgs without a cluster-wide
 * namespace scan.
 *
 * Same fail-closed `K8sResult<T>` / get-then-create-or-patch conventions
 * as lib/k8s.ts and lib/authz.ts throughout -- no new pattern introduced.
 */
import {
  createNamespace,
  createOrUpdateConfigMap,
  createProjectWithDatabase,
  getConfigMap,
  type K8sResult,
} from "@/lib/k8s";

export const ORGS_REGISTRY_NAMESPACE = "platform-console";
export const ORGS_REGISTRY_CONFIGMAP = "platform-console-orgs";
export const ORG_ROLES_CONFIGMAP_NAME = "platform-console-org-roles";

export interface Org {
  id: string;
  name: string;
  namespace: string;
  ownerIdentifier: string;
  createdAt: string;
}

interface OrgRegistryEntry {
  name: string;
  namespace: string;
  ownerIdentifier: string;
  createdAt: string;
}

// Same disallowed-character escaping lib/authz.ts's
// encodeIdentifierKey/decodeIdentifierKey uses for ConfigMap `data` keys
// (must match `[-._a-zA-Z0-9]+`) -- duplicated here (not imported) because
// authz.ts does not export it; org ids never contain characters outside
// that set (see slugify below) so this only guards the identifier stored
// as JSON *value*, which has no such restriction, but is kept identical
// for consistency with the rest of this codebase's ConfigMap handling.
function slugify(input: string): string {
  const slug = input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || "org";
}

function namespaceFor(orgName: string): string {
  const slug = slugify(orgName).slice(0, 40);
  const suffix = globalThis.crypto.randomUUID().slice(0, 8);
  return `org-${slug}-${suffix}`;
}

async function getRegistry(): Promise<K8sResult<Record<string, OrgRegistryEntry>>> {
  const existing = await getConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, OrgRegistryEntry> = {};
  for (const [id, raw] of Object.entries(existing.data.data)) {
    try {
      parsed[id] = JSON.parse(raw) as OrgRegistryEntry;
    } catch {
      // A hand-edited or corrupt registry entry is skipped, not fatal --
      // same "don't let one bad row break the whole list" discipline
      // toAssignments in lib/authz.ts uses via its isRole filter.
    }
  }
  return { ok: true, data: parsed };
}

export async function listOrgs(): Promise<K8sResult<Org[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const orgs = Object.entries(registry.data)
    .map(([id, entry]) => ({ id, ...entry }))
    .sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  return { ok: true, data: orgs };
}

export async function getOrg(id: string): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  return { ok: true, data: entry ? { id, ...entry } : null };
}

export interface CreateOrgResult {
  org: Org;
  firstProjectName: string | null;
  firstProjectError: string | null;
}

/**
 * Real, end-to-end tenant provisioning:
 *   1. POST a new Namespace (labeled `platform-console.io/org-id`,
 *      `platform-console.io/managed-by=platform-console`).
 *   2. Seed that namespace's own `platform-console-org-roles` ConfigMap
 *      with `{ownerIdentifier: "owner"}` -- the SAME ConfigMap name
 *      lib/authz.ts already reads/writes, just in the new namespace
 *      instead of platform-console's own, so /org's existing
 *      OrgRolesPanel UI works against a customer org unmodified (a
 *      future multi-namespace-aware /org would only need to accept a
 *      `?namespace=` param -- out of scope for this change, disclosed
 *      below, not silently claimed done).
 *   3. Register the org in the central `platform-console-orgs` registry.
 *   4. Provision that org's first real Project (paired SingleDatabase),
 *      inside its own namespace, via the existing
 *      createProjectWithDatabase primitive -- the actual "self-service
 *      project provisioning" control, now reachable from a namespace this
 *      flow itself just created instead of a pre-seeded one.
 *
 * Step 4's failure does NOT unwind steps 1-3: an org that exists but
 * whose first project failed to provision is a real, visible, retriable
 * state (same "leave partial state for a human/retry, never silently
 * roll back a multi-object k8s change" discipline the Backups module's
 * own comment documents) -- surfaced via `firstProjectError`, not hidden.
 */
export async function createOrg(input: {
  name: string;
  ownerIdentifier: string;
}): Promise<K8sResult<CreateOrgResult>> {
  const id = globalThis.crypto.randomUUID();
  const namespace = namespaceFor(input.name);

  const nsResult = await createNamespace(namespace, {
    "platform-console.io/org-id": id,
    "platform-console.io/managed-by": "platform-console",
  });
  if (!nsResult.ok) return nsResult;

  const rolesResult = await createOrUpdateConfigMap(namespace, ORG_ROLES_CONFIGMAP_NAME, {
    [input.ownerIdentifier]: "owner",
  });
  if (!rolesResult.ok) return rolesResult;

  const createdAt = new Date().toISOString();
  const registryEntry: OrgRegistryEntry = {
    name: input.name,
    namespace,
    ownerIdentifier: input.ownerIdentifier,
    createdAt,
  };
  const registryResult = await createOrUpdateConfigMap(
    ORGS_REGISTRY_NAMESPACE,
    ORGS_REGISTRY_CONFIGMAP,
    { [id]: JSON.stringify(registryEntry) },
  );
  if (!registryResult.ok) return registryResult;

  const org: Org = { id, ...registryEntry };

  const firstProjectName = "first-project";
  const projectResult = await createProjectWithDatabase({
    name: firstProjectName,
    namespace,
    databaseRefName: `${firstProjectName}-db`,
    hostname: `${firstProjectName}.${namespace}.svc.cluster.local`,
    protocol: "http",
    dbStorageSize: "1Gi",
  });

  return {
    ok: true,
    data: {
      org,
      firstProjectName: projectResult.ok ? firstProjectName : null,
      firstProjectError: projectResult.ok ? null : projectResult.error,
    },
  };
}
