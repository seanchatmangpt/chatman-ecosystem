# Deterministic Ops Dashboard

A standalone shadcn + deck.gl reference dashboard for a fictional platform ops
console — a service entity graph (nodes + call-flow arcs), a filterable jobs
table, a nodes table, and an incidents panel. It has its own `package.json`
and `node_modules`; it does not depend on `platform-console` or any running
cluster.

## Why this exists

This is intended as future template source material for a `ggen` pack, in
the spirit of the existing `pcq-marketplace-pack` and `cyberpunk-tv-platform`
precedent packs: a real, working, opinionated stack pin (Next.js 15 App
Router + React 19 + TypeScript + Tailwind v4 + a real shadcn CLI run + real
deck.gl layers) that a generator can crib layout, component, and data-shape
patterns from, rather than a throwaway demo.

## The determinism guarantee

Every render of the entity graph — nodes, positions, colors, arcs, labels —
is a pure function of the entity list. There is no `Math.random()` and no
`Date.now()`-seeded layout anywhere in `lib/`. Two entity lists with the same
set of ids always produce byte-identical node positions, even when every
entity's `status`/`metric` field has changed between renders (this is what
lets the dashboard's 5-second poll update colors and radii live without the
graph jittering or re-laying-out on every tick).

This is proven, not asserted: `lib/compute-layout.test.ts` and
`lib/live-update.test.ts` are real `node:test` suites (no mocking — pure
functions over real fixture data) covering:

- identical input (by reference, and by separate-but-structurally-equal
  instances) → identical output
- a different id set → genuinely different output (the memoization key isn't
  vacuously stable)
- re-running an earlier input again reproduces the original output exactly
  (no hidden internal state/counters)
- same id set, different `status`/`metric` per tick → identical layout, but
  different derived color/radius

Run them yourself:

```bash
npm test
# node --test lib/*.test.ts — 17/17 passing
```

## Fixture data

All data is static and checked in — no network calls, no backend:

- `lib/fixtures/entities.json` — 12 services with a real-shaped call graph
  (gateway → auth/storefront → inventory/pricing/search; checkout →
  payments/orders → ledger/notifications; billing → ledger), each with a
  `status` (`healthy | degraded | down`) and a traffic `metric`
- `lib/fetch-entities.ts` — loads and validates that fixture (`parseEntities`
  throws descriptive errors on malformed records; never silently coerces)
- `lib/ops-data.ts` — hand-authored jobs/nodes/incidents data for the
  Overview/Nodes/Incidents tabs

## Stack

- Next.js 15.5.23, React 19.2.0, TypeScript 5 — App Router, fully statically
  prerendered
- Tailwind CSS v4
- shadcn CLI (Base UI under the hood, not Radix) — card, table, badge, tabs,
  dialog, skeleton, alert, separator, button, input, label
- `@deck.gl/core` / `@deck.gl/layers` / `@deck.gl/react` 9.3.10 —
  `OrthographicView` with a real bounding-box fit, `ScatterplotLayer` for
  entities, `ArcLayer` for call-flow edges, `TextLayer` for labels
- Dark theme by default

## Running it

```bash
npm install
npm run dev
```

Then open http://localhost:3000. `npm run build` produces a static
production build; `npm run lint` and `npx tsc --noEmit` are both clean.
