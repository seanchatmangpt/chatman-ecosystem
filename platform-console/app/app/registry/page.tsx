import Nav from "@/components/Nav";
import {
  hasClusterCredentials,
  listContainerImageStatuses,
  listDeployments,
  type ContainerImageStatus,
  type K8sDeployment,
} from "@/lib/k8s";

export const dynamic = "force-dynamic";

// The platform's own namespaces only -- the 4 project namespaces,
// supabase-demo, and platform-console's own namespace -- the same list
// app/logs/page.tsx uses, since the image-presence cross-check reuses that
// module's `pods` get/list RBAC grant rather than requesting a new one.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

const IMAGE_PULL_WAITING_REASONS = new Set([
  "ImagePullBackOff",
  "ErrImagePull",
  "InvalidImageName",
]);

// containerd canonicalizes any image reference with no registry host to
// Docker Hub's canonical form -- a Deployment spec written as
// `platform-console/console:latest` comes back on the real Pod's
// `containerStatuses[].image` as `docker.io/platform-console/console:latest`
// (confirmed live via `kubectl get pods -o json` on this cluster: every
// containerStatus, including `supabase/*` and `postgrest/*` images,
// carries the same real `docker.io/` prefix). Comparing the two fields
// verbatim made every row on this page compare as "unconfirmed" -- a false
// drift signal on images that are genuinely Ready. Normalize by stripping
// exactly that real, observed prefix before comparing; this is not a
// fabricated allowance, it is undoing a real, documented canonicalization
// containerd itself performs.
function normalizeImageRef(image: string): string {
  return image.replace(/^(docker\.io|index\.docker\.io)\//, "");
}

interface RegistryRow {
  namespace: string;
  deployment: string;
  container: string;
  image: string;
  replicasReady: number;
  replicasDesired: number;
  /** true when a real Ready Pod container reporting this exact image (with
   * a real imageID digest) was found -- confirms it is actually present. */
  confirmedPresent: boolean;
  /** Real digest (`imageID`) from the confirming container status, if any. */
  digest: string | null;
  /** Real image-pull-failure reason from a Pod's containerStatuses, if any
   * Pod using this image is stuck Waiting on one. */
  pullFailureReason: string | null;
  pullFailureMessage: string | null;
}

function buildRows(
  namespace: string,
  deployments: K8sDeployment[],
  imageStatuses: ContainerImageStatus[],
): RegistryRow[] {
  const rows: RegistryRow[] = [];
  for (const dep of deployments) {
    for (const c of dep.containers) {
      const matches = imageStatuses.filter(
        (s) => normalizeImageRef(s.image) === normalizeImageRef(c.image),
      );
      const confirmed = matches.find((s) => s.ready && s.imageID);
      const failing = matches.find(
        (s) => s.waitingReason && IMAGE_PULL_WAITING_REASONS.has(s.waitingReason),
      );
      rows.push({
        namespace,
        deployment: dep.name,
        container: c.name,
        image: c.image,
        replicasReady: dep.replicasReady,
        replicasDesired: dep.replicasDesired,
        confirmedPresent: Boolean(confirmed),
        digest: confirmed?.imageID ?? null,
        pullFailureReason: failing?.waitingReason ?? null,
        pullFailureMessage: failing?.waitingMessage ?? null,
      });
    }
  }
  return rows;
}

function StatusBadge({ row }: { row: RegistryRow }) {
  if (row.pullFailureReason) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-red-900 bg-red-950/40 px-2 py-0.5 text-xs text-red-300">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
        {row.pullFailureReason}
      </span>
    );
  }
  if (row.confirmedPresent) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 text-xs text-emerald-300">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        present
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 rounded-full border border-amber-900 bg-amber-950/40 px-2 py-0.5 text-xs text-amber-300">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
      unconfirmed
    </span>
  );
}

export default async function RegistryPage() {
  const clusterConfigured = hasClusterCredentials();

  const perNamespace = await Promise.all(
    PLATFORM_NAMESPACES.map(async (namespace) => {
      const [deploymentsResult, imageStatusesResult] = await Promise.all([
        listDeployments(namespace),
        listContainerImageStatuses(namespace),
      ]);
      return { namespace, deploymentsResult, imageStatusesResult };
    }),
  );

  const rows: RegistryRow[] = [];
  const errors: Array<{ namespace: string; error: string }> = [];
  for (const { namespace, deploymentsResult, imageStatusesResult } of perNamespace) {
    if (!deploymentsResult.ok) {
      errors.push({ namespace: `${namespace} (deployments)`, error: deploymentsResult.error });
      continue;
    }
    const imageStatuses = imageStatusesResult.ok ? imageStatusesResult.data : [];
    if (!imageStatusesResult.ok) {
      errors.push({ namespace: `${namespace} (pods)`, error: imageStatusesResult.error });
    }
    rows.push(...buildRows(namespace, deploymentsResult.data, imageStatuses));
  }

  const driftCount = rows.filter((r) => r.pullFailureReason || !r.confirmedPresent).length;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Container Registry</h1>
        <p className="mb-4 max-w-3xl text-sm text-gray-400">
          This cluster has no push-capable registry (no ECR/GCR/ACR
          equivalent) -- every image here was built locally and{" "}
          <code>kind load docker-image</code>d directly into the kind node&apos;s
          containerd. So instead of a registry catalog, this is an honest{" "}
          <strong>image inventory</strong>: every real <code>Deployment</code>{" "}
          container&apos;s <code>image</code> field, cross-referenced against
          real Pod <code>containerStatuses</code> (the console pod has no
          containerd socket, so it cannot run <code>crictl images</code>{" "}
          itself). A row is <span className="text-emerald-300">present</span>{" "}
          when a Ready Pod actually reports that image plus a real digest;{" "}
          <span className="text-red-300">flagged red</span> when a Pod is
          stuck on a real image-pull failure (<code>ImagePullBackOff</code> /
          <code>ErrImagePull</code> / <code>InvalidImageName</code>) --
          otherwise <span className="text-amber-300">unconfirmed</span> (no
          Pod evidence either way yet).
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
            This page only returns real data when running as the
            platform-console pod.
          </div>
        )}

        {errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {errors.map((e) => (
              <p
                key={e.namespace}
                className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300"
              >
                {e.namespace}: {e.error}
              </p>
            ))}
          </div>
        )}

        {clusterConfigured && rows.length > 0 && (
          <p className="mb-4 text-xs text-gray-500">
            {rows.length} container(s) across {PLATFORM_NAMESPACES.length} namespaces --{" "}
            {driftCount === 0 ? (
              <span className="text-emerald-400">0 drift signals</span>
            ) : (
              <span className="text-amber-400">{driftCount} not confirmed present</span>
            )}
            .
          </p>
        )}

        <div className="card overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wide text-gray-500">
                <th className="px-4 py-3 font-medium">Namespace</th>
                <th className="px-4 py-3 font-medium">Deployment</th>
                <th className="px-4 py-3 font-medium">Container</th>
                <th className="px-4 py-3 font-medium">Image</th>
                <th className="px-4 py-3 font-medium">Replicas</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-sm text-gray-400">
                    {clusterConfigured ? "No Deployments found." : "—"}
                  </td>
                </tr>
              )}
              {rows.map((row) => (
                <tr
                  key={`${row.namespace}/${row.deployment}/${row.container}`}
                  className="border-b border-border/50 last:border-b-0"
                >
                  <td className="px-4 py-3 text-gray-300">
                    <code>{row.namespace}</code>
                  </td>
                  <td className="px-4 py-3 text-gray-100">{row.deployment}</td>
                  <td className="px-4 py-3 text-gray-300">{row.container}</td>
                  <td className="px-4 py-3">
                    <code className="text-xs text-gray-100">{row.image}</code>
                    {row.digest && (
                      <p className="mt-1 text-[11px] text-gray-500">{row.digest}</p>
                    )}
                    {row.pullFailureMessage && (
                      <p className="mt-1 text-[11px] text-red-400">{row.pullFailureMessage}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {row.replicasReady}/{row.replicasDesired}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge row={row} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
