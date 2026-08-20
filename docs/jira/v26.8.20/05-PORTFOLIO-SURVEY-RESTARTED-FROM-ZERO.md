# v26.8.20 — Portfolio Survey, Restarted From Zero

> **Supersedes nothing by editing it — corrects by addition.** This document exists because the
> user explicitly rejected treating this session's own prior `docs/jira/v26.8.20/00-04*.md` series
> as ground truth for a portfolio-wide survey, and asked for the whole exploration re-run with zero
> framing carried forward, including README.md/CLAUDE.md content in every repo surveyed (self-
> authored docs are a claim to check, not truth — this pass caught one repo's headline benchmark
> claims running ~400x below its own logged numbers, and another repo's "release ready" badge
> contradicted by git state). Five fresh Explore agents surveyed `chatman-ecosystem`, `~/cns`,
> `~/chatmangpt`, `~/dev`, and the `ggen` tooling substrate cold, verifying claims against real
> files, benchmark logs, and git state rather than restating self-descriptions. Full agent reports
> are preserved in `/Users/sac/.claude/plans/sharded-marinating-turing.md`; this document is the
> committed, citable synthesis.

## What's independently, freshly confirmed as real

- **`chatman-ecosystem`**: a real, large Next.js enterprise console
  (`platform-console/app/lib/`: 144 `.ts` files, 52,816 lines; `app/api/`: 245 route
  subdirectories) plus a small, real, curated ontology (`ontology/*.ttl`: 80 declared
  classes/individuals across 4 files, ~810 lines — independently recounted at **44**
  `ce:Capability` individuals in `platform-console-capabilities.ttl`). **The "receipt/actuation-
  boundary enforcement" claim and the root README's "constitutional control plane" framing are
  explicitly downgraded to UNVERIFIED this pass** — the vocabulary exists in filenames
  (`ce-standing.ts`, `authority-object.ts`) and in the `gymact`/`autofde-lab` submodules' own
  `CLAUDE.md` files, but no agent traced any of it into actually-executing enforcement code
  (`AuthorityResolver`, an OCEL writer/verifier) this pass. This is a genuine, disclosed
  verification gap, not a debunked claim — the next real step for this repo is tracing that code,
  not repeating the claim.
- **`~/cns`**: real ontology/CLI-tooling code exists (`ontologies/core_runtime.owl`,
  `unified_cli.owl`, `cli_ontology.ttl` — all model CNS's own CLI/runtime architecture, not an
  external domain, no capability/authority/broker vocabulary found). But nearly every headline
  performance number in the README is either unsupported by any artifact in the repo or **directly
  contradicted by the repo's own dated benchmark JSON logs**:
  - "625M ops/sec (115% of target)" → actual logged run: 1,584,171 msgs/sec against a
    630,000,000 target = **0.25% of target**.
  - "2.9B ops/sec" BitFlow / "1M TPS" pipeline → actual logged TPS: 159,456 against a 1,000,000
    target = **~16%**; the newest "unified benchmark" report shows the relevant benchmark script
    failing outright (`Cannot find module '.../bitflow-benchmark.js'`, `exitCode: 1`).
  - "97.66 BILLION ops/sec" — appears only in README/marketing text, corroborated nowhere in the
    repo. **Likely fabricated**, not merely unsupported.
  - The one confirmed claim (122 tests, 100% pass) tests **mocked** stand-ins per the repo's own
    `HIVE_MIND_VALIDATION_REPORT.md`, which itself states "Performance claims need production
    benchmarks."
- **`~/chatmangpt`**: real, substantial engineering exists in places — OSA's `test/` dir (474
  files; a sampled 791-line `byzantine_coordinator_test.exs` had real scenario logic, not stubs)
  and BusinessOS's Go backend (~90+ real handler files with matching tests, working
  9-service `docker-compose.yml`, 10 real CI workflows). But the portfolio-wide "RELEASE READY,
  4,045 tests passing" README banner is a **stale ~4-5-month-old snapshot presented as current**
  (verified via `git log -1` on the three flagship subprojects: last touched Apr 11–29, 2026 vs.
  today 2026-08-20), and is actively contradicted by real git state: `canopy` is in a **detached
  HEAD with uncommitted deletions** at survey time. `ostar`'s own `CLAUDE.md` self-contradicts its
  ambitious framing in the same file: "Never say 'ETHOS complete'... Only 1/6 tiers verified."
- **`~/dev`**: 191 top-level entries, 38 with `mix.exs`. **Only 3 of 38 are actual git repos**
  (`pnet` — 56 real iterative commits; `ttl_forge` — 3; `hello_world` — 4, trivial) — everything
  else, including `beamops`, `remindly`, `city_edge`, `trialbase`, was never git-initialized.
  Real domain modeling exists in `city_edge` (a genuine `AshDoubleEntry`-based ledger domain with
  real actions) and `trialbase` (17 concrete Ash resource modules, a legal/case-management +
  billing domain) — but **zero `Ash.Policy`/multitenancy code was found anywhere in the entire
  corpus**, confirmed independently twice. **`~/dev/beamops` is confirmed, independently, twice
  this session, to be unmodified BEAMOps book companion code**: not a git repo, no README,
  `mix.exs`'s copyright banner credits the Pragmatic Bookshelf book verbatim, the internal app is
  named `Kanban`, not "beamops." It is reference material to build *alongside*, with zero local
  work on it — not a project with existing user work to continue, correcting this session's
  earlier framing of it as "the substrate to extend."
- **`ggen` tooling** (`ggen-marketplace`, `ggen-create`, `ggen-marketplace-bridged-packs`): **zero
  Elixir/Ash/Phoenix/BEAM pack-generation capability exists anywhere**, confirmed by direct grep
  of all 148 marketplace pack names/`pack.toml` contents and the entire `ggen-create` Python+Rust
  source tree. The only real Erlang/OTP touchpoint anywhere is `azure-terraform-pack`, which
  deploys a *pre-existing* compiled Erlang/OTP escript as a Terraform-provisioned subprocess —
  infrastructure deployment, not Ash/Elixir/Phoenix code generation. One other pack
  (`ma-case-study-pack`) explicitly self-documents its own Erlang/OTP dispatch chain as "PLANNED
  — not built." `ggen-marketplace-bridged-packs` is a confirmed **stale, drifted one-way
  snapshot** of a past marketplace state (version/description mismatches, 12+ packs differ
  between the two sets), not a live mirror.

## The pattern across all five repos, stated plainly

Extensive, real engineering effort coexists with self-authored/self-graded "COMPLETE"/"PRODUCTION
READY"/"VALIDATED" claims that — every time this session actually checked one against a build, a
benchmark log, or a git state — either failed to hold up or were explicitly disclosed as
unverified/incomplete by the repo's own adjacent documents. This is not a new discovery unique to
this pass: `~/chatmangpt/PORTFOLIO_REALITY.md` and `~/chatmangpt/ostar/CLAUDE.md` already say
versions of this about themselves. What this session adds is independent, from-scratch
verification — fresh benchmark-log reads, fresh git-state checks — corroborating the pattern with
new, specific evidence rather than repeating the self-assessment.

## Applying the user's note: public ontologies are available to render from

Whatever gets built next for XaaS/entitlement/tenancy modeling should reuse the public
vocabularies already available (PROV-O, ODRL, GoodRelations, SKOS, DCTERMS, SHACL — the same
reuse-first discipline `chatman-ecosystem/ontology/capabilities.ttl` and
`platform-console/services/gymact/.claude/rules/ontology.md` already state) rather than inventing
a new vocabulary — the one real, verified-working pattern this survey found holding up under
scrutiny.

## The concrete, verified gap

No Elixir/Ash/Phoenix XaaS entitlement/tenancy/capability-modeling work exists anywhere on this
machine today — not in `~/dev`, not in `~/cns`, not in `~/chatmangpt`, and no `ggen` tooling
exists to generate it. Building it means starting a genuinely new Ash/Phoenix project from public
ontologies, informed by (not copied from) `city_edge`'s and `trialbase`'s real resource-modeling
patterns — none of which have policy/tenancy layers to lift, only resource-shape patterns worth
learning from.

## What this document does not do

It does not re-verify `chatman-ecosystem`'s receipt/actuation-boundary claim down to the actual
`AuthorityResolver`/OCEL implementation — that remains a disclosed, open gap, not resolved here.
It does not start the new Ash/Phoenix project the gap above calls for — that is the next real
step, pending confirmation of scope.

## See Also

- `/Users/sac/.claude/plans/sharded-marinating-turing.md` — the full plan-mode transcript with
  every agent's complete returned report, including the initial pass this restart superseded
- [`03-XAAS-ASH-ECOSYSTEM-MAP.md`](03-XAAS-ASH-ECOSYSTEM-MAP.md),
  [`04-XAAS-BEAMOPS-2E-MDBOOK-PLAN.md`](04-XAAS-BEAMOPS-2E-MDBOOK-PLAN.md) — this session's prior
  docs, explicitly not treated as authoritative for this restart; any future reliance on them
  should re-verify their claims the same way this document did, not restate them
