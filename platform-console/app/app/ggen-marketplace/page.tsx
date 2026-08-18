import Nav from "@/components/Nav";
import StatusPanel from "@/components/StatusPanel";
import { fetchGgenMarketplaceStatus } from "@/lib/status";

export const dynamic = "force-dynamic";

export default async function GgenMarketplacePage() {
  const result = await fetchGgenMarketplaceStatus();

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">ggen-marketplace</h1>
        <p className="mb-8 text-sm text-gray-400">
          Live fields fetched server-side from{" "}
          <code>ggen-marketplace-status.ggen-marketplace.svc.cluster.local/status</code>.
        </p>
        <StatusPanel title="Status" result={result} />
      </main>
    </>
  );
}
