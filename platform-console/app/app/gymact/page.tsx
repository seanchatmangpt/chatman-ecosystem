import Nav from "@/components/Nav";
import StatusPanel from "@/components/StatusPanel";
import { fetchGymactStatus } from "@/lib/status";

export const dynamic = "force-dynamic";

export default async function GymactPage() {
  const result = await fetchGymactStatus();

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">gymact</h1>
        <p className="mb-8 text-sm text-gray-400">
          Live fields fetched server-side from{" "}
          <code>gymact-status.gymact.svc.cluster.local/status</code>.
        </p>
        <StatusPanel title="Status" result={result} />
      </main>
    </>
  );
}
