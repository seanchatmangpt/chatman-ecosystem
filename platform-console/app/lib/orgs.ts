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
  type PatchSlaTier,
} from "@/lib/tiers";
import type { SamlConfig } from "@/lib/saml-config";

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
  /** Per-org opt-in (SOC2 CC7.1 vulnerability-management auto-remediation
   * SLA): when `true`, POST /api/security-scan/auto-remediate is allowed
   * to file a `deployment.quarantine` maker-checker approval request
   * (lib/approval-workflow.ts) against this org's own Deployments the
   * moment a scan finds a CRITICAL CVE tied to one of them -- it still
   * never actuates without a second, distinct approver. Optional and
   * unset/`false` by default, same forward-compatible-optional-field
   * round-trip discipline as `branding`/`region` above: this control never
   * fires uninvited on an existing customer. */
  autoRemediateCritical?: boolean;
  /** Per-org opt-in for K8s Fault Diagnosis
   * (lib/k8s-fault-scan.ts, wrapping autofde-lab's real structural-
   * anomaly scanner): when `true`, POST /api/k8s-fault-scan is allowed
   * to collect this org's own namespace's live cluster state and run the
   * real scanner against it. Same "never runs against an org that hasn't
   * turned it on" discipline `autoRemediateCritical` above already
   * establishes -- optional and unset/`false` by default, so this
   * control never fires uninvited on an existing customer. */
  enableFaultScan?: boolean;
  /**
   * SLA credit auto-application idempotency guard (see
   * setOrgLastSlaCreditAppliedMonth below and
   * POST /api/orgs/[id]/sla-credits): the last "YYYY-MM" month this org
   * had a real SLA credit actually applied to its Stripe customer
   * balance for. Optional and unset by default, same forward-compatible-
   * optional-field round-trip discipline as `branding`/`region`/
   * `autoRemediateCritical` above -- every org registered (or credited)
   * before this field existed round-trips through JSON.parse/stringify
   * with `lastSlaCreditAppliedMonth: undefined`.
   */
  lastSlaCreditAppliedMonth?: string;
  /**
   * Per-org custom domain self-service (the standard AWS Amplify/Vercel/
   * Retool "custom domain" enterprise-tier upsell, sitting directly on top
   * of the white-label branding above -- branding changes the CHROME,
   * this changes the URL it's served on). `customDomain` is the hostname
   * the org's owner has requested (e.g. `console.customer.com`);
   * `customDomainStatus` mirrors the real, live state of the
   * `cert-manager.io/v1` Certificate CR lib/k8s.ts's createOrgCertificate
   * creates for it (`pending` until cert-manager's own controller flips
   * the Certificate's `status.conditions[type=Ready]` to `True`, `issued`
   * once it has, `failed` if cert-manager reports a terminal failure) --
   * never a value this module invents client-side. Optional and unset by
   * default, same forward-compatible-optional-field round-trip discipline
   * as `branding`/`region` above.
   */
  customDomain?: string;
  customDomainStatus?: "pending" | "issued" | "failed";
  /**
   * Contractual Patch-Timeliness SLA Tier (CVE Remediation Credits,
   * lib/patch-sla.ts): a SEPARATE contracted commitment from `slaTier`
   * above (that one is uptime/support-response; this one is "how fast
   * does a CRITICAL/HIGH CVE actually get remediated"). Unset by default
   * -- an org with no `patchSlaTier` has made no patch-timeliness
   * commitment at all and is never walked by the breach-detection cron
   * (app/api/cron/patch-sla-breach-scan/route.ts checks `patchSlaTier !=
   * null` before scoring any org), same "opt-in, never fires uninvited"
   * discipline `autoRemediateCritical` above already establishes. See
   * lib/tiers.ts's `PATCH_SLA_COMMITTED_HOURS` for the fixed per-tier,
   * per-severity remediation-window table this is scored against.
   */
  patchSlaTier?: PatchSlaTier;
  /**
   * Partner/MSP Multi-Tenant Management Console (lib/partners.ts): the
   * id of the `Partner` record that manages this org, if any -- the
   * missing "managing identity above a single org" concept this file's
   * own module doc used to have no way to express. Purely denormalized
   * from a Partner's own `managedOrgIds` list (the Partner record is
   * still the source of truth an MSP CRUDs); kept here too so a reader
   * that already has an `Org` (e.g. an org's own admin page) can show
   * "managed by <partner>" without a second registry scan. Optional and
   * unset by default, same forward-compatible-optional-field round-trip
   * discipline as every other optional field on this type -- every org
   * registered before this field existed round-trips through
   * JSON.parse/stringify with `managingPartnerId: undefined`.
   */
  managingPartnerId?: string;
  /**
   * Customer-facing SAML 2.0 metadata configuration surface (config-only,
   * fail-closed -- see lib/saml-config.ts's module doc for the full
   * rationale): an org admin's submitted IdP Entity ID / SSO URL / signing
   * certificate, structurally validated offline and persisted here so it
   * round-trips exactly like `branding`/`region` above. `status` tracks
   * `unconfigured` (never set) -> `configured` (validated shape saved,
   * no real assertion flow wired) -> `validated` reserved for a later
   * pass that actually exercises the IdP's real SSO redirect. No code
   * path in lib/session.ts or any auth callback route reads this field
   * to authenticate a session -- the existing OIDC/Supabase login path
   * is entirely unaffected by this field's presence or value. Optional
   * and unset by default, same forward-compatible-optional-field round-
   * trip discipline as every other optional field on this type.
   */
  samlConfig?: SamlConfig;
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
  // Vulnerability-scan-triggered auto-remediation opt-in (see the
  // `autoRemediateCritical` field on `Org` above for the full rationale).
  // Optional and unset/`false` by default -- every org registered before
  // this field existed round-trips through JSON.parse/stringify with
  // `autoRemediateCritical: undefined`, treated identically to `false` by
  // every reader (setOrgAutoRemediateCritical below is the only writer).
  autoRemediateCritical?: boolean;
  // K8s Fault Diagnosis opt-in -- see the identically-named field on
  // `Org` above for the full rationale. Optional and unset/`false` by
  // default, same round-trip discipline as `autoRemediateCritical`.
  enableFaultScan?: boolean;
  // SLA credit auto-application idempotency guard -- see the identically-
  // named field on `Org` above for the full rationale. Optional and unset
  // by default, same forward-compatible-optional-field round-trip
  // discipline as every other optional registry field above.
  lastSlaCreditAppliedMonth?: string;
  // Custom-domain binding -- see the identically-named fields on `Org`
  // above for the full rationale. Optional and unset by default, same
  // forward-compatible-optional-field round-trip discipline as every
  // other optional registry field above.
  customDomain?: string;
  customDomainStatus?: "pending" | "issued" | "failed";
  // Patch-Timeliness SLA tier -- see the identically-named field on `Org`
  // above for the full rationale. Optional and unset by default, same
  // forward-compatible-optional-field round-trip discipline as every
  // other optional registry field above.
  patchSlaTier?: PatchSlaTier;
  // Partner/MSP managing-identity link -- see the identically-named
  // field on `Org` above for the full rationale. Optional and unset by
  // default, same forward-compatible-optional-field round-trip
  // discipline as every other optional registry field above.
  managingPartnerId?: string;
  // SAML metadata configuration -- see the identically-named field on
  // `Org` above for the full rationale. Optional and unset by default,
  // same forward-compatible-optional-field round-trip discipline as
  // every other optional registry field above.
  samlConfig?: SamlConfig;
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
 * Real SAML config read: backs GET /api/orgs/[id]/saml-config. Same
 * "`{ok: true, data: null}` is not an error" convention as
 * getOrgBranding/getOrgRegion -- distinguishes "org exists but has never
 * configured SAML metadata" from a real registry-read failure.
 */
export async function getOrgSamlConfig(id: string): Promise<K8sResult<SamlConfig | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  return { ok: true, data: entry?.samlConfig ?? null };
}

/**
 * Real SAML config write: backs PUT /api/orgs/[id]/saml-config. Callers
 * must run `validateSamlConfig` (lib/saml-config.ts) first -- same
 * "route validates, lib function merge-patches already-valid input"
 * split as setOrgBranding/validateBranding -- then this merge-patches
 * only this org's registry entry's `samlConfig` key, same one-key-at-a-
 * time discipline as setOrgBranding/setOrgRegion. On success the persisted
 * status is always `"configured"`: this write only ever proves the
 * submitted metadata is structurally well-formed, never that a real SAML
 * assertion flow has been exercised end to end (that would be
 * `"validated"`, reserved for a later pass -- see lib/saml-config.ts's
 * module doc). Fail-closed: this function has no side effect on
 * lib/session.ts or any auth callback route.
 */
export async function setOrgSamlConfig(
  id: string,
  input: { entityId: string; ssoUrl: string; certificatePem: string },
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const samlConfig: SamlConfig = {
    entityId: input.entityId,
    ssoUrl: input.ssoUrl,
    certificatePem: input.certificatePem,
    status: "configured",
    updatedAt: new Date().toISOString(),
  };
  const updatedEntry: OrgRegistryEntry = { ...entry, samlConfig };
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

/**
 * Real cross-org uniqueness check: backs POST /api/orgs/[id]/custom-domain.
 * Scans every existing org's registry entry (the same registry `listOrgs`
 * itself reads -- no separate hostname index to drift out of sync) and
 * returns the id of whichever OTHER org already has `hostname` bound, or
 * `null` if it's free. Comparison is case-insensitive (DNS hostnames are
 * not case-sensitive) and excludes `excludeOrgId` so an org re-submitting
 * its OWN already-bound hostname is never rejected as "claimed".
 */
export async function findOrgByCustomDomain(
  hostname: string,
  excludeOrgId?: string,
): Promise<K8sResult<string | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const needle = hostname.toLowerCase();
  for (const [id, entry] of Object.entries(registry.data)) {
    if (id === excludeOrgId) continue;
    if (entry.customDomain?.toLowerCase() === needle) {
      return { ok: true, data: id };
    }
  }
  return { ok: true, data: null };
}

/**
 * Real custom-domain read: backs GET /api/orgs/[id]/custom-domain. Same
 * "`{ok: true, data: null}` is not an error" convention as
 * getOrgBranding/getOrgRegion -- distinguishes "org exists but has never
 * requested a custom domain" from a real registry-read failure.
 */
export async function getOrgCustomDomain(
  id: string,
): Promise<K8sResult<{ customDomain: string; customDomainStatus: "pending" | "issued" | "failed" } | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry?.customDomain) return { ok: true, data: null };
  return {
    ok: true,
    data: { customDomain: entry.customDomain, customDomainStatus: entry.customDomainStatus ?? "pending" },
  };
}

/**
 * Real custom-domain write: backs POST /api/orgs/[id]/custom-domain, called
 * ONLY after the route has already (a) validated the hostname shape
 * (lib/custom-domains.ts's isValidCustomDomainHostname) and (b) confirmed
 * via findOrgByCustomDomain above that no OTHER org already claims it --
 * this function itself does not re-check either, same "route validates,
 * module persists" division of labor setOrgRegion's route/module split
 * already uses for its own tier/region checks. Merge-patches only this
 * org's registry entry's `customDomain`/`customDomainStatus` keys, same
 * one-key-at-a-time discipline as setOrgBranding/setOrgRegion.
 */
export async function setOrgCustomDomain(
  id: string,
  hostname: string,
  status: "pending" | "issued" | "failed",
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, customDomain: hostname, customDomainStatus: status };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}

/**
 * Updates just this org's `customDomainStatus` (never the hostname itself)
 * -- backs GET /api/orgs/[id]/custom-domain's live-poll re-sync, when a
 * fresh read of the Certificate CR's own status (lib/k8s.ts's
 * getCertificateStatus) disagrees with whatever status was last persisted
 * here. A no-op (returns the org unchanged) if this org has no
 * `customDomain` bound at all, so a stale/racing poll can never invent one.
 */
export async function setOrgCustomDomainStatus(
  id: string,
  status: "pending" | "issued" | "failed",
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry?.customDomain) return { ok: true, data: entry ? { id, ...entry } : null };

  const updatedEntry: OrgRegistryEntry = { ...entry, customDomainStatus: status };
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

/**
 * Real Patch-Timeliness SLA-tier write: backs PUT on the patch-SLA config
 * (no dedicated PUT route was in this pass's scope -- setOrgSla's sibling
 * exists so any future admin UI/route has a real writer to call, same
 * "module exposes the setter, the route decides who may call it" division
 * of labor as every other setter in this file). Unlike `slaTier` this
 * tier has no derived-numbers side table to also write -- the committed-
 * hours lookup (`PATCH_SLA_COMMITTED_HOURS`, lib/tiers.ts) is read fresh
 * by lib/patch-sla.ts at breach-detection time, never copied onto the
 * registry entry, so a later change to that table takes effect on the
 * NEXT scan for every org already on that tier (deliberately different
 * from setOrgSla's copy-at-write-time choice: a patch-timeliness
 * commitment is scored against whatever window is CURRENTLY contracted
 * for that tier, not a snapshot frozen at enrollment). Merge-patches only
 * `patchSlaTier`, same one-key-at-a-time discipline as every other setter
 * in this module. `null` clears the commitment (org opts out of the
 * patch-timeliness SLA entirely).
 */
export async function setOrgPatchSla(
  id: string,
  patchSlaTier: PatchSlaTier | null,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, patchSlaTier: patchSlaTier ?? undefined };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}

/**
 * Real per-org auto-remediation opt-in write: backs
 * PUT /api/orgs/[id]/auto-remediate-critical (and any admin UI toggle).
 * Same one-key-at-a-time merge-patch discipline as setOrgBranding/
 * setOrgRegion/setOrgSla -- flips exactly `autoRemediateCritical`, never
 * touches any other registry field.
 */
export async function setOrgAutoRemediateCritical(
  id: string,
  enabled: boolean,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, autoRemediateCritical: enabled };
  const patchResult = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!patchResult.ok) return patchResult;

  return { ok: true, data: { id, ...updatedEntry } };
}

/**
 * Real SLA-credit-applied write: backs the actual-application half of
 * POST /api/orgs/[id]/sla-credits, called ONLY after a real Stripe
 * customer-balance transaction has actually been created
 * (lib/stripe-billing.ts's applySlaCreditToStripeBalance). Records
 * `month` as the last month this org had a credit applied for -- the
 * route reads this back BEFORE calling Stripe to refuse a second
 * application for the same month (no single actor, retry, or duplicate
 * approval can double-credit a customer's balance). Same one-key-at-a-
 * time merge-patch discipline as every other setter in this module.
 */
export async function setOrgLastSlaCreditAppliedMonth(
  id: string,
  month: string,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, lastSlaCreditAppliedMonth: month };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}

/**
 * Partner/MSP managing-identity link writer -- called from
 * lib/partners.ts whenever a Partner's own `managedOrgIds` changes, so
 * this denormalized pointer on the Org side never drifts from the
 * Partner record that is its source of truth. `partnerId: null` clears
 * the link (an org removed from a partner's managed list, or the
 * partner itself deleted). Same partial-merge-write convention as
 * setOrgLastSlaCreditAppliedMonth immediately above.
 */
export async function setOrgManagingPartnerId(
  id: string,
  partnerId: string | null,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = {
    ...entry,
    managingPartnerId: partnerId ?? undefined,
  };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}
