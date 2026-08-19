# Appendix K.3 — Find Unreceipted Actions

**Parent:** [Appendix K — Example SPARQL Queries](k-example-sparql-queries.md)

Standing belongs to an exact subject. Inspection is not execution, execution is not verification, and a named receipt file is not evidence that the intended transition occurred. A useful receipt binds identity, authority, consequence, verifier result, and replay instructions so a later observer can reconstruct why the standing claim was made.

## Minimal record

```text
subject = <exact identity>
observed = <bounded inputs>
admitted = <constraints and uncertainty>
authority = <SELECT|CONSTRUCT|DO>
executed = <observed action or NONE>
verified = <postcondition evidence>
receipt = <content identity>
replay = <deterministic reconstruction method>
standing = <bounded status>
```

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
