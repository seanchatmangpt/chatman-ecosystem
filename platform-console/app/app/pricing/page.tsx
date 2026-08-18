import Nav from "@/components/Nav";
import { plans } from "@/data/plans";

export default function PricingPage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Pricing</h1>
        <p className="mb-10 max-w-2xl text-sm text-gray-400">
          Static plan information. There is no checkout flow on this page
          &mdash; the Enterprise tier&apos;s &ldquo;Contact sales&rdquo;
          button opens your mail client via a plain <code>mailto:</code>{" "}
          link.
        </p>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`card flex flex-col p-6 ${
                plan.highlighted ? "border-accent" : ""
              }`}
            >
              <h2 className="text-lg font-semibold text-white">{plan.name}</h2>
              <p className="mt-1 text-sm text-gray-400">{plan.description}</p>
              <div className="mt-4">
                <span className="text-3xl font-bold text-white">{plan.price}</span>
                <span className="ml-1 text-sm text-gray-400">{plan.priceNote}</span>
              </div>
              <ul className="mt-6 flex-1 space-y-2 text-sm text-gray-300">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <a
                href={plan.cta.href}
                className="mt-6 block rounded-md bg-accent px-4 py-2 text-center text-sm font-medium text-white hover:opacity-90"
              >
                {plan.cta.label}
              </a>
            </div>
          ))}
        </div>
      </main>
    </>
  );
}
