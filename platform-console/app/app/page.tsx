import Link from "next/link";
import Nav from "@/components/Nav";

const serviceLayers = [
  {
    href: "/iaas",
    label: "IaaS",
    title: "Infrastructure Control Plane",
    description:
      "Live namespaces, workloads, services, network policy, identity boundaries and Flux reconciliation.",
    evidence: "Kubernetes API + Flux CRDs",
  },
  {
    href: "/paas",
    label: "PaaS",
    title: "Platform Capability Plane",
    description:
      "Managed projects, deployments, services, secrets, database backups, registry, logs and delivery state.",
    evidence: "Project CRDs + namespace-scoped platform primitives",
  },
  {
    href: "/saas",
    label: "SaaS",
    title: "Application Experience Plane",
    description:
      "Tenant/project readiness and application auth, database, storage and functions traced to live runtime evidence.",
    evidence: "Tenant Project → capability → runtime",
  },
];

const projects = [
  {
    slug: "autofde-lab",
    name: "autofde-lab",
    description: "Justfile-driven test harness (test / test-full / test-level4 / test-level4-full).",
  },
  {
    slug: "gymact",
    name: "gymact",
    description: "Python CLI package, installed console script `gymact`.",
  },
  {
    slug: "ggen",
    name: "ggen",
    description: "Rust binary + `ggen sync run` pack pipeline.",
  },
  {
    slug: "ggen-marketplace",
    name: "ggen-marketplace",
    description: "Curated pack library (ontology-modeled packs, incl. soc2-audit-pack).",
  },
];

export default function OverviewPage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-7xl px-6 py-10">
        <section className="mb-10 overflow-hidden rounded-2xl border border-border bg-panel">
          <div className="border-b border-border bg-gradient-to-r from-blue-950/60 via-panel to-panel px-6 py-7">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">Unified cloud surface</div>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">IaaS · PaaS · SaaS as observable projections</h1>
            <p className="mt-3 max-w-4xl text-sm leading-6 text-gray-300">
              The console now exposes the conventional cloud layers without inventing three independent sources of truth. Each dashboard composes the real Kubernetes, operator and Flux control-plane primitives already used by the platform, preserves failed observations as typed uncertainty, and links every aggregate back to its operational surface.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-px bg-border lg:grid-cols-3">
            {serviceLayers.map((layer) => (
              <Link key={layer.href} href={layer.href} className="group bg-panel px-6 py-6 transition hover:bg-blue-950/20">
                <div className="flex items-center justify-between gap-4">
                  <span className="rounded-full border border-blue-900 bg-blue-950/40 px-2.5 py-1 text-[10px] font-semibold tracking-[0.18em] text-blue-300">
                    {layer.label}
                  </span>
                  <span className="text-xs text-gray-600 group-hover:text-blue-300">open →</span>
                </div>
                <h2 className="mt-5 text-lg font-semibold text-white">{layer.title}</h2>
                <p className="mt-2 text-sm leading-6 text-gray-400">{layer.description}</p>
                <div className="mt-5 border-t border-border pt-3 font-mono text-[10px] text-gray-600">{layer.evidence}</div>
              </Link>
            ))}
          </div>
        </section>

        <section>
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-white">Ecosystem project surfaces</h2>
            <p className="mt-2 max-w-3xl text-sm text-gray-400">
              These remain project-specific live status pages. They are intentionally separate from the IaaS/PaaS/SaaS aggregates so a layer view cannot silently overwrite a project&apos;s own standing.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {projects.map((p) => (
              <Link
                key={p.slug}
                href={`/${p.slug}`}
                className="card block p-5 transition hover:border-accent"
              >
                <h3 className="mb-1 text-base font-medium text-white">{p.name}</h3>
                <p className="text-sm text-gray-400">{p.description}</p>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
