import Nav from "@/components/Nav";
import { evidenceBundle } from "@/data/evidence-bundle";

export default function CompliancePage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-4 text-2xl font-semibold text-white">
          Evidence Bundle
        </h1>

        <div className="mb-8 rounded-md border border-amber-800 bg-amber-950/40 p-4 text-sm text-amber-200">
          This page shows evidence of specific technical controls being
          enforced. It is not a SOC 2 report and does not constitute
          compliance certification, which can only be issued by a licensed
          CPA firm after an independent audit.
        </div>

        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Each entry below states one specific, checkable technical fact and
          where it can be verified &mdash; never a compliance verdict. No
          field on this page is named &ldquo;compliant&rdquo; or
          &ldquo;soc2_ready&rdquo;, by design.
        </p>

        <div className="space-y-4">
          {evidenceBundle.map((entry) => (
            <div key={entry.id} className="card p-5">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <h2 className="text-base font-medium text-white">
                  {entry.control}
                </h2>
                <span className="rounded-full border border-border px-2 py-0.5 text-xs text-gray-400">
                  {entry.evidence_type === "source_control_definition"
                    ? "evidence_gathered: source"
                    : "evidence_gathered: runtime_observation"}
                </span>
              </div>
              <p className="mb-3 text-sm text-gray-300">{entry.description}</p>
              <dl className="grid grid-cols-1 gap-1 text-xs text-gray-500 sm:grid-cols-2">
                <div>
                  <dt className="inline text-gray-600">source_reference: </dt>
                  <dd className="inline break-all">{entry.source_reference}</dd>
                </div>
                <div>
                  <dt className="inline text-gray-600">last_verified_at: </dt>
                  <dd className="inline">{entry.last_verified_at}</dd>
                </div>
              </dl>
              {entry.notes && (
                <p className="mt-3 border-t border-border pt-3 text-xs italic text-gray-500">
                  {entry.notes}
                </p>
              )}
            </div>
          ))}
        </div>
      </main>
    </>
  );
}
