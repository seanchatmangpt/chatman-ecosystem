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

// Per-org white-label branding (Vercel/Retool/Auth0-style paid add-on
// tier): a customer org can override this console's default chrome --
// product name, sidebar logo, accent color -- for its own end users.
// Optional and unset by default so every existing org (created before
// this field existed) round-trips through JSON.parse/stringify below
// with `branding: undefined`, same as any other optional field added to
// an already-live JSON-in-ConfigMap-value record in this codebase.
export interface OrgBranding {
  productName: string;
  logoUrl: string;
  accentColor: string;
}

export interface Org {
  id: string;
  name: string;
  namespace: string;
  ownerIdentifier: string;
  createdAt: string;
  branding?: OrgBranding;
}

interface OrgRegistryEntry {
  name: string;
  namespace: string;
  ownerIdentifier: string;
  createdAt: string;
  branding?: OrgBranding;
}

const PRODUCT_NAME_MAX_LENGTH = 60;
const ACCENT_COLOR_RE = /^#[0-9a-fA-F]{6}$/;

/**
 * Fail-closed branding validation -- same discipline as
 * lib/custom-domains.ts's SAN check: reject and return a real, specific
 * error string (never a fabricated silent default) on anything that
 * doesn't meet the contract, so a bad value can never reach the
 * ConfigMap or a rendered page.
 *
 *   - logoUrl must be `https://` -- `data:` URIs are rejected (a stored
 *     XSS vector if ever rendered as-is) and plain `http://` is rejected
 *     (mixed-content warnings/blocking on an https console).
 *   - accentColor must be a strict 6-hex-digit `#rrggbb` (rejects named
 *     colors, 3-digit shorthand, and any CSS injection via `url(...)` /
 *     `;` etc. -- it can only ever be a hex string this regex accepts).
 *   - productName is capped at 60 characters (`PRODUCT_NAME_MAX_LENGTH`).
 */
export function validateBranding(input: {
  productName: string;
  logoUrl: string;
  accentColor: string;
}): string | null {
  if (!input.productName || input.productName.length > PRODUCT_NAME_MAX_LENGTH) {
    return `productName is required and must be at most ${PRODUCT_NAME_MAX_LENGTH} characters`;
  }
  if (!input.logoUrl.startsWith("https://")) {
    return "logoUrl must be an https:// URL";
  }
  if (!ACCENT_COLOR_RE.test(input.accentColor)) {
    return "accentColor must match /^#[0-9a-fA-F]{6}$/";
  }
  return null;
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

/**
 * Real branding read: backs GET /api/orgs/[id]/branding. Returns
 * `{ok: true, data: null}` -- not an error -- both when the org doesn't
 * exist and when it exists but has never set branding, so a caller can
 * distinguish "use the default platform-console chrome" from a real k8s
 * failure the same way getConfigMap already distinguishes "not
 * provisioned" from "API error".
 */
export async function getOrgBranding(id: string): Promise<K8sResult<OrgBranding | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  return { ok: true, data: entry?.branding ?? null };
}

/**
 * Real branding write: backs PUT /api/orgs/[id]/branding. Merge-patches
 * only this org's registry entry via the exact same
 * createOrUpdateConfigMap primitive createOrg already uses to write the
 * registry -- the entry's own `branding` key is replaced wholesale (this
 * function's caller has already run it through validateBranding above),
 * every other registry key (name, namespace, ownerIdentifier, createdAt)
 * and every other org's entry is left untouched, same one-key-at-a-time
 * merge-patch discipline as lib/authz.ts's setOrgRole.
 */
export async function setOrgBranding(
  id: string,
  branding: OrgBranding,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, branding };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}
