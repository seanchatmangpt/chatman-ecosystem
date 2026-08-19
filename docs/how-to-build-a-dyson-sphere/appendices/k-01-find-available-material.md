# Appendix K.1 — Find Available Material

**Parent:** [Appendix K — Example SPARQL Queries](k-example-sparql-queries.md)

Matter is the hard budget that prevents a Dyson program from collapsing into pure software metaphor. Each design must close a mass ledger from feedstock through extraction, refining, fabrication, deployment, maintenance, recycling, and unrecoverable loss. Composition uncertainty is therefore an admitted observation problem before it is a manufacturing problem.

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
