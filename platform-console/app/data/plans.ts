/**
 * Static plan/feature data for the /pricing page. No payment processor, no
 * checkout flow, no card-data collection anywhere in this app -- the
 * "Contact sales" CTA on the Enterprise tier is a plain mailto: link.
 */
export interface Plan {
  id: "free" | "team" | "enterprise";
  name: string;
  price: string;
  priceNote: string;
  description: string;
  features: string[];
  cta: { label: string; href: string };
  highlighted?: boolean;
}

export const plans: Plan[] = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    priceNote: "forever",
    description: "For evaluating the platform on a single project.",
    features: [
      "1 project namespace",
      "Read-only status dashboard",
      "Community support (GitHub issues)",
      "7-day audit log retention",
    ],
    cta: { label: "Get started", href: "/login" },
  },
  {
    id: "team",
    name: "Team",
    price: "$49",
    priceNote: "per seat / month",
    description: "For teams running multiple projects on shared infrastructure.",
    features: [
      "Up to 10 project namespaces",
      "Role-based access control",
      "90-day audit log retention",
      "Email support, next-business-day response",
      "NetworkPolicy default-deny per namespace",
    ],
    cta: { label: "Get started", href: "/login" },
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    priceNote: "annual contract",
    description: "For organizations with dedicated compliance and security requirements.",
    features: [
      "Unlimited project namespaces",
      "Dedicated cluster / VPC isolation",
      "1-year+ audit log retention",
      "Named support engineer, SLA-backed",
      "Evidence bundle export (see /compliance)",
    ],
    cta: { label: "Contact sales", href: "mailto:sales@example.com?subject=Platform%20Console%20Enterprise" },
  },
];
