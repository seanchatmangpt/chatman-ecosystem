import Link from "next/link";
import Nav from "@/components/Nav";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const serviceLayers = [
  {
    href: "/iaas",
    label: "IaaS",
    title: "Infrastructure Control Plane",
    description: "Live namespaces, workloads, services, network policy, identity boundaries and Flux reconciliation.",
  },
  {
    href: "/paas",
    label: "PaaS",
    title: "Platform Capability Plane",
    description: "Managed projects, deployments, services, secrets, database backups, registry, logs and delivery state.",
  },
  {
    href: "/saas",
    label: "SaaS",
    title: "Application Experience Plane",
    description: "Tenant and project readiness traced through platform capabilities to live runtime evidence.",
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
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Platform Overview</h1>
        <p className="mb-8 max-w-3xl text-sm text-muted-foreground">
          The conventional cloud layers are projections over the same live Kubernetes, operator and Flux control-plane evidence. Failed observations remain typed uncertainty rather than being promoted to standing.
        </p>

        <section className="mb-10">
          <h2 className="mb-4 text-lg font-semibold text-foreground">Cloud layers</h2>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {serviceLayers.map((layer) => (
              <Link key={layer.href} href={layer.href} className="block">
                <Card className="h-full transition hover:border-accent">
                  <CardHeader>
                    <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{layer.label}</div>
                    <CardTitle className="text-base font-medium">{layer.title}</CardTitle>
                    <CardDescription>{layer.description}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-2 text-lg font-semibold text-foreground">Ecosystem project surfaces</h2>
          <p className="mb-5 max-w-3xl text-sm text-muted-foreground">
            Project-specific status pages remain separate from the aggregate layer views, so an IaaS/PaaS/SaaS projection cannot overwrite a project&apos;s own standing.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {projects.map((p) => (
              <Link key={p.slug} href={`/${p.slug}`} className="block">
                <Card className="h-full transition hover:border-accent">
                  <CardHeader>
                    <CardTitle className="text-base font-medium">{p.name}</CardTitle>
                    <CardDescription>{p.description}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
