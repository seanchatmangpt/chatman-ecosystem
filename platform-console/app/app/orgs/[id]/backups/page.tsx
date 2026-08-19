import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg, getOrgProjectTier } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import {
  listBackupRecords,
  syncBackupRecordStatus,
  getBackupPolicy,
  RETENTION_DEFAULT_DAYS,
  RETENTION_RANGE,
} from "@/lib/backup-retention";
import BackupRetentionPanel from "@/components/BackupRetentionPanel";

export const dynamic = "force-dynamic";

// Real backup-history + retention-policy settings page for one org: the
// compliance-evidence surface lib/backup-retention.ts's own module doc
// names (a provable "which backup, when, how large, expires when" list)
// plus the maker-checker-gated selector to change the retention window
// within this org's tier's allowed range. Server component gates
// rendering the same way app/orgs/[id]/impersonation/page.tsx already
// does: a non-member sees a real 403 message, not the table; every
// underlying read/write is re-checked by its own route handler
// regardless of what this page renders.

export default async function OrgBackupsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const clusterConfigured = hasClusterCredentials();

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const orgResult = await getOrg(id);
  if (!orgResult.ok || !orgResult.data) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {orgResult.ok ? "org not found" : orgResult.error}
          </p>
        </main>
      </>
    );
  }
  const org = orgResult.data;

  const viewerAccess = await requireRoleIn(session, org.namespace, "viewer");
  const ownerAccess = await requireRoleIn(session, org.namespace, "owner");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Backups &amp; retention</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real, tiered backup-retention evidence for this org: every <code>pg_dump</code> Job taken
          against this org&apos;s projects, when it was taken, how large the dump is, and the exact
          date it expires under the org&apos;s current retention policy -- compliance evidence for
          regulatory windows like a 7-year financial-record or HIPAA retention requirement.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only returns
            real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && !viewerAccess.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{viewerAccess.role}</code>) does not meet the required minimum role
              (<code>viewer</code>) to view this org&apos;s backups.
            </p>
          </div>
        )}

        {clusterConfigured && viewerAccess.ok && (
          <BackupsSection orgId={id} namespace={org.namespace} canManage={ownerAccess.ok} />
        )}
      </main>
    </>
  );
}

async function BackupsSection({
  orgId,
  namespace,
  canManage,
}: {
  orgId: string;
  namespace: string;
  canManage: boolean;
}) {
  const [tierResult, policyResult, recordsResult] = await Promise.all([
    getOrgProjectTier(namespace),
    getBackupPolicy(orgId),
    listBackupRecords(orgId),
  ]);

  if (!tierResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read org tier: {tierResult.error}
      </p>
    );
  }
  if (!policyResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read backup policy: {policyResult.error}
      </p>
    );
  }
  if (!recordsResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read backup history: {recordsResult.error}
      </p>
    );
  }

  const tier = tierResult.data;
  const retentionDays = policyResult.data?.retentionDays ?? RETENTION_DEFAULT_DAYS[tier];

  const now = Date.now();
  const backups = [];
  for (const record of recordsResult.data) {
    const synced = await syncBackupRecordStatus(record);
    const r = synced.ok ? synced.data : record;
    backups.push({
      id: r.id,
      jobName: r.jobName,
      projectName: r.projectName,
      takenAt: r.takenAt,
      sizeBytes: r.sizeBytes,
      retainUntil: r.retainUntil,
      status: r.status,
      ageDays: Math.floor((now - Date.parse(r.takenAt)) / (24 * 60 * 60 * 1000)),
      daysUntilExpiry: Math.ceil((Date.parse(r.retainUntil) - now) / (24 * 60 * 60 * 1000)),
    });
  }

  return (
    <BackupRetentionPanel
      orgId={orgId}
      canManage={canManage}
      initialTier={tier}
      initialRetentionDays={retentionDays}
      initialAllowedRange={RETENTION_RANGE[tier]}
      initialBackups={backups}
    />
  );
}
