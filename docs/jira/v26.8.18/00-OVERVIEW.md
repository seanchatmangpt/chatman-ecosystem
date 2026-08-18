# ggen as IaaS/PaaS/SaaS — Design Proposal v26.8.18

Index ticket for a four-part design proposal on layering ggen's own manufacturing role
inside chatman-ecosystem, following the same IaaS/PaaS/SaaS taxonomy
`SONY-READINESS-GAP-CLOSURE.md` already applies to `platform-console` as a whole, applied here
specifically to ggen for the first time. The set was prompted by a design conversation about
what ggen would concretely look like at each layer — as raw manufacturing capacity, as a
managed self-service pipeline, and as a tenant-facing capability product — given that ggen is
today only a bare status stub tenant of `platform-console`
(`platform-console/services/ggen/app.py`) and a `PARTIAL_ALIVE`-pinned external repository in
`status/repos/ggen.md`, not a provisioned service. This is a design-proposal ticket set, not a
defect/bug ticket set like `docs/jira/v26.8.16/`: no code changes accompany it. It documents an
architecture direction for future work, grounded in real, already-verified facts about both
repos — including one real, working precedent from this session (the shared
`run_pack_query` implementation reachable from both a CLI verb and an MCP tool), not
speculation.

## Repo root paths (referenced throughout)

| Repo | Root path | Role in this ticket set |
|---|---|---|
| chatman-ecosystem | `/Users/sac/chatman-ecosystem/` | Control-plane repo these tickets live in |
| ggen | `/Users/sac/ggen/` | Manufacturing system being layered |
| ggen-marketplace (content) | `~/ggen-marketplace/` | 147+ packs, PaaS/SaaS buildpack catalog |

## Tickets

1. [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md) — the bottom layer: manufacturing capacity plus
   receipt custody as the real substrate a tenant needs to run `ggen sync run` lawfully,
   with no packs, ontology semantics, or product surface yet in scope.
2. [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md) — the managed, API-driven sync pipeline layer,
   grounded in the real `run_pack_query` CLI+MCP shared-implementation precedent and
   `ggen-mcp`'s Bounded Unattended-Write Dispatcher as the model for BRCE-compliant
   auto-provisioning.
3. [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md) — the tenant-facing capability-catalog layer,
   where the BLAKE3 receipt chain stops being developer plumbing and becomes the product a
   buyer is paying proof of having received.
4. [04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) — argues the three layers are
   not three products but three different actuation-authority boundaries around one
   invariant, `CONSTITUTION.md`'s "Zero unreceipted actuation," and proposes per-layer rail
   registration (`ggen_iaas`/`ggen_paas`/`ggen_saas`) in `catalog/rails.toml` with the
   concrete evidence bar each would need to move from `CANDIDATE` to `ALIVE`.

## Definition of done for the set

- All four proposal tickets ground every claim in a real, cited file path from either repo,
  or explicitly flag an item as illustrative/greenfield rather than implying it exists.
- No ticket proposes bypassing `CONSTITUTION.md`'s zero-unreceipted-actuation invariant; every
  proposed auto-provisioning or auto-deploy path is modeled on the existing Bounded
  Unattended-Write Dispatcher precedent, not a new unreviewed dispatch mechanism.
- Cross-links between all five files in this directory resolve to real filenames.
- No code changes are implied as already done by this ticket set — it is a direction, not a
  landed feature.

## See Also

- `/Users/sac/chatman-ecosystem/CONSTITUTION.md` — the zero-unreceipted-actuation invariant
  every ticket in this set is checked against
- `/Users/sac/chatman-ecosystem/SONY-READINESS-GAP-CLOSURE.md` — the existing IaaS/PaaS/SaaS
  layering this set applies to ggen specifically for the first time
- `/Users/sac/chatman-ecosystem/docs/40-ggen-semantic-manufacturing-system.md` — the formal
  `ggen:(O*,Q,G_r,V_a,P)->(T,R_d)` signature these three layers each expose differently
- `/Users/sac/ggen/docs/jira/v26.8.16/00-OVERVIEW.md` — a defect-ticket set for contrast; this
  set is a design proposal, not a WIP-closure sweep
