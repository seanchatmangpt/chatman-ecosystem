import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import ApplyMigrationForm from "@/components/ApplyMigrationForm";
import RollbackMigrationButton from "@/components/RollbackMigrationButton";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { listMigrations } from "@/lib/migrations";
import { getProject, hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Real AWS RDS "schema management" / GCP Cloud SQL / Supabase migrations-
// tool equivalent, self-service and distinct from the existing Backups
// module (full pg_dump/restore): lets an operator apply/track/rollback
// real, versioned SQL changes against THIS project's own live Postgres,
// one statement pair at a time, via lib/migrations.ts. Owner-gated (same
// boundary as /audit and /org) -- arbitrary DDL/DML against a project's
// live schema is exactly the kind of consequential action that boundary
// exists for; the real enforcement is /api/projects/[name]/migrations'
// own server-side requireRole("owner") call, this page's check is the UI
// mirror of it.
export default async function ProjectMigrationsPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const projectResult = await getProject(name);
  const clusterConfigured = hasClusterCredentials();

  const shell = (body: React.ReactNode) => (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-1 text-2xl font-semibold text-white">{name}</h1>
        {projectResult.ok && projectResult.data && (
          <p className="mb-6 text-sm text-gray-500">
            namespace <code>{projectResult.data.namespace}</code>
          </p>
        )}
        <ProjectSubNav name={name} active="migrations" />
        {body}
      </main>
    </>
  );

  if (!session) {
    return shell(
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        unauthenticated
      </p>,
    );
  }

  if (!projectResult.ok || !projectResult.data) {
    return shell(
      <p className="text-sm text-gray-400">
        {!projectResult.ok ? projectResult.error : "Project not found."}
      </p>,
    );
  }

  if (!clusterConfigured) {
    return shell(
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        not configured: no in-cluster ServiceAccount credentials found. This page only returns
        real data when running as the platform-console pod.
      </div>,
    );
  }

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    return shell(
      <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        <p className="font-medium">403 -- forbidden</p>
        <p className="mt-1 text-red-300/80">
          Your role (<code>{access.role}</code>) does not meet the required minimum role (
          <code>owner</code>) for schema migrations.
        </p>
      </div>,
    );
  }

  const migrationsResult = await listMigrations(name);
  const migrations = migrationsResult.ok ? migrationsResult.data : [];

  return shell(
    <>
      <p className="mb-8 max-w-2xl text-sm text-gray-400">
        The RDS/Cloud SQL schema-management equivalent for this project&apos;s real Postgres --
        distinct from <code>Backups</code> (full dump/restore): applies real versioned SQL
        against <code>{name}</code>&apos;s own live database. &quot;Apply migration&quot; runs
        your up SQL inside a real transaction and only records the row in{" "}
        <code>platform_console.schema_migrations</code> if it fully succeeds -- any real SQL
        error rolls the whole transaction back, so a failed migration never leaves a
        half-applied schema change. Rollback replays the migration&apos;s own stored down SQL,
        also inside one real transaction.
      </p>

      <div className="mb-6 card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Migration history</h2>

        {!migrationsResult.ok && (
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
            {migrationsResult.error}
          </p>
        )}

        {migrationsResult.ok && migrations.length === 0 && (
          <p className="text-sm text-gray-500">No migrations applied yet. Submit one below.</p>
        )}

        {migrationsResult.ok && migrations.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-gray-500">
                  <th className="py-2 pr-4 font-medium">Version</th>
                  <th className="py-2 pr-4 font-medium">Name</th>
                  <th className="py-2 pr-4 font-medium">Applied</th>
                  <th className="py-2 pr-4 font-medium">Checksum</th>
                  <th className="py-2 pr-4 font-medium">Rollback</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {migrations.map((m) => (
                  <tr key={m.version}>
                    <td className="py-2 pr-4">
                      <code className="text-white">{m.version}</code>
                    </td>
                    <td className="py-2 pr-4 text-gray-300">{m.name}</td>
                    <td className="py-2 pr-4 text-gray-400">
                      {new Date(m.appliedAt).toLocaleString()}
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs text-gray-500">
                      {m.checksum.slice(0, 12)}...
                    </td>
                    <td className="py-2 pr-4">
                      <RollbackMigrationButton projectName={name} version={m.version} name={m.name} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card p-6">
        <h2 className="mb-3 text-base font-medium text-white">Apply a new migration</h2>
        <p className="mb-4 text-xs text-gray-500">
          Submits a real up/down SQL pair to <code>/api/projects/{name}/migrations</code> -&gt;{" "}
          <code>lib/migrations.ts</code>&apos;s <code>applyMigration</code>, which runs your up
          SQL against the live database via the console&apos;s own Postgres connection (the same
          credential-discovery pattern the Backups and Audit Log modules already use).
        </p>
        <ApplyMigrationForm projectName={name} />
      </div>
    </>,
  );
}
