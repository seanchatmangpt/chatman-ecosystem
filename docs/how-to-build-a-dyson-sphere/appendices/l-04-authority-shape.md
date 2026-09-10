# Appendix L.4 — Authority Shape

**Parent:** [Appendix L — Example SHACL Shapes](l-example-shacl-shapes.md)

The semantic layer exists to prevent identical reality from fragmenting into incompatible local names. Public vocabularies are preferred where they already express provenance, units, sensors, organizations, policy, preservation, and events. Custom terms are admitted only for genuinely new stellar-industrial meaning. Generated APIs, documents, schemas, simulations, and dashboards are projections over that graph rather than rival semantic authorities.

SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt.

## SHACL pattern

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <https://example.invalid/dyson/> .

ex:ExampleShape a sh:NodeShape ;
  sh:targetClass ex:Example ;
  sh:closed false .
```

The example is intentionally incomplete. Production shapes must bind to the canonical ontology and include the actual constraints required by the subject.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix L.4 — Authority Shape** is not retained as a label-only reference. This page sits on the irreversible boundary between choosing a possibility and changing the world. SELECT, CONSTRUCT, and DO are separate authorities. Search may explore many reversible candidates; construction may manufacture an artifact or counterfactual; only an explicitly admitted grant for the exact subject and consequence class can authorize DO. Access to a connector, credential, model, or command runner is capability—not authority.

## System contract

The brokered sequence is `intent -> exact-subject admission -> authority check -> consequence bound -> receipt reservation -> actuator -> observation -> reconciliation -> final receipt`. Relevant UNKNOWN refuses before DO. Ambiguous actuation does not turn into a retry loop. Replay verifies prior evidence and intentionally lacks an actuator edge. These separations keep autonomous operation from becoming ambient permission.

## Failure modes and falsifiers

Permanent falsifiers include accepting a nearby authority class, allowing a grant for one subject to mutate another, invoking an actuator before reservation is durable, promoting transport ACK to DONE, or letting a planner/model/hook manufacture its own authority. Any such edge is a constitutional defect even if the resulting state happens to be desirable.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
