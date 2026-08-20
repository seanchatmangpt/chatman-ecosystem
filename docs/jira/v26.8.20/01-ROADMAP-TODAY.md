# v26.8.20 — Today's Roadmap (2026-08-20)

> Real state, not a backward-chain premise. Scope is what's actually in flight in this working
> tree as of session start, plus concrete next steps for the IaaS/PaaS/SaaS layers this session
> is deepening in `platform-console`.

## 1. In-flight work (this session, uncommitted at session start)

Recovered from a crashed prior session. Real diff, not projected:

| Area | Change | State |
|---|---|---|
| Submodule conversion | `services/autofde-lab`, `services/gymact` moved to `deployment/`, re-added as git submodules (`.gitmodules` staged) | Staged, needs build verification before commit |
| Compliance API routes | `app/api/ocel/`, `app/api/owner/geofence-policy/`, `app/api/owner/legal-hold/`, `app/api/owner/vendor-offboarding/` | Untracked, new |
| Compliance libs | `lib/geofence-enforcement.ts`, `lib/legal-hold.ts`, `lib/vendor-offboarding-attestation.ts` | Untracked, new |
| Modified libs | `approval-workflow.ts`, `audit-db.ts`, `audit-log.ts`, `dsar.ts`, `ocel-log.ts`, `retention.ts` | Extending existing audit/compliance chain |
| Ontology | `ontology/platform-console-capabilities.ttl` | Modified, tracks new capabilities as RDF individuals |

**Build status (checked, not assumed):** `next build` failed twice before this doc was written —
(1) `app/api/v1/audit-export/route.ts` exported `SCHEMA_VERSION` as a route field, which Next 15
route-type-checking rejects (fixed: un-exported, now module-private); (2) multiple `app/**/page.tsx`
files call `useSearchParams()` without a `Suspense` boundary, which fails static export
(`/api-gateway` via `Nav`'s `FreezeBanner`/`OrgBrandMark`, then 7 `app/org/*` pages plus `signup`/
`login`/`invite` which were already correctly wrapped). Fix in progress: wrap each in the existing
codebase's `Inner` + `<Suspense>` pattern. Build re-run pending; commit gated on green build.

## 2. Layer map for what's actually being built

This session's compliance surface (`legal-hold`, `vendor-offboarding`, `geofence-policy`,
`retention`, `dsar`, `ocel-log`, `audit-db`) sits at the **SaaS layer**: tenant-facing controls
enforced against a shared control plane, logged through one hash-chained audit rail
(`audit-db.ts`) and one OCEL event log (`ocel-log.ts`). It is not IaaS or PaaS work — no new
infra provisioning primitive or deploy/runtime abstraction is being added today.

| Layer | Real components today | Not today |
|---|---|---|
| IaaS | Istio API-gateway rate limiting (`app/api-gateway`), k8s fault-diagnosis capability (real, diagnose-only, bridged to autofde-lab) | No Crossplane/Terraform provisioning layer exists yet — noted as a future option, not started |
| PaaS | Service catalog capability (Backstage-shaped, already listed as a capability), ggen PaaS endpoint | No Knative/Operator-pattern runtime — not started |
| SaaS | `legal-hold`, `vendor-offboarding`, `geofence-policy`, `retention`, `dsar`, OCEL audit chain, Stripe billing, entitlement adapters (stubbed for AWS/Azure/GCP) | Real per-cloud entitlement fulfillment — stubs only (`throw new Error`), tracked in `v26.8.19` |

## 3. Today's concrete steps

1. **Finish the Suspense-boundary fix** for the 7 `app/org/*` pages, re-run `next build` to a
   clean pass, address any newly-surfaced type errors from the new API routes/libs.
2. **Commit** the recovered work as one or more scoped commits once the build is green — submodule
   conversion separately from the new compliance routes/libs, per the existing commit-per-capability
   pattern seen in the recent log (`df1c660`, `9355418`, `d6521de`).
3. **Verify the submodule conversion is intentional and functional**: confirm
   `platform-console/services/autofde-lab` and `services/gymact` resolve as real git submodules
   (not empty gitlinks) — `git submodule status` — before committing `.gitmodules`.
4. **Wire the new untracked routes into `platform-console-capabilities.ttl`** if they aren't
   already reflected (ontology diff currently shows +39 lines; confirm it covers `ocel`,
   `geofence-policy`, `legal-hold`, `vendor-offboarding` as capability individuals, not just a
   subset).
5. **No new IaaS/PaaS provisioning work is scheduled today** — Crossplane, Backstage-proper,
   Knative, and OSB remain candidate future directions (see below), not committed roadmap items,
   pending an explicit decision to pick one up.

## 4. Candidate future directions (not started, not committed)

Raised this session as options, recorded here for continuity rather than acted on:

- **IaaS**: Crossplane (K8s-native declarative provisioning via CRDs) or Terraform/OpenTofu +
  Cluster API for multi-cloud VM/cluster lifecycle; Open Service Broker API if IaaS resources
  need a uniform provisioning/binding contract for higher layers.
- **PaaS**: Backstage as the concrete implementation for the existing "service catalog"
  capability; Knative for scale-to-zero deploy semantics; the Operator pattern for
  per-managed-service operational logic.
- **SaaS**: explicit tenant-isolation model decision (pool vs. silo vs. pool+row-level-scoping)
  now that `legal-hold`/`geofence-policy`/`retention`/`dsar` assume some enforceable boundary;
  SCIM for tenant user provisioning tied to `vendor-offboarding`; Strangler Fig if/when the
  25+ capability modules need to be carved out of any remaining monolithic code paths.
- **Cross-cutting**: Well-Architected-style pillar checklist (reliability/security/cost/ops)
  applied across the three layers; continued capability-as-RDF-individual modeling in
  `platform-console-capabilities.ttl` as the queryable source of truth over ad hoc docs.

None of these has an owning ticket yet. Picking one up starts with a decision, not a build.

## See Also

- [`docs/jira/v26.8.19/00-OVERVIEW.md`](../v26.8.19/00-OVERVIEW.md) — marketplace/entitlement
  backward-chain plan this session's SaaS layer extends
- [`docs/jira/v26.8.20/00-BECOMING-A-LICENSED-PROCESSOR.md`](00-BECOMING-A-LICENSED-PROCESSOR.md) —
  the other v26.8.20 ticket, payments-licensing backward-chain
- [`docs/jira/v26.8.20/02-ERLANG-RUST-LANGUAGE-SPLIT.md`](02-ERLANG-RUST-LANGUAGE-SPLIT.md) —
  candidate pure Erlang/OTP 27-28 (PaaS+SaaS) vs. Rust (IaaS) language split, not started
- `ontology/platform-console-capabilities.ttl` — capability individuals, queryable source of truth
