import Nav from "@/components/Nav";
import StatusPanel from "@/components/StatusPanel";
import { fetchAutofdeLabStatus } from "@/lib/status";

export const dynamic = "force-dynamic";

export default async function AutofdeLabPage() {
  const result = await fetchAutofdeLabStatus();

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">autofde-lab</h1>
        <p className="mb-8 text-sm text-gray-400">
          Live fields fetched server-side from{" "}
          <code>autofde-lab-status.autofde-lab.svc.cluster.local/status</code>.
        </p>
        <StatusPanel title="Status" result={result} />
      </main>
    </>
  );
}
