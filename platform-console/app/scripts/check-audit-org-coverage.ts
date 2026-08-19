/**
 * CI-checkable coverage sweep: every `writeAuditLogEntry({...})` call site
 * under app/api MUST either (a) pass `orgId` in the entry object, or
 * (b) live in a route file that carries an explicit
 * `// org-agnostic: ...` marker comment justifying why no per-tenant org
 * boundary applies (health checks, platform-admin listings, and every
 * route in this console's current data model that operates on the single
 * platform namespace rather than a per-customer org -- see
 * lib/orgs.ts's own header comment on the scope of "org" here).
 *
 * This is the regression guard for the org_id audit-log coverage sweep:
 * before this pass, 86 of 107 files calling writeAuditLogEntry never
 * passed orgId, so most rows were NULL and invisible to org-scoped SIEM
 * exports (GET /api/v1/audit-export), DSAR searches, and retention-purge
 * jobs that filter on org_id. This script fails the build the moment a
 * NEW writeAuditLogEntry call site is added without either orgId or the
 * explicit marker, so that gap cannot silently reopen.
 *
 * Usage: `npx tsx scripts/check-audit-org-coverage.ts` from app/, or wire
 * into CI as `npm run check:audit-org-coverage`. Exits 1 (with the full
 * list of offending file:line locations) on any uncovered call site,
 * 0 otherwise.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const APP_API_ROOT = join(__dirname, "..", "app", "api");
const ORG_AGNOSTIC_MARKER = "org-agnostic:";

/**
 * Files (relative to app/api, POSIX-style) that are allowed to have
 * writeAuditLogEntry call sites without `orgId`, and WHY -- each one is
 * required to carry a matching `// org-agnostic: ...` comment in the file
 * itself (checked below), so this list and the in-file marker can never
 * drift apart silently. Grouped by the reason category from the sweep.
 */
const ALLOWLIST: Record<string, string> = {
  // ---- Auth/session bootstrap: no org is resolvable yet at this point in the flow
  "auth/gotrue-signup/route.ts": "pre-session identity bootstrap, no org resolved yet",
  "auth/gotrue-login/route.ts": "pre-session identity bootstrap, no org resolved yet",
  "auth/oidc-login/route.ts": "pre-session identity bootstrap, no org resolved yet",
  "auth/oidc-callback/route.ts": "pre-session identity bootstrap, no org resolved yet",
  "login/route.ts": "pre-session identity bootstrap, no org resolved yet",
  "org-invites/route.ts": "invite acceptance mints a session before any org role exists on it",

  // ---- Platform-admin / single-tenant-namespace routes: this console's
  // current data model has no per-customer-org boundary on these --
  // they operate on the one platform-console namespace or on a fixed
  // platform-namespace roster, not a customer org from lib/orgs.ts's
  // registry (see that module's own header comment on scope).
  "scheduled-jobs/route.ts": "platform-wide job listing, no per-org scope",
  "privacy/download/route.ts": "signed-URL download route, deliberately unauthenticated/unscoped",
  "openclaw-catalog/route.ts": "platform-wide catalog read, no per-org scope",
  "org/roles/route.ts": "platform-namespace role assignment, not a customer-org boundary",
  "custom-domains/route.ts": "platform-namespace resource, no per-org scope",
  "budget-alerts/route.ts": "fixed platform-namespace roster, not the orgs registry",
  "secrets/route.ts": "platform-namespace secrets, no per-org scope",
  "feature-flags/route.ts": "platform-wide flag state, no per-org scope",
  "admin/referrals/route.ts": "platform-admin listing across all referrals",
  "contract-renewals/route.ts": "platform-admin listing across all orgs' renewal records",
  "certificates/route.ts": "platform-namespace certificates, no per-org scope",
  "api-keys/route.ts": "platform-namespace API keys, no per-org scope",
  "api-keys/[id]/rate-limit/route.ts": "platform-namespace API key, no per-org scope",
  "orgs/route.ts": "platform-admin org listing/creation itself, precedes any single org",
  "tags/route.ts": "platform-namespace resource tags, no per-org scope",
  "alerts/route.ts": "platform-wide alert listing, no per-org scope",
  "search/route.ts": "platform-wide search across resource kinds, no per-org scope",
  "security-scan/route.ts": "platform-namespace scan, no per-org scope",
  "support/impersonate/route.ts": "the impersonation action is tagged via impersonatedBy/impersonationSessionId, and the target org is the platform-console operator's own -- see lib/audit-db.ts's dedicated columns",
  "logs/route.ts": "arbitrary-namespace pod log tail, not scoped to the orgs registry",
  "audit/verify/route.ts": "verifies the whole platform-wide hash chain, not one org's slice",
  "batch-jobs/route.ts": "platform-namespace batch jobs, no per-org scope",
  "audit/export/route.ts": "bulk platform-wide export path (distinct from the org-scoped GET /api/v1/audit-export)",
  "sessions/route.ts": "platform-namespace active sessions, no per-org scope",
  "castle/route.ts": "platform-namespace Castle listing, no per-org scope",
  "castle/sunset/route.ts": "platform-namespace Castle sunset action, no per-org scope",
  "castle/deploy/route.ts": "platform-namespace Castle deploy action, no per-org scope",
  "castle/schedule/route.ts": "platform-namespace Castle scheduling, no per-org scope",
  "castle/schedule/run-due/route.ts": "cron-fired sweep across every namespace's due schedules",
  "dashboards/route.ts": "platform-namespace dashboards, no per-org scope",
  "cost-anomaly/route.ts": "fixed platform-namespace roster, not the orgs registry",
  "quota-enforcement/route.ts": "fixed platform-namespace roster, not the orgs registry",
  "exec/route.ts": "arbitrary-namespace pod exec, not scoped to the orgs registry",
  "plan-state/route.ts": "platform-namespace ResourceQuota plan state, no per-org scope",
  "webhooks/route.ts": "platform-namespace webhook subscriptions, no per-org scope",
  "webhooks/[id]/deliveries/route.ts": "webhook subscription id is not an org id in this data model",
  "webhooks/deliveries/[deliveryId]/replay/route.ts": "delivery id is not an org id in this data model",
  "webhooks/deliveries/[deliveryId]/attempts/route.ts": "delivery id is not an org id in this data model",
  "gymact-kernel/route.ts": "platform-namespace GymAct kernel action, no per-org scope",
  "prometheus/route.ts": "platform-namespace Prometheus proxy, no per-org scope",
  "approvals/route.ts": "platform-namespace maker-checker approvals, no per-org scope",
  "approvals/[id]/route.ts": "approval id is not an org id in this data model",
  "billing/stripe/webhook/route.ts": "inbound Stripe webhook, org resolved indirectly via customer metadata, not this route's own params",
  "billing/stripe/change-plan/route.ts": "fixed platform-namespace roster, not the orgs registry",
  "billing/overage/route.ts": "fixed platform-namespace roster, not the orgs registry",
  "billing/route.ts": "fixed platform-namespace roster, not the orgs registry",
  "billing/stripe/checkout/route.ts": "fixed platform-namespace roster, not the orgs registry",
  "cron/retention-purge/route.ts": "cron-fired sweep across the whole platform-console namespace's audit log",
  "deployments/canary/route.ts": "platform-namespace canary deployment, no per-org scope",

  // ---- Projects: a project lives in a k8s namespace (its own or an
  // org's), but lib/k8s.ts's Project type carries no orgId field today --
  // see lib/orgs.ts's header comment ("no concept of a second customer
  // org" for this console's own default namespace). Threading a real
  // orgId through these would require a project->org join this codebase
  // does not yet have; tracked as follow-up, not invented here.
  "projects/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/migrations/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/promote/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/cache/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/storage/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/queue/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/storage/download/route.ts": "signed-URL download route, deliberately unauthenticated/unscoped",
  "projects/[name]/iac/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/export-all/download/route.ts": "signed-URL download route, deliberately unauthenticated/unscoped",
  "projects/[name]/tier/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/export-all/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/functions/invoke/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/quota/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/backups/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "projects/[name]/budget/route.ts": "Project has no orgId field in this data model (see lib/orgs.ts)",
  "load-test/route.ts": "load-test target is an arbitrary namespace, not scoped to the orgs registry",
  "security-scan/auto-remediate/route.ts":
    "fans out across every opted-in org's findings in one run, not a single orgId",
};

interface CallSite {
  file: string; // relative to app/api, POSIX-style
  line: number; // 1-indexed
  hasOrgId: boolean;
}

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      walk(full, out);
    } else if (entry === "route.ts") {
      out.push(full);
    }
  }
  return out;
}

/**
 * Finds every `writeAuditLogEntry({ ... })` call in `source` and reports
 * whether its object literal contains an `orgId` key -- real brace
 * balancing (not a naive regex across the whole file), so a call whose
 * object body happens to omit orgId is never confused with a later,
 * unrelated `orgId` appearing elsewhere in the file.
 */
function findCallSites(source: string): { line: number; hasOrgId: boolean }[] {
  const sites: { line: number; hasOrgId: boolean }[] = [];
  const marker = "writeAuditLogEntry({";
  let i = 0;
  while (true) {
    const idx = source.indexOf(marker, i);
    if (idx === -1) break;
    const start = idx + marker.length;
    let depth = 1;
    let j = start;
    while (depth > 0 && j < source.length) {
      if (source[j] === "{") depth++;
      else if (source[j] === "}") depth--;
      j++;
    }
    const body = source.slice(start, j - 1);
    const line = source.slice(0, idx).split("\n").length;
    // A call site is also covered when its object literal opens with an
    // inline `// org-agnostic: ...` comment justifying the omission right
    // at that specific call (e.g. a 403 branch that fires before the
    // route has parsed enough of the request to know its org yet, in a
    // file whose other call sites DO pass a real orgId) -- distinct from
    // the file-level ALLOWLIST below, which covers a file where NO call
    // site can ever resolve an org.
    const hasInlineMarker = new RegExp(`^\\s*//\\s*${ORG_AGNOSTIC_MARKER}`).test(body);
    sites.push({ line, hasOrgId: /\borgId\s*:/.test(body) || hasInlineMarker });
    i = j;
  }
  return sites;
}

function main(): void {
  const files = walk(APP_API_ROOT);
  const violations: string[] = [];
  let totalCalls = 0;
  let coveredCalls = 0;

  for (const absPath of files) {
    const source = readFileSync(absPath, "utf8");
    if (!source.includes("writeAuditLogEntry(")) continue;

    const relPath = relative(APP_API_ROOT, absPath).split("\\").join("/");
    const sites = findCallSites(source);
    if (sites.length === 0) continue;

    totalCalls += sites.length;
    coveredCalls += sites.filter((s) => s.hasOrgId).length;

    const missing = sites.filter((s) => !s.hasOrgId);
    if (missing.length === 0) continue;

    const allowReason = ALLOWLIST[relPath];
    if (allowReason) {
      if (!source.includes(ORG_AGNOSTIC_MARKER)) {
        violations.push(
          `app/api/${relPath}: allowlisted ("${allowReason}") but missing the required ` +
            `"// ${ORG_AGNOSTIC_MARKER} ..." marker comment`,
        );
      }
      continue;
    }

    for (const site of missing) {
      violations.push(`app/api/${relPath}:${site.line}: writeAuditLogEntry call missing orgId`);
    }
  }

  console.log(
    `audit-org-coverage: ${coveredCalls}/${totalCalls} writeAuditLogEntry call sites pass orgId ` +
      `(remainder covered by ${Object.keys(ALLOWLIST).length}-entry allowlist)`,
  );

  if (violations.length > 0) {
    console.error(`\naudit-org-coverage: ${violations.length} uncovered call site(s):\n`);
    for (const v of violations) console.error(`  - ${v}`);
    console.error(
      `\nEither add orgId to the entry (resolved the same way the route already resolves its org), ` +
        `or add both a "// ${ORG_AGNOSTIC_MARKER} ..." comment in the file and an entry in ALLOWLIST here.`,
    );
    process.exitCode = 1;
    return;
  }

  console.log("audit-org-coverage: OK");
}

main();
