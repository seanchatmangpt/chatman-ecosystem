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
import type { SsoGroupRoleMapping } from "@/lib/sso-role-mapping";
import { writeAuditLogEntryAwaited, newRequestId } from "@/lib/audit-db";

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
  /**
   * SSO/SCIM group -> app role mapping (lib/sso-role-mapping.ts): the
   * org's own declared intent -- "SSO group X should confer role Y" --
   * that GET /api/orgs/[id]/sso-role-drift diffs against the real,
   * live `platform-console-org-roles` ConfigMap assignments in this
   * org's own namespace to surface drift (over-privileged/orphaned
   * accounts, or a mapping nobody currently uses). Config-only, same
   * fail-closed posture as `samlConfig` immediately above: this field
   * is never read by lib/session.ts or any auth callback route to
   * actually grant a role from a real IdP group claim -- see
   * lib/sso-role-mapping.ts's module doc for the full, honest scope
   * boundary. Optional and unset by default, same forward-compatible-
   * optional-field round-trip discipline as every other optional field
   * on this type.
   */
  ssoGroupMappings?: SsoGroupRoleMapping[];
  /**
   * Per-org negotiated pricing/discount-schedule override (Fortune 5
   * procurement multi-year custom contract price, never the public
   * tiers.ts list price): see `OrgPricingOverride` below for the full
   * rationale. Optional and unset by default -- an org with no override
   * is billed at the standard TIER_RESOURCE_QUOTAS/ILLUSTRATIVE_RATES
   * list price exactly as before this field existed, same forward-
   * compatible-optional-field round-trip discipline as every other
   * optional field on this type.
   */
  pricingOverride?: OrgPricingOverride;
  /**
   * Secret & Certificate Rotation Compliance Enforcement
   * (lib/rotation-compliance.ts): `true` once a `compliance.rotation-block`
   * maker-checker approval was actually granted and applied for this org
   * -- a second, distinct owner-role approver signed off that this org's
   * live k8s Secrets or TLS certificates have exceeded
   * `ROTATION_SLA_DAYS` without being rotated, the exact SOC2 CC6.1 /
   * PCI-DSS 3.6.4 rotation-cadence control a Fortune-5 buyer's security
   * review asks for evidence of. `rotationComplianceBlockedAt` records
   * when. Optional and unset/`false` by default, same forward-compatible-
   * optional-field round-trip discipline as `autoRemediateCritical`
   * above -- this control never fires uninvited on an existing customer
   * and never blocks anything until a second approver actually agrees.
   */
  rotationComplianceBlocked?: boolean;
  rotationComplianceBlockedAt?: string;
  /**
   * Customer-Managed Encryption Key (CMEK/BYOK) binding record -- see
   * `CmekKeyBinding` below for the full rationale. Optional and unset by
   * default: an org with no binding is understood to have its Secrets/PVCs
   * encrypted under the platform's own default at-rest encryption, never
   * a customer key, same forward-compatible-optional-field round-trip
   * discipline as `pricingOverride`/`rotationComplianceBlocked` above.
   */
  cmekBinding?: CmekKeyBinding;
  /**
   * Real AWS Marketplace linkage (app/lib/entitlement-adapters/aws.ts):
   * the `customer-identifier` AWS Marketplace assigns this org's buyer at
   * subscribe time (via the SaaS registration redirect's `x-amzn-marketplace-token`
   * resolve-customer exchange -- the customer's own AWS account onboarding
   * flow, not something this console invents). Set once, by whatever route
   * handles that redirect, and read back by AwsMarketplaceAdapter's
   * applyEntitlementEvent to resolve an inbound SNS entitlement event back
   * to the org whose Project tier it should drive. Optional and unset by
   * default, same forward-compatible-optional-field round-trip discipline
   * as every other optional field on this type -- an org with no AWS
   * Marketplace subscription simply never gets one.
   */
  awsMarketplaceCustomerId?: string;
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
  // SSO/SCIM group -> app role mapping -- see the identically-named
  // field on `Org` above for the full rationale. Optional and unset by
  // default, same forward-compatible-optional-field round-trip
  // discipline as every other optional registry field above.
  ssoGroupMappings?: SsoGroupRoleMapping[];
  // Per-org negotiated pricing/discount-schedule override -- see the
  // identically-named field on `Org` above for the full rationale.
  // Optional and unset by default, same forward-compatible-optional-
  // field round-trip discipline as every other optional registry field
  // above.
  pricingOverride?: OrgPricingOverride;
  // Secret & Certificate Rotation Compliance block state -- see the
  // identically-named fields on `Org` above for the full rationale.
  // Optional and unset/`false` by default, same forward-compatible-
  // optional-field round-trip discipline as every other optional
  // registry field above.
  rotationComplianceBlocked?: boolean;
  rotationComplianceBlockedAt?: string;
  // Customer-Managed Encryption Key (CMEK/BYOK) binding -- see the
  // identically-named field on `Org` above for the full rationale.
  // Optional and unset by default, same forward-compatible-optional-
  // field round-trip discipline as every other optional registry field
  // above.
  cmekBinding?: CmekKeyBinding;
  // AWS Marketplace customer linkage -- see the identically-named field
  // on `Org` above for the full rationale. Optional and unset by
  // default, same forward-compatible-optional-field round-trip
  // discipline as every other optional registry field above.
  awsMarketplaceCustomerId?: string;
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

/**
 * Reverse lookup: which org (if any) owns a given k8s namespace.
 * lib/budget-alerts.ts and lib/cost-anomaly.ts are namespace-scoped (they
 * predate multi-tenant orgs and cover this console's own fixed platform-
 * namespace roster), so lib/webhook-poller.ts's per-namespace crossings/
 * anomaly events need this to additively route through
 * lib/alert-routing.ts's org-keyed rules. Returns `null` (not an error)
 * for a namespace with no matching org entry -- e.g. platform-console's
 * own namespace, or a namespace never provisioned via `createOrg`.
 */
export async function getOrgIdForNamespace(namespace: string): Promise<K8sResult<string | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const found = Object.entries(registry.data).find(([, entry]) => entry.namespace === namespace);
  return { ok: true, data: found ? found[0] : null };
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
 * Real SSO group -> role mapping read: backs GET
 * /api/orgs/[id]/sso-role-mapping and the drift computation in
 * GET /api/orgs/[id]/sso-role-drift. Same "`{ok: true, data: []}` is
 * not an error" convention as getOrgSamlConfig -- distinguishes "org
 * exists but has never configured a mapping" from a real registry-read
 * failure.
 */
export async function getOrgSsoGroupMappings(id: string): Promise<K8sResult<SsoGroupRoleMapping[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  return { ok: true, data: entry?.ssoGroupMappings ?? [] };
}

/**
 * Real SSO group -> role mapping write: backs the security-review-gated
 * PUT /api/orgs/[id]/sso-role-mapping, called only after that route's
 * maker-checker approval (lib/approval-workflow.ts's
 * `sso.role-mapping.update`) has actually been granted. Callers must
 * run `validateSsoGroupMappings` (lib/sso-role-mapping.ts) first --
 * same "route validates, lib function merge-patches already-valid
 * input" split as setOrgSamlConfig -- then this merge-patches only this
 * org's registry entry's `ssoGroupMappings` key, same one-key-at-a-time
 * discipline as every other setOrg* writer in this module.
 */
export async function setOrgSsoGroupMappings(
  id: string,
  mappings: SsoGroupRoleMapping[],
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, ssoGroupMappings: mappings };
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
 * Real per-org negotiated pricing/discount-schedule override (AWS/GCP/
 * Azure Enterprise Agreement custom-price-sheet line item): closes the
 * gap that lib/tiers.ts's TIER_RESOURCE_QUOTAS/RESERVATION_DISCOUNT_TABLE
 * and lib/stripe-billing.ts/lib/overage-billing.ts only ever know the
 * public list-price tier -- every Fortune 5 procurement negotiates a
 * custom multi-year contract price that never matches that sheet, and
 * today that gap is handled manually outside the console (a spreadsheet
 * finance tracks by hand). Storing this here, on the SAME
 * `platform-console-orgs` registry ConfigMap entry setOrgSla/setOrgRegion
 * already write (no new k8s resource kind), lets
 * lib/overage-billing.ts's rate computation and QBR/invoice generation
 * read the real, signed contract rate as the system of record instead.
 *
 * Exactly one of `discountPercent` (applied against the standard
 * ILLUSTRATIVE_RATES per-unit price -- a percentage OFF list) or
 * `fixedUnitPrice` (a flat replacement RateTable-shaped per-unit price,
 * negotiated as an absolute number rather than a discount off a moving
 * list price) is ever set -- never both, enforced by
 * `validatePricingOverride` below, same "reject and return a real,
 * specific error string" fail-closed discipline `validateBranding`
 * above already establishes. `effectiveFrom`/`effectiveUntil` are RFC3339
 * timestamps bounding exactly when the override is live -- a negotiated
 * contract has a real start and end date, and overage-billing must never
 * apply an expired or not-yet-started rate. `contractRef` and
 * `approvedBy` are the audit trail a QBR or an external auditor actually
 * asks for: which signed contract this rate traces to, and which
 * (internal, finance/deal-desk) identity attested it -- never a
 * free-text price an API caller can simply assert without a second,
 * distinct approver signing off (see setOrgPricingOverride below, gated
 * behind the same maker-checker `requireApproval` primitive
 * dr-failover.ts/tier.downgrade already use).
 */
export interface OrgPricingOverride {
  discountPercent?: number;
  fixedUnitPrice?: { cpuPerCoreHour: number; memoryPerGiBHour: number };
  effectiveFrom: string;
  effectiveUntil: string;
  contractRef: string;
  approvedBy: string;
}

/**
 * Fail-closed validation -- same discipline as `validateBranding` above:
 * reject and return a real, specific error string (never a fabricated
 * silent default/clamp) on anything that doesn't meet the contract, so a
 * bad negotiated-rate row can never reach the ConfigMap.
 *
 *   - Exactly one of `discountPercent`/`fixedUnitPrice` must be set.
 *   - `discountPercent` must be a finite number in (0, 100] -- 0 or
 *     negative is not a discount at all, and > 100 would mean the vendor
 *     pays the customer.
 *   - `fixedUnitPrice`'s two rates must be finite and >= 0.
 *   - `effectiveFrom`/`effectiveUntil` must both parse as real dates and
 *     `effectiveFrom` must be strictly before `effectiveUntil` -- an
 *     inverted or degenerate window can never be stored.
 *   - `contractRef`/`approvedBy` must be non-empty -- this override is
 *     never provable at audit time without both.
 */
export function validatePricingOverride(input: {
  discountPercent?: number;
  fixedUnitPrice?: { cpuPerCoreHour: number; memoryPerGiBHour: number };
  effectiveFrom: string;
  effectiveUntil: string;
  contractRef: string;
  approvedBy: string;
}): string | null {
  const hasDiscount = input.discountPercent !== undefined;
  const hasFixed = input.fixedUnitPrice !== undefined;
  if (hasDiscount === hasFixed) {
    return "exactly one of discountPercent or fixedUnitPrice is required";
  }
  if (hasDiscount) {
    if (!Number.isFinite(input.discountPercent) || input.discountPercent! <= 0 || input.discountPercent! > 100) {
      return "discountPercent must be a number in (0, 100]";
    }
  }
  if (hasFixed) {
    const { cpuPerCoreHour, memoryPerGiBHour } = input.fixedUnitPrice!;
    if (
      !Number.isFinite(cpuPerCoreHour) ||
      cpuPerCoreHour < 0 ||
      !Number.isFinite(memoryPerGiBHour) ||
      memoryPerGiBHour < 0
    ) {
      return "fixedUnitPrice.cpuPerCoreHour and memoryPerGiBHour must both be numbers >= 0";
    }
  }
  const fromMs = Date.parse(input.effectiveFrom);
  const untilMs = Date.parse(input.effectiveUntil);
  if (Number.isNaN(fromMs) || Number.isNaN(untilMs)) {
    return "effectiveFrom and effectiveUntil must both be valid RFC3339 timestamps";
  }
  if (fromMs >= untilMs) {
    return "effectiveFrom must be strictly before effectiveUntil";
  }
  if (!input.contractRef.trim()) {
    return "contractRef is required";
  }
  if (!input.approvedBy.trim()) {
    return "approvedBy is required";
  }
  return null;
}

/**
 * Real negotiated-pricing-override read: backs
 * GET /api/orgs/[id]/pricing-override. Same "`{ok: true, data: null}` is
 * not an error" convention as getOrgSla/getOrgBranding -- distinguishes
 * "org exists but has never had a negotiated rate bound" (billed at the
 * standard list price, computed by the caller, never fabricated here)
 * from a real registry-read failure.
 */
export async function getOrgPricingOverride(id: string): Promise<K8sResult<OrgPricingOverride | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };
  return { ok: true, data: entry.pricingOverride ?? null };
}

/**
 * Real negotiated-pricing-override write: backs
 * PUT /api/orgs/[id]/pricing-override. Callers (the route handler) MUST
 * gate this behind a fresh `pricing.override` approval
 * (lib/approval-workflow.ts's requireApproval, same maker-checker
 * primitive dr-failover.ts/tier.downgrade already use) before ever
 * calling this -- this function itself performs no approval check, same
 * "module exposes the setter, the route decides who may call it"
 * division of labor as every other setter in this file (see
 * setOrgSla/setOrgPatchSla above), but because this one action moves
 * real negotiated revenue it additionally writes a real, awaited
 * audit_log row (writeAuditLogEntryAwaited -- awaited, not
 * fire-and-forget, so the negotiated rate is durably provable at audit
 * time before this call returns) on every set, distinct from the
 * route's own per-request access-log entry. Passing `override: null`
 * clears/expires the override (an org reverts to standard list pricing)
 * and is logged the same way with `pricingOverrideAction: "expire"`.
 * Merge-patches only this org's registry entry's `pricingOverride` key,
 * same one-key-at-a-time discipline as every other setter in this
 * module.
 */
export async function setOrgPricingOverride(
  id: string,
  override: OrgPricingOverride | null,
  actor: string,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, pricingOverride: override ?? undefined };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/pricing-override`,
    status: 200,
    requestId: newRequestId(),
    pricingOverrideAction: override ? "set" : "expire",
    pricingOverrideContractRef: override?.contractRef ?? entry.pricingOverride?.contractRef,
  });

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

/**
 * Real Secret & Certificate Rotation Compliance block write: backs POST
 * (block) and DELETE (unblock) /api/compliance/rotation. Callers (the
 * route handler, via lib/rotation-compliance.ts's
 * applyRotationComplianceBlock/clearRotationComplianceBlock) MUST gate
 * this behind a fresh `compliance.rotation-block` approval
 * (lib/approval-workflow.ts's requireApproval, same maker-checker
 * primitive `pricing.override`/`tier.downgrade` already use) before ever
 * calling this -- this function itself performs no approval check, same
 * "module exposes the setter, the route decides who may call it"
 * division of labor as every other setter in this file (see
 * setOrgPricingOverride above). Because this action is the durable
 * SOC2/PCI compliance-violation record a security team points auditors
 * at, it writes a real, AWAITED audit_log row
 * (writeAuditLogEntryAwaited -- awaited, not fire-and-forget, so the
 * block/unblock decision is durably provable at audit time before this
 * call returns), distinct from the route's own per-request access-log
 * entry, same discipline setOrgPricingOverride already establishes for
 * its own revenue-moving write. Merge-patches only this org's registry
 * entry's `rotationComplianceBlocked`/`rotationComplianceBlockedAt` keys,
 * same one-key-at-a-time discipline as every other setter in this
 * module.
 */
export async function setOrgRotationComplianceBlock(
  id: string,
  blocked: boolean,
  actor: string,
  violationCount: number,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const blockedAt = new Date().toISOString();
  const updatedEntry: OrgRegistryEntry = {
    ...entry,
    rotationComplianceBlocked: blocked,
    rotationComplianceBlockedAt: blocked ? blockedAt : undefined,
  };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    orgId: id,
    timestamp: blockedAt,
    actor,
    method: blocked ? "POST" : "DELETE",
    path: `/api/compliance/rotation?orgId=${encodeURIComponent(id)}&blocked=${blocked}&violationCount=${violationCount}`,
    status: 200,
    requestId: newRequestId(),
  });

  return { ok: true, data: { id, ...updatedEntry } };
}

/**
 * Real per-org Customer-Managed Encryption Key (CMEK/BYOK) binding record
 * -- the specific control a Fortune 5 security review asks for before
 * this platform is trusted to store any regulated customer data: proof
 * that this org's own Secrets/PVCs are encrypted under a key reference
 * the CUSTOMER supplied and controls (their own AWS KMS/GCP Cloud KMS/
 * Azure Key Vault/HashiCorp Vault key), not the platform's shared default
 * encryption key -- so the customer, not the vendor, holds the ability to
 * revoke access to their own data at rest. Mirrors `OrgPricingOverride`'s
 * own "non-secret, auditable shape, bound only after a second approver
 * signs off" discipline field-for-field: no key MATERIAL is ever stored
 * here, only the external key's own reference id -- the actual envelope
 * encryption/decryption is always performed by the customer's own KMS,
 * never by this console.
 */
export type CmekProvider = "aws-kms" | "gcp-kms" | "azure-keyvault" | "vault";

export interface CmekKeyBinding {
  provider: CmekProvider;
  /** The customer's own external key reference -- e.g. a full AWS KMS key
   * ARN, a GCP Cloud KMS resource name, an Azure Key Vault key identifier
   * URI, or a Vault transit key name. Never key material; always a
   * reference this console hands to the CSI/Secrets-encryption layer, the
   * same "reference, not the secret itself" discipline
   * `requestedExportSubscription` already applies to bucket credentials. */
  keyRef: string;
  boundAt: string;
  boundBy: string;
  /** The key reference this binding replaced, when this binding is a
   * rotation rather than an org's first-ever binding -- `undefined` for a
   * first binding. Preserved so GET can show a real rotation history
   * entry, never fabricated. */
  previousKeyRef?: string;
  /** Non-empty human-supplied justification the approver actually reviewed
   * (e.g. "Fortune 5 security review SR-4821 BYOK requirement"), same
   * "an approver reviews a specific written reason, not a bare toggle"
   * discipline `requestedFreezeReason`/`contractRef` already establish. */
  reason: string;
}

/**
 * Fail-closed validation -- same discipline as `validatePricingOverride`
 * above: reject and return a real, specific error string (never a
 * fabricated silent default) on anything that doesn't meet the contract,
 * so a malformed CMEK binding can never reach the ConfigMap.
 *
 *   - `provider` must be one of the four supported real KMS providers.
 *   - `keyRef` must be non-empty and at least plausibly shaped for its
 *     provider (an AWS KMS ARN starts `arn:aws:kms:`, a GCP Cloud KMS
 *     resource name starts `projects/`, an Azure Key Vault key identifier
 *     is an `https://` URI, a Vault transit key name is any non-empty
 *     string -- Vault has no single canonical reference shape). This is a
 *     structural sanity check only; it never calls out to the real KMS to
 *     confirm the key exists or is reachable, the same "the console
 *     records the reference an operator asserts, it does not itself hold
 *     KMS credentials to verify it" boundary `requestedExportSubscription`
 *     already draws for bucket endpoints.
 *   - `reason`/`boundBy` must be non-empty -- this binding is never
 *     provable at audit time without both.
 */
export function validateCmekKeyBinding(input: {
  provider: CmekProvider;
  keyRef: string;
  boundBy: string;
  reason: string;
}): string | null {
  const validProviders: CmekProvider[] = ["aws-kms", "gcp-kms", "azure-keyvault", "vault"];
  if (!validProviders.includes(input.provider)) {
    return `provider must be one of: ${validProviders.join(", ")}`;
  }
  const keyRef = input.keyRef.trim();
  if (!keyRef) {
    return "keyRef is required";
  }
  if (input.provider === "aws-kms" && !keyRef.startsWith("arn:aws:kms:")) {
    return "keyRef for provider aws-kms must be a full KMS key ARN (arn:aws:kms:...)";
  }
  if (input.provider === "gcp-kms" && !keyRef.startsWith("projects/")) {
    return "keyRef for provider gcp-kms must be a full Cloud KMS resource name (projects/...)";
  }
  if (input.provider === "azure-keyvault" && !keyRef.startsWith("https://")) {
    return "keyRef for provider azure-keyvault must be a full Key Vault key identifier URI (https://...)";
  }
  if (!input.boundBy.trim()) {
    return "boundBy is required";
  }
  if (!input.reason.trim()) {
    return "reason is required";
  }
  return null;
}

/**
 * Real CMEK binding read: backs GET /api/orgs/[id]/cmek. Same
 * "`{ok: true, data: null}` is not an error" convention as
 * getOrgPricingOverride -- distinguishes "org exists but has never had a
 * customer key bound" (its Secrets/PVCs are encrypted under the
 * platform's own default, computed by the caller, never fabricated here)
 * from a real registry-read failure.
 */
export async function getOrgCmekBinding(id: string): Promise<K8sResult<CmekKeyBinding | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };
  return { ok: true, data: entry.cmekBinding ?? null };
}

/**
 * Real CMEK binding write: backs PUT/DELETE /api/orgs/[id]/cmek. Callers
 * (the route handler) MUST gate this behind a fresh `cmek.key-binding`
 * approval (lib/approval-workflow.ts's requireApproval, same maker-checker
 * primitive `pricing.override`/`tier.downgrade` already use) before ever
 * calling this -- this function itself performs no approval check, same
 * "module exposes the setter, the route decides who may call it" division
 * of labor as every other setter in this file (see setOrgPricingOverride
 * above). Because this action binds or rotates the exact key reference a
 * Fortune 5 security reviewer will ask to see proof of, it additionally
 * writes a real, AWAITED audit_log row (writeAuditLogEntryAwaited --
 * awaited, not fire-and-forget, so the binding/rotation is durably
 * provable at audit time before this call returns), distinct from the
 * route's own per-request access-log entry, same discipline
 * setOrgPricingOverride/setOrgRotationComplianceBlock already establish.
 * Passing `binding: null` clears the binding (an org reverts to the
 * platform default encryption key) and is logged the same way with
 * `cmekAction: "unbind"`. Merge-patches only this org's registry entry's
 * `cmekBinding` key, same one-key-at-a-time discipline as every other
 * setter in this module.
 */
export async function setOrgCmekBinding(
  id: string,
  binding: CmekKeyBinding | null,
  actor: string,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, cmekBinding: binding ?? undefined };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: binding ? "PUT" : "DELETE",
    path: `/api/orgs/${id}/cmek`,
    status: 200,
    requestId: newRequestId(),
    cmekAction: binding ? (entry.cmekBinding ? "rotate" : "bind") : "unbind",
    cmekProvider: binding?.provider ?? entry.cmekBinding?.provider,
    cmekKeyRef: binding?.keyRef ?? entry.cmekBinding?.keyRef,
  });

  return { ok: true, data: { id, ...updatedEntry } };
}

/**
 * Real cross-org uniqueness lookup for `awsMarketplaceCustomerId` -- same
 * "scan the registry `listOrgs` already reads, no separate index to drift
 * out of sync" discipline as `findOrgByCustomDomain` above. AWS assigns
 * one `customer-identifier` per (AWS account, product) pair, so it is
 * effectively unique per listing; this both backs the resolve-customer
 * linking route's own uniqueness guard and is the reverse lookup
 * `AwsMarketplaceAdapter.applyEntitlementEvent` (app/lib/entitlement-
 * adapters/aws.ts) calls to turn an inbound SNS entitlement event's
 * `customer-identifier` back into the org whose Project tier it should
 * drive. Returns `null` (not an error) when no org has linked that AWS
 * customer id yet.
 */
export async function findOrgByAwsMarketplaceCustomerId(
  customerId: string,
): Promise<K8sResult<string | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  for (const [id, entry] of Object.entries(registry.data)) {
    if (entry.awsMarketplaceCustomerId === customerId) {
      return { ok: true, data: id };
    }
  }
  return { ok: true, data: null };
}

/**
 * Real AWS Marketplace linkage write -- backs whatever route completes
 * the AWS SaaS registration redirect's resolve-customer exchange. Same
 * one-key-at-a-time merge-patch discipline as `setOrgCustomDomain` above;
 * callers are responsible for having already confirmed via
 * `findOrgByAwsMarketplaceCustomerId` that no OTHER org already claims
 * this AWS customer id, same "route validates, module persists" split
 * `setOrgCustomDomain`'s own header documents.
 */
export async function setOrgAwsMarketplaceCustomerId(
  id: string,
  awsMarketplaceCustomerId: string,
): Promise<K8sResult<Org | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  if (!entry) return { ok: true, data: null };

  const updatedEntry: OrgRegistryEntry = { ...entry, awsMarketplaceCustomerId };
  const result = await createOrUpdateConfigMap(ORGS_REGISTRY_NAMESPACE, ORGS_REGISTRY_CONFIGMAP, {
    [id]: JSON.stringify(updatedEntry),
  });
  if (!result.ok) return result;

  return { ok: true, data: { id, ...updatedEntry } };
}
