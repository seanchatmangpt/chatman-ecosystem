import Link from "next/link";
import Nav from "@/components/Nav";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

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
        <p className="mb-8 max-w-2xl text-sm text-muted-foreground">
          Each card below links to a project&apos;s live status page, which
          fetches its cluster-internal <code>/status</code> endpoint at
          request time. This page makes no claims about project state
          itself &mdash; only the per-project pages do, and only with what
          the status service actually returns.
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
      </main>
    </>
  );
}
