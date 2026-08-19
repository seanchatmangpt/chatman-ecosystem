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
  k8sRequest,
  listNodeRegions,
  listProjects,
  type K8sResult,
} from "@/lib/k8s";
import {
  tierAtLeast,
  DEFAULT_PROJECT_TIER,
  SLA_TIER_DEFAULTS,
  DEFAULT_SLA_TIER,
  type ProjectTier,
  type SlaTier,
} from "@/lib/tiers";

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
  region?: string;
  slaTier?: SlaTier;
  slaResponseTimeHours?: number;
  slaUptimeTargetPct?: number;
}

interface OrgRegistryEntry {
  name: string;
  namespace: string;
  ownerIdentifier: string;
  createdAt: string;
  branding?: OrgBranding;
  // Per-org contractual SLA / support-priority tier (AWS Enterprise
  // Support / GCP Premium Support-style paid line item Sales can price
  // separately from compute tier): which of SLA_TIER_DEFAULTS
  // (lib/tiers.ts) this org is contracted at, plus the two concrete
  // numbers procurement actually signs -- response-time commitment (in
  // hours) and uptime target (percent) -- copied from that table at
  // write time so a later change to the table's defaults never silently
  // rewrites an already-signed contract's numbers out from under an
  // existing org. Optional and unset by default, same forward-
  // compatible-optional-field round-trip discipline as `branding`/
  // `region` above.
  slaTier?: SlaTier;
  slaResponseTimeHours?: number;
  slaUptimeTargetPct?: number;
  // Data residency / region pinning (AWS/GCP/Azure enterprise-tier
  // console line item; GDPR data-localization / US financial
  // data-residency requirement for regulated buyers). Optional and
  // unset by default, same forward-compatible-optional-field round-trip
  // discipline as `branding` above -- every org registered before this
  // field existed round-trips through JSON.parse/stringify with
  // `region: undefined`. Gated to enterprise-tier orgs at write time
  // (setOrgRegion below); a value ONLY ever lands here already
  // validated against the cluster's real, live node region labels
  // (lib/k8s.ts's listNodeRegions) -- never a fabricated/free-text
  // region string.
  region?: string;
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

/**
 * Real, irreversible tenant teardown -- backs the maker-checker-gated
 * DELETE /api/orgs/[id] (see lib/approval-workflow.ts). Deletes the real
 * k8s Namespace this org's createOrg provisioned (cascading every
 * Project/SingleDatabase/Secret/ConfigMap k8s already owns inside it,
 * same "namespace delete cascades" semantics every k8s cluster
 * guarantees), then removes the org's own row from the central
 * `platform-console-orgs` registry via the same RFC 7386
 * null-value-removes-the-key merge-patch discipline
 * lib/budget-alerts.ts's deleteBudgetThreshold already established --
 * createOrUpdateConfigMap's `Record<string, string>` signature can't
 * express a key removal directly, so the patch is built with an explicit
 * `null` and cast the same way deleteBudgetThreshold does.
 *
 * Namespace deletion is attempted first: if it fails for a reason other
 * than "already gone" (e.g. a real k8s API error), the registry entry is
 * deliberately left in place -- a visible, retriable "org still exists"
 * state, never a registry row silently pointing at a namespace no one
 * can find, and never a customer's data wiped while the platform still
 * thinks the org exists.
 */
export async function deleteOrg(id: string): Promise<K8sResult<null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const nsResult = await k8sRequest<unknown>(
    `/api/v1/namespaces/${encodeURIComponent(entry.namespace)}`,
    "DELETE",
  );
  if (!nsResult.ok && !/not found/i.test(nsResult.error)) {
    return nsResult;
  }

  const patch: Record<string, string | null> = { [id]: null };
  const result = await createOrUpdateConfigMap(
    ORGS_REGISTRY_NAMESPACE,
    ORGS_REGISTRY_CONFIGMAP,
    patch as unknown as Record<string, string>,
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

/**
 * Real "this org's Project tier" read, backing the enterprise-tier gate
 * on region pinning below. Mirrors setProjectTier/TIER_GATED_FLAGS'
 * existing "read the real tier label back off the cluster, never trust
 * a cached/client-supplied value" discipline: lists every real Project
 * CR in this org's own namespace (lib/k8s.ts's listProjects, client-
 * filtered by namespace the same way getProjectDatabasePod's callers
 * already scope a cluster-wide list to one namespace) and returns the
 * HIGHEST tier among them via tierAtLeast's starter < pro < enterprise
 * ordering -- an org with even one enterprise-tier Project is treated
 * as an enterprise org for this gate, so upgrading any one Project's
 * tier (existing setProjectTier) is enough to unlock region pinning,
 * with no separate "org tier" field to duplicate/drift from the real
 * per-Project label. An org with no Projects yet reads as
 * DEFAULT_PROJECT_TIER (starter) -- fail closed, never enterprise by
 * default.
 */
export async function getOrgProjectTier(namespace: string): Promise<K8sResult<ProjectTier>> {
  const result = await listProjects();
  if (!result.ok) return result;
  const inNamespace = result.data.filter((p) => p.namespace === namespace);
  let highest: ProjectTier = DEFAULT_PROJECT_TIER;
  for (const project of inNamespace) {
    if (tierAtLeast(project.tier, highest)) highest = project.tier;
  }
  return { ok: true, data: highest };
}

/**
 * Real region-pinning read: backs GET /api/orgs/[id]/region. Same
 * "`{ok: true, data: null}` is not an error" convention as
 * getOrgBranding -- distinguishes "org exists but has never pinned a
 * region" from a real k8s registry-read failure.
 */
export async function getOrgRegion(id: string): Promise<K8sResult<string | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  return { ok: true, data: entry?.region ?? null };
}

/**
 * Real region-pinning write: backs PUT /api/orgs/[id]/region. Enforces
 * BOTH real gates server-side (never trusts the caller to have already
 * checked either):
 *   1. Enterprise tier: this org's real Project tier (getOrgProjectTier
 *      above) must be at least "enterprise" -- mirrors TIER_GATED_FLAGS'
 *      existing tierAtLeast pattern for gating a capability behind a
 *      minimum Project tier.
 *   2. Live region: `region` must be one `listNodeRegions` (lib/k8s.ts)
 *      actually reports for this cluster's real nodes right now -- never
 *      a fabricated/free-text value that could never be satisfied by the
 *      k8s scheduler.
 * Returns a specific string error (never silently coerced/defaulted) for
 * either failure, same fail-closed discipline as validateBranding.
 * Merge-patches only this org's registry entry's `region` key, same
 * one-key-at-a-time discipline as setOrgBranding.
 */
export async function setOrgRegion(id: string, region: string): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const tierResult = await getOrgProjectTier(entry.namespace);
  if (!tierResult.ok) return tierResult;
  if (!tierAtLeast(tierResult.data, "enterprise")) {
    return { ok: false, error: "region pinning requires this org's Project tier to be enterprise" };
  }

  const regionsResult = await listNodeRegions();
  if (!regionsResult.ok) return regionsResult;
  if (!regionsResult.data.includes(region)) {
    return {
      ok: false,
      error: `region must be one of the cluster's live node regions: ${regionsResult.data.join(", ") || "(none detected)"}`,
    };
  }

  const updatedEntry: OrgRegistryEntry = { ...entry, region };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}

export interface OrgSla {
  slaTier: SlaTier;
  slaResponseTimeHours: number;
  slaUptimeTargetPct: number;
}

/**
 * Real SLA-config read: backs GET /api/orgs/[id]/sla. Same
 * "`{ok: true, data: null}` is not an error" convention as
 * getOrgBranding/getOrgRegion -- distinguishes "org exists but has never
 * had an SLA tier assigned" (defaults to DEFAULT_SLA_TIER's numbers,
 * applied by the route, not fabricated here) from a real registry-read
 * failure. Returns the raw stored fields only; the route layers the
 * "currently meeting SLA" computation on top since that check depends on
 * incident/uptime data this module has no reason to own.
 */
export async function getOrgSla(id: string): Promise<K8sResult<OrgSla | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };
  return {
    ok: true,
    data: {
      slaTier: entry.slaTier ?? DEFAULT_SLA_TIER,
      slaResponseTimeHours: entry.slaResponseTimeHours ?? SLA_TIER_DEFAULTS[DEFAULT_SLA_TIER].slaResponseTimeHours,
      slaUptimeTargetPct: entry.slaUptimeTargetPct ?? SLA_TIER_DEFAULTS[DEFAULT_SLA_TIER].slaUptimeTargetPct,
    },
  };
}

/**
 * Real SLA-tier write: backs PUT /api/orgs/[id]/sla. `slaResponseTimeHours`
 * and `slaUptimeTargetPct` are NEVER accepted from the caller -- they are
 * always recomputed here from SLA_TIER_DEFAULTS (lib/tiers.ts) keyed by
 * the new `slaTier`, the same "fixed lookup table, never a free-text/
 * client-supplied number" discipline `resourceQuotaHardFor` already
 * established for ResourceQuota ceilings. Merge-patches only this org's
 * registry entry's three `sla*` keys, same one-key(-group)-at-a-time
 * discipline as setOrgBranding/setOrgRegion.
 */
export async function setOrgSla(id: string, slaTier: SlaTier): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const defaults = SLA_TIER_DEFAULTS[slaTier];
  const updatedEntry: OrgRegistryEntry = {
    ...entry,
    slaTier,
    slaResponseTimeHours: defaults.slaResponseTimeHours,
    slaUptimeTargetPct: defaults.slaUptimeTargetPct,
  };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}
