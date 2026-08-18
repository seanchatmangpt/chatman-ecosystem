import Nav from "@/components/Nav";
import StatusPanel from "@/components/StatusPanel";
import { fetchGgenStatus } from "@/lib/status";

export const dynamic = "force-dynamic";

export default async function GgenPage() {
  const result = await fetchGgenStatus();

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">ggen</h1>
        <p className="mb-8 text-sm text-gray-400">
          Live fields fetched server-side from{" "}
          <code>ggen-status.ggen.svc.cluster.local/status</code>. Note the
          installed binary version and the workspace Cargo version are
          reported separately below &mdash; they are two different real
          facts about two different artifacts, not merged into one.
        </p>
        <StatusPanel title="Status" result={result} />
      </main>
    </>
  );
}
