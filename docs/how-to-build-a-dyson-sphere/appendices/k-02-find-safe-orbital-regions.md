# Appendix K.2 — Find Safe Orbital Regions

**Parent:** [Appendix K — Example SPARQL Queries](k-example-sparql-queries.md)

Orbital state is not a location label; it is a dynamical state with uncertainty. In the two-body approximation, orbital period satisfies T²=4π²a³/μ, where a is semimajor axis and μ is the standard gravitational parameter. Operational designs must then add perturbations, multi-body effects, solar radiation pressure, station-keeping budgets, conjunction probability, and covariance growth.

## Reference relation

\[T^2 = \frac{4\pi^2 a^3}{\mu}\]

## Query pattern

```sparql
SELECT ?subject ?evidence
WHERE {
  ?subject ?predicate ?evidence .
  FILTER(BOUND(?evidence))
}
```

The concrete ontology IRIs and predicates must come from the admitted graph. This generic pattern is illustrative and must not be mistaken for a canonical query against an unspecified schema.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.
