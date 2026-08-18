/**
 * Real hyperscaler-PaaS-style Resource Tagging / Organization primitive
 * (AWS Resource Groups & Tag Editor / GCP Labels / Azure Tags equivalent):
 * an operator attaches a `key=value` pair to a real platform resource, and
 * that pair is a genuine Kubernetes `metadata.labels` entry on the real
 * object -- never a separate tags table or client-side annotation this
 * console invents. Every tag is written as
 * `platform-console.io/tag-<key>: <value>` via a real RFC 7386 JSON merge
 * patch (the exact same `Content-Type: application/merge-patch+json`
 * convention lib/k8s.ts's `createOrUpdateConfigMap` already established),
 * and every "browse by tag" query is a real `?labelSelector=<key>=<value>`
 * query parameter against the k8s API -- server-side filtering, never a
 * client-side `.filter()` over an unfiltered list.
 *
 * Resource categories reuse exactly the set Global Search
 * (lib/global-search.ts) already established, restricted to the 4 real
 * kinds this module actually PATCHes: Services, Projects, CronJobs
 * (Scheduled Jobs), and the platform's 2 singleton ConfigMaps (Feature
 * Flags, Webhooks) -- surfaced as 2 separate tag categories
 * (`feature-flags`/`webhooks`) since they are 2 distinct, independently
 * taggable objects even though both are the same k8s `kind`. Secrets and
 * Backups are deliberately excluded: Secrets never get a second write path
 * past lib/k8s.ts's own create/delete (this module patches
 * `metadata.labels`, a real mutation, on a resource class the rest of this
 * console treats as sensitive-mutate-never); Backups are Jobs whose name
 * already IS the record (see lib/global-search.ts's own comment) and are
 * routinely garbage-collected by their history limits, so a label on one
 * would not durably tag anything.
 *
 * `TAG_CATEGORY_MIN_ROLE` mirrors lib/global-search.ts's own
 * `CATEGORY_MIN_ROLE` exactly for every category both modules share
 * (service/project/cronjob: viewer; webhook: owner, since a webhook
 * subscription URL is a real exfiltration vector -- same reasoning
 * CATEGORY_MIN_ROLE's own comment documents). `feature-flags` has no
 * Global Search analog (search does not cover Feature Flags at all), so it
 * defaults to the same "member" floor every mutating action in this module
 * already requires -- matching app/api/feature-flags/route.ts's own
 * `requireRole(session, "member")` gate on that ConfigMap.
 */
import { k8sRequest, listAllServices, listConfigMaps, listProjects, type K8sResult } from "@/lib/k8s";
import { listCronJobs, SCHEDULABLE_NAMESPACES } from "@/lib/scheduled-jobs";
import { WEBHOOKS_CONFIGMAP, WEBHOOKS_NAMESPACE } from "@/lib/webhooks";
import { ROLES, type Role } from "@/lib/authz";

// Matches app/feature-flags/page.tsx's and app/api/feature-flags/route.ts's
// own local FLAGS_NAMESPACE/FLAGS_CONFIGMAP constants exactly -- duplicated
// here rather than imported for the same reason lib/global-search.ts's own
// header comment documents for SECRET_NAMESPACES: those two files keep
// them as local, non-exported consts.
const FLAGS_NAMESPACE = "platform-console";
const FLAGS_CONFIGMAP = "platform-feature-flags";

export type TaggableResourceType = "service" | "project" | "cronjob" | "feature-flags" | "webhooks";

export const TAG_LABEL_PREFIX = "platform-console.io/tag-";

const TAG_CATEGORY_MIN_ROLE: Record<TaggableResourceType, Role> = {
  service: "viewer",
  project: "viewer",
  cronjob: "viewer",
  "feature-flags": "member",
  webhooks: "owner",
};

function roleMeets(role: Role, minimum: Role): boolean {
  return ROLES.indexOf(role) >= ROLES.indexOf(minimum);
}

/**
 * The real minimum role required to APPLY (or remove) a tag on one
 * category: at least "member" (every mutating action in this console's
 * app-level RBAC requires at least member -- see lib/authz.ts), raised to
 * that category's own Global-Search-derived minimum when it is higher
 * (webhooks -> owner). Exported so the API route's `requireRole` call
 * enforces exactly this per-category minimum rather than a flat "member"
 * that would under-protect webhooks.
 */
export function minRoleForTagging(type: TaggableResourceType): Role {
  const categoryMin = TAG_CATEGORY_MIN_ROLE[type];
  return ROLES.indexOf(categoryMin) > ROLES.indexOf("member") ? categoryMin : "member";
}

/** The real minimum role required to SEE (browse-by-tag / view current
 * tags on) one category -- identical to lib/global-search.ts's own
 * CATEGORY_MIN_ROLE for every category shared with search. */
export function minRoleForViewing(type: TaggableResourceType): Role {
  return TAG_CATEGORY_MIN_ROLE[type];
}

// A k8s label KEY segment (the part after any `/` prefix) and a label
// VALUE both follow the identical RFC 1123-ish constraint: empty, or 63
// characters or fewer, starting and ending with an alphanumeric, with only
// `-`, `_`, `.`, and alphanumerics in between. Real Kubernetes API
// validation, reproduced here so an invalid tag is rejected with a clear
// 400 before ever reaching the API server (server-side validation is still
// the real backstop -- a malformed PATCH would be rejected there too, this
// is purely a faster, clearer failure).
const LABEL_SEGMENT_RE = /^[A-Za-z0-9]([A-Za-z0-9_.-]{0,61}[A-Za-z0-9])?$/;

function tagLabelKey(key: string): string {
  return `${TAG_LABEL_PREFIX}${key}`;
}

// The `tag-` fragment prepended to every user-supplied key before it
// becomes the label NAME segment (the part after the `platform-
// console.io/` prefix, which is a DNS-subdomain and is never itself
// checked against LABEL_SEGMENT_RE -- a `/` is only valid as the one
// separator between prefix and name, never inside either half).
const TAG_NAME_SEGMENT_PREFIX = "tag-";

/** `null` when valid; otherwise a human-readable reason naming the exact
 * Kubernetes label-name constraint violated. */
export function validateTagKey(key: string): string | null {
  if (!key) return "tag key is required";
  // Real k8s label-key shape: an optional `<dns-subdomain>/` prefix (never
  // validated against LABEL_SEGMENT_RE -- a `/` would fail that regex,
  // it's only ever valid as the prefix/name separator) followed by a name
  // segment that IS validated against it. TAG_LABEL_PREFIX already ends in
  // `/`, so only the part after it (`tag-<key>`) is checked here.
  const nameSegment = `${TAG_NAME_SEGMENT_PREFIX}${key}`;
  if (nameSegment.length > 63) {
    return `tag key too long: "${nameSegment}" is ${nameSegment.length} characters -- the name segment of a Kubernetes label key is limited to 63 characters`;
  }
  if (!LABEL_SEGMENT_RE.test(nameSegment)) {
    return `tag key "${key}" produces an invalid Kubernetes label name segment ("${nameSegment}") -- must start and end with an alphanumeric and contain only letters, digits, '-', '_', or '.'`;
  }
  return null;
}

/** `null` when valid; otherwise a human-readable reason naming the exact
 * Kubernetes label-value constraint violated. */
export function validateTagValue(value: string): string | null {
  if (!value) return "tag value is required";
  if (value.length > 63) {
    return `tag value "${value}" is ${value.length} characters -- Kubernetes label values are limited to 63 characters`;
  }
  if (!LABEL_SEGMENT_RE.test(value)) {
    return `tag value "${value}" is not a valid Kubernetes label value -- must start and end with an alphanumeric and contain only letters, digits, '-', '_', or '.'`;
  }
  return null;
}

export interface ResourceRef {
  namespace: string;
  name: string;
}

function resourcePath(type: TaggableResourceType, ref: ResourceRef): string {
  switch (type) {
    case "service":
      return `/api/v1/namespaces/${encodeURIComponent(ref.namespace)}/services/${encodeURIComponent(ref.name)}`;
    case "project":
      return `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(ref.namespace)}/projects/${encodeURIComponent(ref.name)}`;
    case "cronjob":
      return `/apis/batch/v1/namespaces/${encodeURIComponent(ref.namespace)}/cronjobs/${encodeURIComponent(ref.name)}`;
    case "feature-flags":
      return `/api/v1/namespaces/${FLAGS_NAMESPACE}/configmaps/${FLAGS_CONFIGMAP}`;
    case "webhooks":
      return `/api/v1/namespaces/${WEBHOOKS_NAMESPACE}/configmaps/${WEBHOOKS_CONFIGMAP}`;
  }
}

/** The fixed namespace/name pair backing the 2 singleton ConfigMap
 * categories -- callers of applyTag/removeTag for these 2 types don't need
 * to (and can't meaningfully) supply their own ref. */
export function fixedRefFor(type: "feature-flags" | "webhooks"): ResourceRef {
  return type === "feature-flags"
    ? { namespace: FLAGS_NAMESPACE, name: FLAGS_CONFIGMAP }
    : { namespace: WEBHOOKS_NAMESPACE, name: WEBHOOKS_CONFIGMAP };
}

interface RawObjectMeta {
  metadata: { name: string; namespace: string; labels?: Record<string, string> };
}

/** Strips the `platform-console.io/tag-` prefix off every label that
 * carries it, returning just the tag key/value pairs -- every other real
 * label the object carries (e.g. a CronJob's own `app=platform-scheduled-
 * jobs`) is deliberately never surfaced as a "tag". */
export function extractTags(labels: Record<string, string>): Record<string, string> {
  const tags: Record<string, string> = {};
  for (const [k, v] of Object.entries(labels)) {
    if (k.startsWith(TAG_LABEL_PREFIX)) tags[k.slice(TAG_LABEL_PREFIX.length)] = v;
  }
  return tags;
}

/** Real single-object GET, returning just this object's own tags (already
 * stripped of the `platform-console.io/tag-` prefix). Used by the /tags
 * page's generic "apply tag" form to show what's already on a resource the
 * operator named, without a whole extra list call. */
export async function getResourceTags(
  type: TaggableResourceType,
  ref: ResourceRef,
): Promise<K8sResult<Record<string, string>>> {
  const result = await k8sRequest<RawObjectMeta>(resourcePath(type, ref));
  if (!result.ok) return result;
  return { ok: true, data: extractTags(result.data.metadata.labels ?? {}) };
}

/**
 * PATCHes a real k8s label onto the real object -- a real RFC 7386 merge
 * patch touching only `metadata.labels.<this one key>`, never a full-
 * object PUT, so no other label already on the object (including another
 * tag) is ever disturbed. `key`/`value` are validated against real
 * Kubernetes label-name/label-value constraints before the request is
 * ever sent (see validateTagKey/validateTagValue above).
 */
export async function applyTag(
  resourceType: TaggableResourceType,
  ref: ResourceRef,
  key: string,
  value: string,
): Promise<K8sResult<Record<string, string>>> {
  const keyError = validateTagKey(key);
  if (keyError) return { ok: false, error: keyError };
  const valueError = validateTagValue(value);
  if (valueError) return { ok: false, error: valueError };

  const result = await k8sRequest<RawObjectMeta>(
    resourcePath(resourceType, ref),
    "PATCH",
    { metadata: { labels: { [tagLabelKey(key)]: value } } },
    "application/merge-patch+json",
  );
  if (!result.ok) return result;
  return { ok: true, data: extractTags(result.data.metadata.labels ?? {}) };
}

/**
 * Removes one tag via a real RFC 7386 merge patch setting that one label
 * key's value to `null` -- the merge-patch spec's own key-removal
 * semantics (the API server's merge, not this app's own filtering, is what
 * actually removes it), the same convention lib/webhooks.ts's
 * deleteWebhookSubscription already uses for a ConfigMap `data` key.
 */
export async function removeTag(
  resourceType: TaggableResourceType,
  ref: ResourceRef,
  key: string,
): Promise<K8sResult<Record<string, string>>> {
  const result = await k8sRequest<RawObjectMeta>(
    resourcePath(resourceType, ref),
    "PATCH",
    { metadata: { labels: { [tagLabelKey(key)]: null } } } as unknown as Record<string, unknown>,
    "application/merge-patch+json",
  );
  if (!result.ok) return result;
  return { ok: true, data: extractTags(result.data.metadata.labels ?? {}) };
}

export interface TaggedResource {
  type: TaggableResourceType;
  name: string;
  namespace: string;
  detail: string;
  path: string;
}

function labelSelectorFor(key: string, value: string): string {
  return `${tagLabelKey(key)}=${value}`;
}

async function listServicesByTag(key: string, value: string): Promise<TaggedResource[]> {
  const result = await listAllServices(labelSelectorFor(key, value));
  if (!result.ok) return [];
  return result.data.map((svc) => ({
    type: "service" as const,
    name: svc.name,
    namespace: svc.namespace,
    detail: `${svc.namespace} · Service Discovery`,
    path: "/service-discovery",
  }));
}

async function listProjectsByTag(key: string, value: string): Promise<TaggedResource[]> {
  const result = await listProjects(labelSelectorFor(key, value));
  if (!result.ok) return [];
  return result.data.map((p) => ({
    type: "project" as const,
    name: p.name,
    namespace: p.namespace,
    detail: `${p.namespace} · Projects`,
    path: `/projects/${encodeURIComponent(p.name)}/database`,
  }));
}

async function listCronJobsByTag(key: string, value: string): Promise<TaggedResource[]> {
  const selector = labelSelectorFor(key, value);
  const perNamespace = await Promise.all(
    SCHEDULABLE_NAMESPACES.map(async (namespace) => {
      const result = await listCronJobs(namespace, selector);
      if (!result.ok) return [];
      return result.data.map((job) => ({
        type: "cronjob" as const,
        name: job.name,
        namespace: job.namespace,
        detail: `${job.namespace} · schedule ${job.schedule} · Scheduled Jobs`,
        path: "/scheduled-jobs",
      }));
    }),
  );
  return perNamespace.flat();
}

async function listConfigMapsByTag(key: string, value: string): Promise<TaggedResource[]> {
  const result = await listConfigMaps(FLAGS_NAMESPACE, labelSelectorFor(key, value));
  if (!result.ok) return [];
  const out: TaggedResource[] = [];
  for (const cm of result.data) {
    // Explicit allowlist match on name, never an else-branch guess -- a
    // third, unrelated ConfigMap in this same namespace (e.g.
    // platform-console-org-roles) carrying this label by coincidence must
    // never be misreported as "webhooks" or "feature-flags".
    if (cm.name === FLAGS_CONFIGMAP) {
      out.push({
        type: "feature-flags",
        name: cm.name,
        namespace: cm.namespace,
        detail: `${cm.namespace} · Feature Flags`,
        path: "/feature-flags",
      });
    } else if (cm.name === WEBHOOKS_CONFIGMAP) {
      out.push({
        type: "webhooks",
        name: cm.name,
        namespace: cm.namespace,
        detail: `${cm.namespace} · Webhooks`,
        path: "/webhooks",
      });
    }
  }
  return out;
}

/**
 * Real cross-resource "browse by tag" lookup -- the AWS Resource Groups /
 * GCP Labels filtered-resource-list equivalent. Every category is queried
 * live in parallel via the real k8s API's own `?labelSelector=` query
 * parameter (a genuine server-side filter, never a client-side `.filter()`
 * over every object of that kind), and a category is only ever queried at
 * all when the caller's role meets that category's own
 * `TAG_CATEGORY_MIN_ROLE` -- the exact same role-gated fan-out shape
 * lib/global-search.ts's searchPlatform already established.
 */
export async function listResourcesByTag(
  key: string,
  value: string,
  role: Role,
): Promise<TaggedResource[]> {
  if (validateTagKey(key) || validateTagValue(value)) return [];

  const tasks: Promise<TaggedResource[]>[] = [];
  if (roleMeets(role, TAG_CATEGORY_MIN_ROLE.service)) tasks.push(listServicesByTag(key, value));
  if (roleMeets(role, TAG_CATEGORY_MIN_ROLE.project)) tasks.push(listProjectsByTag(key, value));
  if (roleMeets(role, TAG_CATEGORY_MIN_ROLE.cronjob)) tasks.push(listCronJobsByTag(key, value));

  const wantFeatureFlags = roleMeets(role, TAG_CATEGORY_MIN_ROLE["feature-flags"]);
  const wantWebhooks = roleMeets(role, TAG_CATEGORY_MIN_ROLE.webhooks);
  if (wantFeatureFlags || wantWebhooks) {
    tasks.push(
      listConfigMapsByTag(key, value).then((rs) =>
        rs.filter(
          (r) =>
            (r.type === "feature-flags" && wantFeatureFlags) || (r.type === "webhooks" && wantWebhooks),
        ),
      ),
    );
  }

  const results = await Promise.all(tasks);
  return results.flat();
}
