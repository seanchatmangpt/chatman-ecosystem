# 23.5 Runtime

**Parent:** [23. From Ontology to Artifact](23-from-ontology-to-artifact.md)

## Claim

`Runtime` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger from ontology to artifact system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.

The semantic layer exists to prevent identical reality from fragmenting into incompatible local names. Public vocabularies are preferred where they already express provenance, units, sensors, organizations, policy, preservation, and events. Custom terms are admitted only for genuinely new stellar-industrial meaning. Generated APIs, documents, schemas, simulations, and dashboards are projections over that graph rather than rival semantic authorities.

ggen is treated as a semantic manufacturing compiler: graph and query select meaning, templates render projections, validators reject malformed output, and receipts bind the generated artifact to the admitted subject. Generation is not evidence of correctness. The value of the generator is reproducibility and class closure—once a construction pattern is admitted, it can be regenerated for new subjects without rediscovering the pattern manually.

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

## Operationalization

The implementation path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. The decisive rule is that the semantic or analytical result produced in this subchapter has **no ambient execution authority**. It may change the candidate set, create a proof obligation, generate a simulation, or manufacture an intent. A consequential action still requires explicit subject identity, authority, preconditions, execution, postcondition verification, and a receipt.

A practical record for this topic should contain:

- exact subject and revision/epoch;
- observed inputs with units and provenance;
- admitted assumptions and explicit UNKNOWNs;
- candidate construction or policy;
- constraints and refusal conditions;
- required authority class: SELECT, CONSTRUCT, or DO;
- verifier and postcondition;
- receipt identity and replay method when consequence occurs;

## Evidence boundary

For `Runtime`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.

## Falsifier

The working claim for `Runtime` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.
