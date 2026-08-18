/**
 * Real "Infrastructure as Code export" + "drift detection" primitives --
 * the AWS CloudFormation drift-detection / Terraform plan / GCP Deployment
 * Manager equivalent for this console's own self-service Project+Database
 * resources. Everything here reads real, live Kubernetes objects through
 * lib/k8s.ts (never a stored/cached copy) and either serializes them back
 * into real re-appliable YAML (exportProjectManifest) or diffs them
 * against what a fresh `createProjectWithDatabase` call would submit today
 * (detectDrift). Runs on the Node.js runtime only, same constraint as
 * lib/k8s.ts (which this module is built entirely on top of).
 */
import * as yaml from "js-yaml";
import {
  buildProjectManifest,
  buildSingleDatabaseManifest,
  getProject,
  getRawProject,
  getRawSingleDatabase,
  type CreateProjectInput,
  type K8sResult,
  type RawCustomResource,
} from "./k8s";

// Mirrors app/api/projects/route.ts's own default fallback for a caller
// that leaves dbStorageSize blank -- kept here as the single named
// constant both files should stay in sync with (that route's fallback and
// this module's drift baseline are describing the exact same default).
const DEFAULT_DB_STORAGE_SIZE = "1Gi";

// Server-managed annotation keys the create path never sets and that a
// real hand-applied resource (e.g. bootstrapped via `kubectl apply -f`
// before this console existed) can legitimately carry -- excluded from
// both the export and the drift comparison so they never register as
// fabricated "drift" or clutter the exported manifest with something that
// isn't real desired-state input.
const IGNORED_ANNOTATION_KEYS = new Set([
  "kubectl.kubernetes.io/last-applied-configuration",
]);

function significantAnnotations(
  annotations: Record<string, string> | undefined,
): Record<string, string> {
  if (!annotations) return {};
  return Object.fromEntries(
    Object.entries(annotations).filter(([k]) => !IGNORED_ANNOTATION_KEYS.has(k)),
  );
}

// ------------------------------------------------------------------ Export

export interface ProjectManifestExport {
  projectName: string;
  namespace: string;
  generatedAt: string;
  /** Real, re-appliable multi-document YAML: the Project CR, then (if it
   * exists) its SingleDatabase CR, joined with `---`. */
  yaml: string;
  project: RawCustomResource;
  database: RawCustomResource | null;
}

/**
 * Strips server-generated bookkeeping (resourceVersion/uid/generation/
 * creationTimestamp/status/the kubectl last-applied-configuration
 * annotation) from a raw CR the way the removed `kubectl get -o yaml
 * --export` flag used to -- what's left is exactly what a client would
 * submit on a create or update: apiVersion/kind/metadata.{name,namespace,
 * labels,annotations}/spec. `status` is deliberately dropped entirely: it
 * is server-owned (the operator writes it), never legal client input, and
 * a `metadata.resourceVersion` left in place would make the export NOT
 * re-appliable to a create (the API server would reject a stale/foreign
 * resourceVersion on write) -- so leaving either in would silently break
 * the one property this export exists to guarantee.
 */
function toReappliableManifest(cr: RawCustomResource): RawCustomResource {
  const { name, namespace, labels, annotations } = cr.metadata;
  const cleanAnnotations = significantAnnotations(annotations);
  return {
    apiVersion: cr.apiVersion,
    kind: cr.kind,
    metadata: {
      name,
      namespace,
      ...(labels && Object.keys(labels).length ? { labels } : {}),
      ...(Object.keys(cleanAnnotations).length ? { annotations: cleanAnnotations } : {}),
    },
    spec: cr.spec,
  };
}

/**
 * Reads the ACTUAL live Project + SingleDatabase CRs for `projectName` and
 * serializes them back into real, valid, re-appliable YAML -- a genuine
 * "infrastructure as code" export of what's really running (every field
 * the operator itself has since defaulted in), not a re-derived template
 * guess. `database` is `null` (never an error) when the Project's
 * `databaseRef` doesn't resolve to a SingleDatabase that currently exists.
 */
export async function exportProjectManifest(
  projectName: string,
): Promise<K8sResult<ProjectManifestExport>> {
  const summary = await getProject(projectName);
  if (!summary.ok) return summary;
  if (!summary.data) {
    return { ok: false, error: `project '${projectName}' not found` };
  }
  const { namespace, databaseRefName } = summary.data;

  const rawProject = await getRawProject(namespace, projectName);
  if (!rawProject.ok) return rawProject;
  if (!rawProject.data) {
    return { ok: false, error: `project '${projectName}' not found in namespace ${namespace}` };
  }

  const rawDb = databaseRefName
    ? await getRawSingleDatabase(namespace, databaseRefName)
    : ({ ok: true, data: null } as K8sResult<RawCustomResource | null>);
  if (!rawDb.ok) return rawDb;

  const project = toReappliableManifest(rawProject.data);
  const database = rawDb.data ? toReappliableManifest(rawDb.data) : null;

  const docs = [project, ...(database ? [database] : [])];
  const yamlText = docs
    .map((doc) => yaml.dump(doc, { noRefs: true, lineWidth: -1, sortKeys: false }))
    .join("---\n");

  return {
    ok: true,
    data: {
      projectName,
      namespace,
      generatedAt: new Date().toISOString(),
      yaml: yamlText,
      project,
      database,
    },
  };
}

// ------------------------------------------------------------------ Drift

export interface DriftEntry {
  resource: "Project" | "SingleDatabase";
  /** Dot path within the resource, e.g. `spec.databaseRef.name` or
   * `metadata.labels`. */
  path: string;
  /** What a fresh createProjectWithDatabase call would submit here today. */
  desired: unknown;
  /** What the live object actually has at this path (`null` when absent). */
  actual: unknown;
}

export interface DriftReport {
  projectName: string;
  namespace: string;
  generatedAt: string;
  /** The exact inputs used to reconstruct the desired baseline -- shown so
   * a reader can see precisely which "fresh call" this drift report is
   * comparing against, same transparency principle as `terraform plan`
   * printing the plan it diffed against. */
  desiredInputs: CreateProjectInput;
  drift: DriftEntry[];
  hasDrift: boolean;
}

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

/**
 * Walks every leaf of `desired` and compares it against the same path in
 * `actual`, appending a DriftEntry for each mismatch. Deliberately a
 * SUBSET walk driven by `desired`'s own keys, never `actual`'s: `actual`
 * (a real reconciled CR) legitimately carries dozens of fields the create
 * path never sets at all (the CRD's own server-side defaults -- e.g.
 * `spec.auth.replicas`, `spec.rest.dbMaxRows`) and those are not drift,
 * they are the operator doing its job. Only fields this platform's own
 * create path actually populates are load-bearing "desired state" here.
 */
function diffSubset(
  resource: DriftEntry["resource"],
  desired: Record<string, unknown>,
  actual: Record<string, unknown> | undefined,
  pathPrefix: string,
  out: DriftEntry[],
): void {
  for (const [key, desiredValue] of Object.entries(desired)) {
    const path = pathPrefix ? `${pathPrefix}.${key}` : key;
    const actualValue = actual ? actual[key] : undefined;
    if (isPlainObject(desiredValue)) {
      diffSubset(
        resource,
        desiredValue,
        isPlainObject(actualValue) ? actualValue : undefined,
        path,
        out,
      );
      continue;
    }
    if (JSON.stringify(desiredValue) !== JSON.stringify(actualValue)) {
      out.push({ resource, path, desired: desiredValue, actual: actualValue ?? null });
    }
  }
}

function diffMetadata(
  resource: DriftEntry["resource"],
  live: RawCustomResource["metadata"],
  out: DriftEntry[],
): void {
  // The create path never sets labels or annotations on either CR, so the
  // desired baseline for both is empty -- any real label/annotation found
  // live (after filtering the ignored system-managed keys above) is a
  // genuine hand-edit the create path could not have produced.
  const liveLabels = live.labels ?? {};
  if (Object.keys(liveLabels).length > 0) {
    out.push({ resource, path: "metadata.labels", desired: {}, actual: liveLabels });
  }
  const liveAnnotations = significantAnnotations(live.annotations);
  if (Object.keys(liveAnnotations).length > 0) {
    out.push({ resource, path: "metadata.annotations", desired: {}, actual: liveAnnotations });
  }
}

/**
 * Compares the live Project + SingleDatabase CRs' current spec against
 * what a fresh `createProjectWithDatabase` call would submit for
 * `projectName` today, using the same default-derivation
 * `app/api/projects/route.ts` applies when a caller leaves a field blank
 * (`databaseRefName` -> `${name}-db`, `hostname` -> `${name}.supabase.
 * local`, `protocol` -> `http`, `dbStorageSize` -> `1Gi`). This is
 * deliberately NOT re-derived from the live object itself -- if it were,
 * a hand-edited field would just get echoed back as its own "desired"
 * value and no drift could ever be detected in it. Reports every real
 * field-level difference between that reconstructed manifest and the live
 * spec (e.g. someone hand-editing `dbStorageSize`, or adding a label /
 * annotation via `kubectl patch` that the create path never sets), plus
 * whether the live objects even exist. A Project bootstrapped outside this
 * console's own create path (e.g. applied directly via `kubectl apply`
 * with a custom `databaseRefName` or `studio.orgName`) will honestly show
 * that mismatch too -- that is real, true drift relative to what this
 * platform's create flow would produce for a project of this name, not a
 * false positive.
 */
export async function detectDrift(projectName: string): Promise<K8sResult<DriftReport>> {
  const summary = await getProject(projectName);
  if (!summary.ok) return summary;
  if (!summary.data) {
    return { ok: false, error: `project '${projectName}' not found` };
  }
  const { namespace, databaseRefName } = summary.data;

  const rawProject = await getRawProject(namespace, projectName);
  if (!rawProject.ok) return rawProject;
  if (!rawProject.data) {
    return { ok: false, error: `project '${projectName}' not found in namespace ${namespace}` };
  }

  const desiredInputs: CreateProjectInput = {
    name: projectName,
    namespace,
    databaseRefName: `${projectName}-db`,
    hostname: `${projectName}.supabase.local`,
    protocol: "http",
    dbStorageSize: DEFAULT_DB_STORAGE_SIZE,
  };
  const desiredProject = buildProjectManifest(desiredInputs);
  const desiredDb = buildSingleDatabaseManifest({
    name: desiredInputs.databaseRefName,
    namespace,
    storageSize: desiredInputs.dbStorageSize,
  });

  const drift: DriftEntry[] = [];
  diffSubset("Project", desiredProject.spec, rawProject.data.spec, "spec", drift);
  diffMetadata("Project", rawProject.data.metadata, drift);

  const resolvedDbName = databaseRefName ?? desiredInputs.databaseRefName;
  const rawDb = await getRawSingleDatabase(namespace, resolvedDbName);
  if (!rawDb.ok) return rawDb;

  if (!rawDb.data) {
    drift.push({
      resource: "SingleDatabase",
      path: "(existence)",
      desired: `SingleDatabase/${resolvedDbName} exists`,
      actual: "not found",
    });
  } else {
    diffSubset("SingleDatabase", desiredDb.spec, rawDb.data.spec, "spec", drift);
    diffMetadata("SingleDatabase", rawDb.data.metadata, drift);
  }

  return {
    ok: true,
    data: {
      projectName,
      namespace,
      generatedAt: new Date().toISOString(),
      desiredInputs,
      drift,
      hasDrift: drift.length > 0,
    },
  };
}
