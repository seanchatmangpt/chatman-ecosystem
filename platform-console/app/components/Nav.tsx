"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import NotificationBell from "@/components/NotificationBell";

const links = [
  { href: "/", label: "Overview" },
  { href: "/quickstart", label: "Quickstart" },
  { href: "/autofde-lab", label: "autofde-lab" },
  { href: "/gymact", label: "gymact" },
  { href: "/ggen", label: "ggen" },
  { href: "/ggen-marketplace", label: "ggen-marketplace" },
  { href: "/projects", label: "Projects" },
  { href: "/secrets", label: "Secrets" },
  { href: "/scheduled-jobs", label: "Scheduled Jobs" },
  { href: "/batch-jobs", label: "Batch Compute" },
  { href: "/deployments/canary", label: "Canary Deploy" },
  { href: "/load-test", label: "Load Testing" },
  { href: "/feature-flags", label: "Feature Flags" },
  { href: "/usage", label: "Usage" },
  { href: "/billing", label: "Billing" },
  { href: "/budget-alerts", label: "Budget Alerts" },
  { href: "/logs", label: "Logs" },
  { href: "/exec", label: "Container Exec" },
  { href: "/observability", label: "Observability" },
  { href: "/alerts", label: "Alerting" },
  { href: "/gitops", label: "GitOps" },
  { href: "/iam", label: "IAM" },
  { href: "/org", label: "Org Roles" },
  { href: "/api-keys", label: "API Keys" },
  { href: "/webhooks", label: "Webhooks" },
  { href: "/audit", label: "Audit Log" },
  { href: "/sessions", label: "Sessions" },
  { href: "/registry", label: "Registry" },
  { href: "/service-discovery", label: "Service Discovery" },
  { href: "/tags", label: "Tags" },
  { href: "/custom-domains", label: "Custom Domains" },
  { href: "/topology", label: "Topology" },
  { href: "/network", label: "Network" },
  { href: "/api-gateway", label: "API Gateway" },
  { href: "/disaster-recovery", label: "Disaster Recovery" },
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
          <div className="flex items-center gap-2">
            <NotificationBell />
            <form action="/api/logout" method="post">
              <button
                type="submit"
                className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
              >
                Sign out
              </button>
            </form>
          </div>
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
