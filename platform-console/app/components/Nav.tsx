import Link from "next/link";

const links = [
  { href: "/", label: "Overview" },
  { href: "/autofde-lab", label: "autofde-lab" },
  { href: "/gymact", label: "gymact" },
  { href: "/ggen", label: "ggen" },
  { href: "/ggen-marketplace", label: "ggen-marketplace" },
  { href: "/projects", label: "Projects" },
  { href: "/secrets", label: "Secrets" },
  { href: "/backups", label: "Backups" },
  { href: "/logs", label: "Logs" },
  { href: "/observability", label: "Observability" },
  { href: "/gitops", label: "GitOps" },
  { href: "/iam", label: "IAM" },
  { href: "/registry", label: "Registry" },
  { href: "/api-gateway", label: "API Gateway" },
  { href: "/compliance", label: "Compliance" },
  { href: "/pricing", label: "Pricing" },
];

export default function Nav() {
  return (
    <nav className="border-b border-border bg-panel">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-sm font-semibold tracking-wide text-white">
          platform console
        </Link>
        <ul className="flex flex-wrap gap-5 text-sm text-gray-300">
          {links.map((l) => (
            <li key={l.href}>
              <Link href={l.href} className="hover:text-white">
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
        <form action="/api/logout" method="post">
          <button
            type="submit"
            className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-300 hover:text-white"
          >
            Sign out
          </button>
        </form>
      </div>
    </nav>
  );
}
