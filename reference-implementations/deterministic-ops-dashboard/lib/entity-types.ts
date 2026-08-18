/**
 * Structural entity model for the deck.gl graph layer.
 *
 * `status` is a real three-state lifecycle, not a fabricated good/bad binary:
 * a service is "healthy" (serving normally), "degraded" (serving, but past an
 * alert threshold — elevated latency/error rate/saturation), or "down" (not
 * serving). This mirrors how an actual service mesh or health-check system
 * reports state, and it's what `lib/palette.ts` and the status badges key off.
 *
 * `edges` model only real, asserted relationships — "service X calls service
 * Y" — never a random pairing. The fixture graph below is a small plausible
 * slice of a checkout path: a gateway fans out to auth and the storefront
 * API, the storefront API calls inventory and pricing, checkout calls
 * payments and orders, and orders writes through to the ledger. `weight` is
 * the call's relative traffic share (0..1), asserted per edge, not derived.
 */

export type EntityStatus = "healthy" | "degraded" | "down";

export interface EntityEdge {
  targetId: string;
  weight: number; // 0..1, relative traffic share of this call relationship
}

export interface Entity {
  id: string;
  label: string;
  status: EntityStatus;
  metric: number; // drives node radius (e.g. requests/sec, in hundreds)
  edges: EntityEdge[];
}

export const SERVICE_ENTITIES: Entity[] = [
  {
    id: "svc-gateway",
    label: "api-gateway",
    status: "healthy",
    metric: 82,
    edges: [
      { targetId: "svc-auth", weight: 0.35 },
      { targetId: "svc-storefront", weight: 0.65 },
    ],
  },
  {
    id: "svc-auth",
    label: "auth-service",
    status: "healthy",
    metric: 41,
    edges: [],
  },
  {
    id: "svc-storefront",
    label: "storefront-api",
    status: "healthy",
    metric: 63,
    edges: [
      { targetId: "svc-inventory", weight: 0.5 },
      { targetId: "svc-pricing", weight: 0.5 },
    ],
  },
  {
    id: "svc-inventory",
    label: "inventory-service",
    status: "degraded",
    metric: 29,
    edges: [],
  },
  {
    id: "svc-pricing",
    label: "pricing-service",
    status: "healthy",
    metric: 33,
    edges: [],
  },
  {
    id: "svc-checkout",
    label: "checkout-service",
    status: "degraded",
    metric: 47,
    edges: [
      { targetId: "svc-payments", weight: 0.7 },
      { targetId: "svc-orders", weight: 0.3 },
    ],
  },
  {
    id: "svc-payments",
    label: "payments-service",
    status: "down",
    metric: 18,
    edges: [],
  },
  {
    id: "svc-orders",
    label: "orders-service",
    status: "healthy",
    metric: 52,
    edges: [{ targetId: "svc-ledger", weight: 1.0 }],
  },
  {
    id: "svc-ledger",
    label: "ledger-service",
    status: "healthy",
    metric: 24,
    edges: [],
  },
];
