# Appendix K.5 — Find Resource Bottlenecks

**Parent:** [Appendix K — Example SPARQL Queries](k-example-sparql-queries.md)

The subject is treated as a bounded object in the larger stellar-manufacturing graph. Its inputs, outputs, constraints, failure modes, and evidence obligations must be explicit before the system may generalize from a local success to a reusable class.

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
