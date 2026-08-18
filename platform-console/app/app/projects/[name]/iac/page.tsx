import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import ManifestActions from "@/components/ManifestActions";
import { hasClusterCredentials } from "@/lib/k8s";
import { detectDrift, exportProjectManifest, type DriftEntry } from "@/lib/iac";

export const dynamic = "force-dynamic";

function DriftValue({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return <span className="italic text-gray-600">(absent)</span>;
  }
  if (typeof value === "object") {
    return <code className="text-white">{JSON.stringify(value)}</code>;
  }
  return <code className="text-white">{String(value)}</code>;
}

function DriftRow({ entry }: { entry: DriftEntry }) {
  return (
    <tr>
      <td className="py-2 pr-4">
        <span className="rounded border border-border px-1.5 py-0.5 text-[10px] text-gray-400">
          {entry.resource}
        </span>
      </td>
      <td className="py-2 pr-4">
        <code className="text-gray-300">{entry.path}</code>
      </td>
      <td className="py-2 pr-4">
        <DriftValue value={entry.desired} />
      </td>
      <td className="py-2 pr-4">
        <DriftValue value={entry.actual} />
      </td>
    </tr>
  );
}

export default async function ProjectIacPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = await params;

  const shell = (body: React.ReactNode) => (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-1 text-2xl font-semibold text-white">{name}</h1>
        <p className="mb-6 text-sm text-gray-500">Infrastructure as Code</p>
        <ProjectSubNav name={name} active="iac" />
        {body}
      </main>
    </>
  );

  if (!hasClusterCredentials()) {
    return shell(
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        not configured: no in-cluster ServiceAccount credentials found. This
        page only returns real data when running as the platform-console
        pod.
      </div>,
    );
  }

  const [manifestResult, driftResult] = await Promise.all([
    exportProjectManifest(name),
    detectDrift(name),
  ]);

  if (!manifestResult.ok) {
    return shell(
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        {manifestResult.error}
      </p>,
    );
  }

  const manifest = manifestResult.data;
  const drift = driftResult.ok ? driftResult.data : null;

  return shell(
    <>
      <p className="mb-8 max-w-2xl text-sm text-gray-400">
        The CloudFormation drift-detection / <code>terraform plan</code>{" "}
        equivalent for this project&apos;s own Project + SingleDatabase
        custom resources. The export below is the REAL live spec read
        straight off the cluster (via the same ServiceAccount every other
        module in this console uses) and re-serialized as valid,
        re-appliable YAML -- not a template guess. The drift report compares
        that live spec against exactly what a fresh &quot;Create
        Project&quot; call would submit for this project name today.
      </p>

      <div className="mb-6 card p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-medium text-white">Exported manifest</h2>
          <ManifestActions
            yamlText={manifest.yaml}
            fileName={`${manifest.projectName}.iac.yaml`}
          />
        </div>
        <p className="mb-3 text-xs text-gray-500">
          Namespace <code>{manifest.namespace}</code> -- generated{" "}
          {new Date(manifest.generatedAt).toLocaleString()}. Re-apply with{" "}
          <code>kubectl apply -f {manifest.projectName}.iac.yaml</code>.
        </p>
        <div className="overflow-x-auto rounded-md border border-border bg-black/40">
          <pre className="max-h-[32rem] overflow-y-auto p-4 text-xs text-gray-300">
            <code>{manifest.yaml}</code>
          </pre>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="mb-3 text-base font-medium text-white">Drift report</h2>

        {!driftResult.ok && (
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
            {driftResult.error}
          </p>
        )}

        {drift && (
          <>
            <p className="mb-3 text-xs text-gray-500">
              Desired baseline: databaseRef{" "}
              <code>{drift.desiredInputs.databaseRefName}</code>, hostname{" "}
              <code>{drift.desiredInputs.hostname}</code>, protocol{" "}
              <code>{drift.desiredInputs.protocol}</code>, dbStorageSize{" "}
              <code>{drift.desiredInputs.dbStorageSize}</code> -- the exact
              defaults <code>POST /api/projects</code> applies for a project
              named <code>{drift.projectName}</code>.
            </p>

            {!drift.hasDrift && (
              <p className="rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
                No drift. The live spec matches what a fresh create call
                would submit today.
              </p>
            )}

            {drift.hasDrift && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-gray-500">
                      <th className="py-2 pr-4 font-medium">Resource</th>
                      <th className="py-2 pr-4 font-medium">Field</th>
                      <th className="py-2 pr-4 font-medium">Desired</th>
                      <th className="py-2 pr-4 font-medium">Actual</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {drift.drift.map((entry) => (
                      <DriftRow key={`${entry.resource}:${entry.path}`} entry={entry} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </>,
  );
}
