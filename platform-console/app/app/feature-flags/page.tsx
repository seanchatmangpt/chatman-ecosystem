import Nav from "@/components/Nav";
import FeatureFlagsPanel from "@/components/FeatureFlagsPanel";
import { getConfigMap, hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Matches services/autofde-lab/app.py's FEATURE_FLAGS_NAMESPACE/
// FEATURE_FLAGS_CONFIGMAP defaults exactly -- one real ConfigMap, one
// name, read by both this page and the live-toggle proof service.
const FLAGS_NAMESPACE = "platform-console";
const FLAGS_CONFIGMAP = "platform-feature-flags";

export default async function FeatureFlagsPage() {
  const clusterConfigured = hasClusterCredentials();
  const result = clusterConfigured ? await getConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP) : null;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Feature Flags</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real hyperscaler-PaaS-style Feature Flags (AWS AppConfig / LaunchDarkly / GCP Feature
          Flags equivalent), backed by one real k8s <code>ConfigMap</code> (
          <code>platform-feature-flags</code>, <code>platform-console</code> namespace) -- no
          external SaaS dependency. Toggling <code>verbose-status</code> below changes the real,
          live <code>/status</code> response of <code>autofde-lab-status</code> (see the{" "}
          <a className="underline hover:text-white" href="/autofde-lab">
            autofde-lab
          </a>{" "}
          page): that service reads this exact ConfigMap live via the Kubernetes API on every
          request, never a cached or simulated value.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && result && !result.ok && (
          <p className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
            {result.error}
          </p>
        )}

        {clusterConfigured && result?.ok && <FeatureFlagsPanel flags={result.data?.data ?? {}} />}
      </main>
    </>
  );
}
