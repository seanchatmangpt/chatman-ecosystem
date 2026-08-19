# Operations and Admission — v26.8.18

> Reviewed subject: `seanchatmangpt/chatman-ecosystem@1ed4972318467c5bfb5d283505893a361536d37a`

## Operating law

Every operation must preserve the sequence:

```text
parse
→ route
→ admit or REFUSED
→ diagnose / repair
→ construct
→ verify
→ authority admission
→ actuate
→ observe consequence
→ receipt
→ replay
→ standing
```

Inspection, configuration, compilation, workflow existence, and HTTP success are not interchangeable with successful execution against the exact admitted subject.

## Composition-root Crown

The local Crown remains the narrowest complete verifier for the Rust composition root:

```bash
./scripts/crown.sh
```

The script requires the repository's declared Rust tooling plus `cargo-deny` and `cargo-machete` and checks formatting, Clippy, locked tests, Rustdoc, dependency/license/source policy, unused dependencies, catalog validity, receipts, projections, architecture, storage differential behavior, and exact-subject Crown standing.

Useful narrower commands:

```bash
cargo run --locked -p ecosystem-cli --bin ecosystem -- catalog validate
cargo run --locked -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo run --locked -p ecosystem-cli --bin ecosystem -- projection check
cargo run --locked -p ecosystem-cli --bin ecosystem -- architecture check
cargo run --locked -p ecosystem-cli --bin ecosystem -- storage verify
cargo run --locked -p ecosystem-cli --bin ecosystem -- crown --verify
```

## v26.8.18 platform evidence

Platform-console uses per-control evidence rather than one blanket readiness label. The canonical evidence bundle is:

`platform-console/evidence/control-evidence-bundle.json`

At the reviewed base it records live-tested controls and points to `platform-console/docs/SCOPE-AND-LIMITATIONS.md` for cross-cutting topology limits. Replaying one control does not automatically replay every other control.

Operational evidence in the 2026-08-18 implementation sequence includes real tests of:

- project provisioning and Kubernetes readiness;
- quota rejection and quota-triggered scale-to-zero/reset;
- RBAC positive/negative paths;
- mTLS and NetworkPolicy reachability;
- OIDC authorization-code/PKCE flow and negative controls;
- vulnerability detection with real Trivy findings;
- CEL admission rejection of non-conforming workloads;
- Redis connectivity/isolation and teardown;
- NATS pub/sub, JetStream persistence, isolation, and teardown;
- topology data consistency across visual projections;
- Jaeger trace ingestion and query;
- Loki log ingestion and query;
- storage edge-cache MISS/HIT/backend-bypass behavior;
- OTel Collector span acceptance and fan-out to the standing-weaver path;
- cold-standby cluster materialization without destroying the primary cluster.

These observations are persisted evidence from the reviewed tree/history. A future head must not inherit them automatically after subject drift.

## Governor model

Governors move through explicit execution states such as:

`Planned → Admitted → Running → Succeeded`

Alternative execution states include `AwaitingInput`, `AwaitingAuthority`, `Failed`, `Ambiguous`, `Refused`, and `Superseded`.

A timeout is ambiguous, not an automatic permission to retry. Duplicate idempotency keys replay the prior outcome rather than silently repeating the effect.

## ggen provisioning

The v26.8.18 service path uses a real configured ggen binary for provisioning. Operationally:

1. resolve tenant/project identity;
2. construct a bounded workspace/request;
3. invoke the ggen pipeline;
4. verify returned receipt material;
5. append an attempt record;
6. return applied or refused/error state.

Current limitations remain material:

- the repo-level ggen rail is `PARTIAL_ALIVE`;
- tenant isolation is process/namespace/workspace scoped, not a separate dedicated compute capsule per tenant;
- receipt/attempt durability is bounded by the deployed storage configuration;
- SaaS purchase/entitlement/billing is not implied by successful provisioning.

## Observability operations

Current local topology:

```text
Istio / workload tracing
      -> OTel Collector
           -> Jaeger
           -> standing weaver live-check

container logs -> Promtail -> Loki
metrics        -> Prometheus
```

When validating this stack, verify both producer and consumer consequences. A healthy Deployment or open TCP connection is insufficient.

For example, a tracing replay should show the request being generated, the Collector accepting spans, and downstream observation in the intended sink. The reviewed implementation fixed real transport/compression/network-policy failures before recording success.

The remaining unattended-traffic limitation must stay explicit until a generator can sustain the observation path without a human-driven request source in the admitted topology.

## Security operations

Security changes require both positive and negative evidence where applicable:

- admission policies: one compliant object admitted and one non-compliant object refused;
- NetworkPolicy: one allowed path and one denied path;
- RBAC: one authorized verb and one unauthorized verb;
- auth: valid session plus mismatch/tamper/revocation cases;
- vulnerability scanning: a real scanner plus a positive-control image with detectable findings;
- storage/signing: verify identity/digest and postcondition, not only command exit.

An evidence bundle with zero `gaps[]` entries does not erase declared system limitations such as single-node topology or absent independent audit.

## Cache and artifact policy

Caches accelerate execution; they do not confer standing.

For the Rust Crown:

- PRs may restore trusted default-branch caches;
- PRs do not write shared caches;
- default-branch runs are shared-cache writers;
- cache keys derive from committed toolchain/lock state;
- cold-cache execution remains a required falsifier against accidental cache dependence.

Exact-SHA workflow artifacts may transfer one candidate, but the receiver must verify source SHA, lockfile/toolchain identity, artifact digest, and required receipts before using the artifact as evidence.

## Generated projections

Do not hand-edit:

- `views/generated/*`;
- generated SOC 2 binder outputs when their ontology/ggen source is the canonical input;
- `status/README.md` or `status/repos/*.md` when `status/snapshot.json` is their generator input.

If a projection is stale, repair/regenerate from the canonical source. Documentation may explicitly mark the projection as stale, but must not overwrite its facts manually.

## SOC 2 boundary

`soc2/` is an evidence/readiness binder. It may support scoping and a later audit engagement. It may not claim `compliant`, `certified`, `attested`, or equivalent audit standing without the required independent auditor process.

## Disaster recovery boundary

The second kind cluster is a real cold-standby target. Operations must describe it as:

`DR materialization / cold standby`

and not as:

`HA`, `active-active`, `multi-region`, `zero-RPO`, or `automatic failover`.

Those stronger claims require different infrastructure and receipts.

## Future v26.9.1 release graph

The next composition crown is verified separately:

```bash
python3 scripts/verify_release.py --check-refs
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_release.py --check-refs --require-alive
```

The strict command is expected to refuse advancement while any required component lacks exact `ALIVE` evidence.

## Publication discipline

A documentation update may describe observed implementation and may open a draft pull request. It does not itself grant authority to:

- merge;
- deploy to production;
- publish a package/release;
- spend;
- communicate externally as an authorized representative;
- declare a compliance result.

Those are separate consequential actions and require their own exact authority and receipts.
