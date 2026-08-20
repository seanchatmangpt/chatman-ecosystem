# Appendix D — O*.toml Reference

`O*.toml` denotes the admitted-subject carrier pattern. A concrete implementation should use the owning repository's actual schema.

```toml
[subject]
id = "service:example"
kind = "service"
repository = "owner/repo"
commit = "0123456789abcdef0123456789abcdef01234567"

[observation]
observed_at = "2026-08-16T00:00:00Z"
sources = ["git", "runtime"]

[semantics]
ontology = "platform:v3"
policy = "release:v9"

[authority]
class = "CONSTRUCT"
allow_do = false

[verification]
required = ["semantic", "unit", "integration"]

[replay]
toolchain = "toolchain:example-v1"
```

## Required properties

The carrier should make subject ambiguity visible, preserve source freshness, name semantic policy, distinguish authority class, and state the evidence expected before standing can advance.

## Anti-patterns

Avoid `branch = "main"` as the only source identity for a crown claim, `environment = "prod"` without an exact target coordinate, or `approved = true` without the authority identity and policy that made the decision.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix D — O*.toml Reference** is not retained as a label-only reference. This page belongs to the observation boundary: it explains how a real subject becomes an admitted, replayable description rather than an unqualified bag of facts. Observation is always partial. The carrier must bind exact subject identity, measurement time, source provenance, units, uncertainty, contradiction state, and the dimensions that remain UNKNOWN. A digest identifies the carrier; it does not make the carrier true.

## System contract

The operational sequence is `raw signal -> normalization -> provenance -> contradiction handling -> O* admission`. A value can be syntactically present yet inadmissible because its source is stale, its units are unresolved, or another source contradicts it. The critical rule is that UNKNOWN is preserved as topology. Missing knowledge may remove candidate actions from the lawful frontier, but it cannot be converted into permission merely because a planner prefers progress.

## Failure modes and falsifiers

Falsifiers are identity drift, stale observations reused against a changed subject, loss of provenance, contradictory measurements collapsed without a rule, and a regenerated observation whose digest cannot be reproduced from the same admitted inputs. Any of these lowers standing. The recovery path is re-observation and re-admission, not manual assertion that the old world model is still close enough.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
