/**
 * Global Search / Command Palette (AWS resource search / GCP Cloud
 * Console search bar equivalent): real cross-resource lookup, run live
 * against the exact same lib functions every individual module already
 * calls -- never a client-side static index, never a separate search
 * service or precomputed cache that could drift from the live cluster.
 *
 * Every category below is queried in parallel via the real k8s API (or,
 * for webhook subscriptions, the real backing ConfigMap), and results
 * are only ever included for a category the caller's role can already
 * read on that category's own page/route -- see CATEGORY_MIN_ROLE.
 * Secrets follow the exact never-render-values discipline
 * app/secrets/page.tsx documents: only Secret NAMES and KEY NAMES are
 * ever matched or returned, decoded values are never read.
 */
import {
  getProjectDatabasePod,
  listAllServices,
  listJobs,
  listProjects,
  listSecrets,
  type SupabaseProject,
} from "@/lib/k8s";
import { listCronJobs, SCHEDULABLE_NAMESPACES } from "@/lib/scheduled-jobs";
import { listWebhookSubscriptions } from "@/lib/webhooks";
import { ROLES, type Role } from "@/lib/authz";

// The platform's own namespaces only -- identical list to
// app/secrets/page.tsx's PLATFORM_NAMESPACES (and to the per-namespace
// Role+RoleBinding pairs granted in k8s/paas-rbac.yaml's Secrets Manager
// section). Duplicated here rather than imported because the page file
// keeps it as a local, non-exported const -- same duplication convention
// lib/scheduled-jobs.ts's own comment already documents for
// SCHEDULABLE_NAMESPACES.
const SECRET_NAMESPACES = ["autofde-lab", "gymact", "ggen", "ggen-marketplace", "supabase-demo"];

export type SearchResultType = "service" | "project" | "secret" | "cronjob" | "backup" | "webhook";

export interface SearchResult {
  type: SearchResultType;
  /** The matched resource's own identifier (Service name, Project name, Secret name, ...). */
  name: string;
  /** Short human context shown under the name (namespace, event type, ...). */
  detail: string;
  /** Where clicking this result navigates to. */
  path: string;
}

/**
 * The minimum app-level role (lib/authz.ts) required to see a given
 * category in search results -- set to exactly the same minimum each
 * category's own read path (page or GET route) already enforces today,
 * so search can never surface a resource a session couldn't otherwise
 * see:
 *  - service/project/secret/cronjob/backup: their own GET routes
 *    (app/api/secrets, app/api/scheduled-jobs, .../backups) and pages
 *    only call requireSession, no requireRole -- readable by any
 *    authenticated role.
 *  - webhook: GET /api/webhooks is requireRole(session, "owner") --
 *    subscription URLs are a real exfiltration vector (see
 *    app/api/webhooks/route.ts), so search matches that exactly.
 */
const CATEGORY_MIN_ROLE: Record<SearchResultType, Role> = {
  service: "viewer",
  project: "viewer",
  secret: "viewer",
  cronjob: "viewer",
  backup: "viewer",
  webhook: "owner",
};

function roleMeets(role: Role, minimum: Role): boolean {
  return ROLES.indexOf(role) >= ROLES.indexOf(minimum);
}

function includesQuery(value: string, q: string): boolean {
  return value.toLowerCase().includes(q);
}

async function searchServices(q: string): Promise<SearchResult[]> {
  const result = await listAllServices();
  if (!result.ok) return [];
  return result.data
    .filter((svc) => includesQuery(svc.name, q))
    .map((svc) => ({
      type: "service" as const,
      name: svc.name,
      detail: `${svc.namespace} · Service Discovery`,
      path: "/service-discovery",
    }));
}

async function searchProjects(q: string): Promise<SearchResult[]> {
  const result = await listProjects();
  if (!result.ok) return [];
  return result.data
    .filter((p) => includesQuery(p.name, q))
    .map((p) => ({
      type: "project" as const,
      name: p.name,
      detail: `${p.namespace} · Projects`,
      path: `/projects/${encodeURIComponent(p.name)}/database`,
    }));
}

async function searchSecrets(q: string): Promise<SearchResult[]> {
  const perNamespace = await Promise.all(
    SECRET_NAMESPACES.map(async (namespace) => {
      const result = await listSecrets(namespace);
      if (!result.ok) return [];
      return result.data
        .filter((s) => includesQuery(s.name, q) || s.keys.some((k) => includesQuery(k, q)))
        .map((s) => ({
          type: "secret" as const,
          name: s.name,
          detail: `${s.namespace} · keys: ${s.keys.join(", ") || "(none)"} · Secrets`,
          path: "/secrets",
        }));
    }),
  );
  return perNamespace.flat();
}

async function searchCronJobs(q: string): Promise<SearchResult[]> {
  const perNamespace = await Promise.all(
    SCHEDULABLE_NAMESPACES.map(async (namespace) => {
      const result = await listCronJobs(namespace);
      if (!result.ok) return [];
      return result.data
        .filter((job) => includesQuery(job.name, q))
        .map((job) => ({
          type: "cronjob" as const,
          name: job.name,
          detail: `${job.namespace} · schedule ${job.schedule} · Scheduled Jobs`,
          path: "/scheduled-jobs",
        }));
    }),
  );
  return perNamespace.flat();
}

/**
 * Mirrors app/api/projects/[name]/backups/route.ts's own lookup exactly:
 * resolve each real Project's database Pod, then list only THAT
 * project's own backup Jobs (`app=platform-backups,database=<stem>`) --
 * the same cross-tenant guard the Backups module itself relies on, so
 * search never attributes one project's backup Job to another project
 * sharing its namespace.
 */
async function searchBackupsForProject(
  project: SupabaseProject,
  q: string,
): Promise<SearchResult[]> {
  const podResult = await getProjectDatabasePod(project);
  if (!podResult.ok || !podResult.data) return [];
  const { namespace, serviceName } = podResult.data;
  const jobsResult = await listJobs(namespace, `app=platform-backups,database=${serviceName}`);
  if (!jobsResult.ok) return [];
  return jobsResult.data
    .filter((job) => includesQuery(job.name, q))
    .map((job) => ({
      type: "backup" as const,
      name: job.name,
      detail: `${project.name} (${namespace}) · ${job.status} · Backups`,
      path: `/projects/${encodeURIComponent(project.name)}/backups`,
    }));
}

async function searchBackups(q: string): Promise<SearchResult[]> {
  const projectsResult = await listProjects();
  if (!projectsResult.ok) return [];
  const perProject = await Promise.all(
    projectsResult.data.map((project) => searchBackupsForProject(project, q)),
  );
  return perProject.flat();
}

async function searchWebhooks(q: string): Promise<SearchResult[]> {
  const result = await listWebhookSubscriptions();
  if (!result.ok) return [];
  return result.data
    .filter(
      (s) => includesQuery(s.id, q) || includesQuery(s.url, q) || includesQuery(s.eventType, q),
    )
    .map((s) => ({
      type: "webhook" as const,
      name: s.url,
      detail: `${s.eventType} · Webhooks`,
      path: "/webhooks",
    }));
}

/**
 * Real cross-resource lookup, run live in parallel against every
 * category the caller's role may read. Case-insensitive substring match
 * against each resource's own name/identifier (and, for Secrets, its key
 * names -- never its values). Not a client-side static index: every call
 * re-queries the real k8s API / real webhooks ConfigMap.
 */
export async function searchPlatform(query: string, role: Role): Promise<SearchResult[]> {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const tasks: Promise<SearchResult[]>[] = [];
  if (roleMeets(role, CATEGORY_MIN_ROLE.service)) tasks.push(searchServices(q));
  if (roleMeets(role, CATEGORY_MIN_ROLE.project)) tasks.push(searchProjects(q));
  if (roleMeets(role, CATEGORY_MIN_ROLE.secret)) tasks.push(searchSecrets(q));
  if (roleMeets(role, CATEGORY_MIN_ROLE.cronjob)) tasks.push(searchCronJobs(q));
  if (roleMeets(role, CATEGORY_MIN_ROLE.backup)) tasks.push(searchBackups(q));
  if (roleMeets(role, CATEGORY_MIN_ROLE.webhook)) tasks.push(searchWebhooks(q));

  const results = await Promise.all(tasks);
  return results.flat();
}
