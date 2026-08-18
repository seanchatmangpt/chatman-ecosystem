"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Overview" },
  { href: "/autofde-lab", label: "autofde-lab" },
  { href: "/gymact", label: "gymact" },
  { href: "/ggen", label: "ggen" },
  { href: "/ggen-marketplace", label: "ggen-marketplace" },
  { href: "/projects", label: "Projects" },
  { href: "/secrets", label: "Secrets" },
  { href: "/feature-flags", label: "Feature Flags" },
  { href: "/usage", label: "Usage" },
  { href: "/logs", label: "Logs" },
  { href: "/observability", label: "Observability" },
  { href: "/alerts", label: "Alerting" },
  { href: "/gitops", label: "GitOps" },
  { href: "/iam", label: "IAM" },
  { href: "/org", label: "Org Roles" },
  { href: "/audit", label: "Audit Log" },
  { href: "/registry", label: "Registry" },
  { href: "/service-discovery", label: "Service Discovery" },
  { href: "/topology", label: "Topology" },
  { href: "/api-gateway", label: "API Gateway" },
  { href: "/compliance", label: "Compliance" },
  { href: "/pricing", label: "Pricing" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-border bg-panel">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-sm font-semibold tracking-wide text-foreground">
            platform console
          </Link>
          <form action="/api/logout" method="post">
            <button
              type="submit"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              Sign out
            </button>
          </form>
        </div>
        <ul className="flex flex-wrap gap-1 text-sm">
          {links.map((l) => {
            const active = l.href === "/" ? pathname === "/" : pathname?.startsWith(l.href);
            return (
              <li key={l.href}>
                <Link
                  href={l.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    buttonVariants({ variant: active ? "secondary" : "ghost", size: "sm" }),
                    "font-normal",
                    !active && "text-muted-foreground",
                  )}
                >
                  {l.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
